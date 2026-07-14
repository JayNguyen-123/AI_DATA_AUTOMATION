from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime

# ---------------------------------------
# 1. API Response Schemas
# ---------------------------------------

class JobResponse(BaseModel):
  job_id: str
  status: str
  message: str

class JobStatusResponse(BaseModel):
  job_id: str
  status: str
  summary_output: Optional[dict] = None
  error_log = Optional[str] = None
  created_at: datetime
  updated_at: datetime

  class Config:
    from_attributes = True

# -----------------------------------------------
# 2. Strict AI Model Output Validation Schemas
# -----------------------------------------------

class CleanSummarySchema(BaseModel):
  account_id: str = Field(description="Unique identity matching across data layers.")
  reconciliation_verified: bool = Field(description="True if form data and excel data match cleanly.")
  critical_descrepancies: List[str] = Field(description="List of misaligments spotted between targets.")
  execute_summary: str = Field(description="A concise narrative summary of data findings.")

