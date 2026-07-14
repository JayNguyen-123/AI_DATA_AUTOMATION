import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, Base, get_db
from app.models import AutomationJob, JobStatus
from app.schemas import JobResponse, JobStatusResponse

from app.workers.tasks import process_pipeline_worker

# Auto-initialize structural PostgresSQL schemas instantly on Launch
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Real-time multi-source document ingestion and extraction pipeline engine."
)

# Enable standarn enterprise network accessibility patterns
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

def stage_file_binary(upload_file: UploadFile, file_uuid: str) -> str:
  """Stream large incoming binary buffers directly to isolated storage volumns."""
  clean_name = f"{file_uuid}_{upload_file.filename.replace(' ', '_')}"
  target_path = os.path.join(settings.UPLOAD_DIR, clean_name)

  try:
    with open(target_path, "wb") as disk_buffer:
      shutil.copyfileobj(upload_file.file, disk_buffer)
    return target_path
  except Exception as io_error:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Local files system transaction abort: {str(io_error)}"

    )

@app.post(
    "/api/v1/automation/process",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Automation Core"]
)

async def create_automation_job(
    target_url: HttpUrl = Form(..., description="The target intelligence URL route to scrape"),
    form_document: UploadFile = File(..., description="The handwritten asset image or PDF"),
    excel_ledger: UploadFile = File(..., description="The corresponding transactional ledger spreadsheet"),
    db: Session = Depends(get_db)
):
    """
    Accepts processing files, generates tracking rows in PostgresSQL,
    and sends the tasks to Celery workers for async background execution.
    """
    # Validate file extension frameworks immediately
    if not form_document.filename.lower().endswith(('.pdf', '.png', '.jpeg')):
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="Unsupported form format. Valid target formats are: .pdf, .png, .jpeg"
      )
    if not excel_ledger.filename.lower().endswith(('.xlsx', '.xls')):
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="Unsupported excel format. Valid target formats are: .xlsx, .xls"
      )

    # Initialize a system tracking transaction key
    job_id = str(uuid.uuid4())

    # Save input stream to shared local worker disk volumn
    form_disk_path = stage_file_binary(form_document, job_id)
    excel_disk_path = stage_file_binary(excel_ledger, job_id)

    try:

      # Commit row to database in a PENDING status state
      db_job = AutomationJob(id=job_id, status=JobStatus.PENDING)
      db.add(db_job)
      db.commit()

    except Exception as db_ex:
      # Evaluate files instantly if DB context tracking fails
      if os.path.exists(form_disk_path): os.remove(form_disk_path)
      if os.path.exists(excel_disk_path): os.remove(excel_disk_path)

      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail=f"Data pipeline logging rejection: {str(db_ex)}"
      )

    # Push task processing request to Redis message broker cluster queue
    process_pipeline_worker.delay(
        job_id=job_id,
        file_path_s3=form_disk_path,
        excel_path=excel_disk_path,
        target_url=str(target_url)
    )

    return JobResponse(
        job_id=job_id,
        status="PENDING",
        message="Asynchronous extraction processing sequence initialized successfully."

    )

@app.get(
    "/api/v1/automation/status/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    tags=["Automation Core"]
)

async def get_job_status(job_id: str, db: Session=Depends(get_db)):
  """Polls database state cleany to extract strutured model analytics instantly."""
  job = db.query(AutomationJob).filter(AutomationJob.id==job_id).first()

  if not job:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Requested tracking sequence ID '{job_id}' does not exist."
    )

  return job

