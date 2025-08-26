from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class GroupStatus(enum.Enum):
    OPEN = "OPEN"
    ANALYZING = "ANALYZING"
    ANALYZED = "ANALYZED"
    NON_ISSUE = "NON_ISSUE"

class ErrorGroup(Base):
    __tablename__ = 'error_groups'
    id = Column(Integer, primary_key=True)
    fingerprint = Column(String(64), unique=True, index=True, nullable=False)
    grouping_method = Column(String(20))
    representative_signature = Column(Text)
    status = Column(SQLEnum(GroupStatus), default=GroupStatus.OPEN, nullable=False)
    
    tags = Column(JSON)
    occurrence_count = Column(Integer, default=0)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    risk_score = Column(Integer, default=50, nullable=False)
    trend = Column(JSON, default=lambda: [0, 0, 0, 0, 0])

    analysis_report = relationship("AnalysisReport", uselist=False, back_populates="group")

class ErrorLog(Base):
    __tablename__ = 'error_logs'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('error_groups.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSON)

class AnalysisReport(Base):
    __tablename__ = 'analysis_reports'
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('error_groups.id'), unique=True)
    
    summary = Column(Text)
    root_cause = Column(Text)
    solution = Column(JSON)
    impact = Column(Text)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("ErrorGroup", back_populates="analysis_report")

def init_db(engine):
    Base.metadata.create_all(bind=engine)