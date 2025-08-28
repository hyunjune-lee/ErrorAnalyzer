from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from concurrent.futures import ThreadPoolExecutor
import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Literal
from datetime import datetime

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from fastapi.responses import HTMLResponse

from app.database.connection import engine, get_db, get_new_db_session
from app.database.models import init_db, ErrorGroup, GroupStatus
from app.services.workflow_service import run_analysis_pipeline, PipelineStatus
from app.services.cache_service import app_cache
from app.config import settings
from sqlalchemy.orm import joinedload

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=4)
scheduler = BackgroundScheduler()

class AnalysisReportSchema(BaseModel):
    summary: Optional[str] = None
    root_cause: Optional[str] = None
    solution: Optional[List[str]] = None
    impact: Optional[str] = None
    class Config: 
        from_attributes = True

class ErrorGroupSchema(BaseModel):
    id: int
    fingerprint: str
    grouping_method: str
    representative_signature: str
    status: str
    occurrence_count: int
    first_seen: datetime
    last_seen: datetime
    analysis_report: Optional[AnalysisReportSchema] = None
    risk_score: int
    trend: List[int]
    sample_log: Optional[dict] = None
    class Config: 
        from_attributes = True

class FetchHistorySchema(BaseModel):
    id: int
    start_time: datetime
    end_time: datetime
    log_count: int

    class Config:
        from_attributes = True

class ToggleNonIssueRequest(BaseModel):
    is_non_issue: bool

class PipelineStatusModel(BaseModel):
    status: Literal["idle", "running"] = "idle"
    stage: Optional[Literal["FETCHING_LOGS", "PROCESSING", "DISPATCHING", "DONE"]] = None
    progress: int = 0
    last_run_summary: str = ""

class SystemStatusModel(BaseModel):
    nelo_configured: bool
    nelo_group_id: str
    log_source_type: str
    pipeline_interval: int

pipeline_status = PipelineStatus()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Error Analyzer PoC...")
    init_db(engine)
    db = get_new_db_session()
    try: 
        app_cache.initialize(db)
    finally: 
        db.close()
    scheduler.add_job(trigger_pipeline, 'interval', seconds=settings.pipeline_interval_seconds, id="analysis_pipeline")
    scheduler.start()
    logger.info(f"Scheduler started. Pipeline runs every {settings.pipeline_interval_seconds} seconds.")
    logger.info(f"Log source: {settings.log_source_type.upper()}")
    if settings.log_source_type.lower() == "nelo":
        logger.info(f"NELO Group ID: {settings.nelo_group_id}")
    yield
    logger.info("Shutting down application...")
    scheduler.shutdown()
    executor.shutdown(wait=True)

app = FastAPI(title="Error Analyzer PoC", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def trigger_pipeline():
    if pipeline_status.status == "running":
        logger.warning("Pipeline is already running. Skipping scheduled trigger.")
        return
    db = get_new_db_session()
    try:
        run_analysis_pipeline(db, executor, pipeline_status)
    except Exception as e:
        logger.exception(f"Error during scheduled pipeline execution: {e}")
        pipeline_status.status = "idle"
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Error Analyzer PoC API is running."}

@app.get("/ui", response_class=HTMLResponse)
async def read_ui():
    ui_path = os.path.join(os.path.dirname(__file__), "ui", "index.html")
    if not os.path.exists(ui_path):
        return HTMLResponse(content="<h1>UI file not found at app/ui/index.html</h1>", status_code=404)
    with open(ui_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/groups", response_model=List[ErrorGroupSchema])
def get_error_groups(db: Session = Depends(get_db)):
    from app.database.models import ErrorLog
    groups = (
        db.query(ErrorGroup)
        .options(joinedload(ErrorGroup.analysis_report))
        .order_by(ErrorGroup.last_seen.desc())
        .all()
    )
    
    # Add sample log data for each group
    for group in groups:
        sample_log = (
            db.query(ErrorLog)
            .filter(ErrorLog.group_id == group.id)
            .order_by(ErrorLog.timestamp.desc())
            .first()
        )
        group.sample_log = sample_log.raw_data if sample_log else None
    
    return groups

@app.get("/api/fetch-history", response_model=List[FetchHistorySchema])
def get_fetch_history(db: Session = Depends(get_db)):
    from app.database.models import FetchHistory
    history = db.query(FetchHistory).order_by(FetchHistory.start_time.desc()).limit(100).all()
    return history

@app.post("/api/groups/{group_id}/toggle-non-issue", response_model=ErrorGroupSchema)
def toggle_non_issue_status(group_id: int, request: ToggleNonIssueRequest, db: Session = Depends(get_db)):
    group = db.query(ErrorGroup).filter(ErrorGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Error group not found")

    if request.is_non_issue:
        group.status = GroupStatus.NON_ISSUE
        app_cache.non_issue_fingerprints.add(group.fingerprint)
    else:
        group.status = GroupStatus.ANALYZED if group.analysis_report else GroupStatus.OPEN
        app_cache.non_issue_fingerprints.discard(group.fingerprint)
    
    db.commit()
    db.refresh(group)
    return group

@app.get("/api/pipeline-status", response_model=PipelineStatusModel)
def get_pipeline_status():
    return PipelineStatusModel(
        status=pipeline_status.status,
        stage=pipeline_status.stage,
        progress=pipeline_status.progress,
        last_run_summary=pipeline_status.last_run_summary
    )

@app.get("/api/system-status", response_model=SystemStatusModel)
def get_system_status():
    return SystemStatusModel(
        nelo_configured=bool(settings.nelo_access_key and settings.nelo_secret_key),
        nelo_group_id=settings.nelo_group_id,
        log_source_type=settings.log_source_type,
        pipeline_interval=settings.pipeline_interval_seconds
    )

@app.post("/trigger-pipeline")
def manual_trigger_pipeline(db: Session = Depends(get_db)):
    if pipeline_status.status == "running":
        return {"message": "Pipeline is already running."}
    run_analysis_pipeline(db, executor, pipeline_status)
    return {"message": "Pipeline execution triggered manually."}