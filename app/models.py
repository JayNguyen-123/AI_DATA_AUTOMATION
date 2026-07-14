import enum
import datetime
from sqlalchemy import Column, String, Datetime, JSON, Enum

class JobStatus(str, enum.Enum):
  PENDING = "PENDING"
  PROCESSING = "PROCESSING"
  COMPLETED = "COMPLETED"
  FAILED = "FAILED"

class AutomationJob(Base):
  __tablename__ = "automation_jobs"

  id = Column(String, primary_key=True, index=True)     # UUID
  status = Column(Enum(JobStatus), default=JobStatus.PENDING, index=True, nullable=False)

  # Raw Extraction Warehousing Columns
  form_data = Column(JSON, nullable=True)
  excel_data = Column(JSON, nullable=True)
  web_data = Column(String, nullable=True)

  # Final AI Analytics Layer Outputs
  summary_output = Column(JSON, nullable=True)
  error_log = Column(String, nullable=True)

  # Performance Monitoring Metrics
  create_at = Column(Datetime, default=datetime.datetime.utcnow, index=True, nullable=False)
  updated_at = Column(Datetime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
