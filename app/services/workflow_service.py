import logging
from datetime import datetime
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor

from app.services.ingestion_service import fetch_logs
from app.processing.fingerprinter import generate_hybrid_fingerprint
from app.services.cache_service import app_cache
from app.database.models import ErrorGroup, ErrorLog, GroupStatus
from app.services.analysis_service import analyze_error_with_ai

logger = logging.getLogger(__name__)

class PipelineStatus:
    def __init__(self):
        self.status = "idle"
        self.stage = None
        self.progress = 0
        self.last_run_summary = ""

def run_analysis_pipeline(db: Session, executor: ThreadPoolExecutor, status: PipelineStatus):
    try:
        status.status = "running"
        start_time = datetime.now()

        status.stage = "FETCHING_LOGS"
        status.progress = 20
        logger.info("--- Starting Analysis Pipeline: Fetching Logs ---")
        logs = fetch_logs()
        if not logs:
            logger.info("--- Pipeline Finished. No logs found. ---")
            return

        new_groups_for_analysis = []
        processed_count = 0
        skipped_non_issue_count = 0
        fingerprint_to_new_count = {}

        status.stage = "PROCESSING"
        status.progress = 60
        logger.info("--- Pipeline Stage: Processing & Grouping ---")
        for log_entry in logs:
            try:
                fingerprint, method, signature = generate_hybrid_fingerprint(log_entry)
                fingerprint_to_new_count[fingerprint] = fingerprint_to_new_count.get(fingerprint, 0) + 1

                if app_cache.is_non_issue(fingerprint):
                    skipped_non_issue_count += 1
                    continue

                group = db.query(ErrorGroup).filter(ErrorGroup.fingerprint == fingerprint).first()
                is_new = False

                if not group:
                    is_new = True
                    group = ErrorGroup(
                        fingerprint=fingerprint,
                        grouping_method=method,
                        representative_signature=signature,
                        status=GroupStatus.ANALYZING
                    )
                    db.add(group)
                    db.flush()
                    logger.info(f"New Error Group detected: {group.id} (Method: {method})")
                
                group.occurrence_count += 1
                group.last_seen = datetime.utcnow()

                error_log = ErrorLog(group_id=group.id, raw_data=log_entry)
                db.add(error_log)

                if is_new:
                    new_groups_for_analysis.append((group.id, log_entry))

                processed_count += 1
            
            except Exception as e:
                logger.exception(f"Error processing log entry: {e}")
                db.rollback()

        logger.info("--- Pipeline Stage: Updating Trend Data ---")
        all_groups = db.query(ErrorGroup).all()
        for group in all_groups:
            new_count = fingerprint_to_new_count.get(group.fingerprint, 0)
            new_trend = list(group.trend)
            new_trend.pop(0)
            new_trend.append(new_count)
            group.trend = new_trend

        db.commit()

        status.stage = "DISPATCHING"
        status.progress = 90
        logger.info("--- Pipeline Stage: Dispatching AI Tasks ---")
        for group_id, sample_log in new_groups_for_analysis:
            logger.info(f"Dispatching AI analysis task for Group ID: {group_id}")
            executor.submit(analyze_error_with_ai, group_id, sample_log)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        summary = f"Finished in {duration:.2f}s. Processed: {processed_count}, Skipped: {skipped_non_issue_count}, New: {len(new_groups_for_analysis)}"
        status.last_run_summary = summary
        logger.info(f"--- {summary} ---")

    finally:
        status.status = "idle"
        status.stage = "DONE"
        status.progress = 100