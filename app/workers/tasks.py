import os
import logging
from app.workers.celery_app import celery_app
from app.database import SessionLocal
from app.models import AutomationJob, JobStatus

# Import core processors constructed in the previous step
from app.core.ocr_engine import extract_form_fields
from app.core.excel_parser import process_excel_chunks
from app.core.web_scraper import scrape_with_bright_data
from app.core.llm_aggregator import aggregate_realtime

logger = logging.getLogger(__name__)

@celery_app.task(
    name="app.workers.tasks.process_pipeline_worker",
    bind=True,
    max_retries=3,
    default_retry_delay=60  # Wait 60 seconds before retrying network/API hiccups
)
def process_pipeline_worker(self, job_id: str, file_path_s3: str, excel_path: str, target_url: str):
    """
    Orchestrates the entire multi-source data extraction pipeline asynchronously.
    Updates states in PostgreSQL and automatically runs storage cleanups.
    """
    logger.info(f"Initializing distributed worker sequence for Job Tracking ID: {job_id}")
    db = SessionLocal()

    # 1. Update system status to PROCESSING inside PostgreSQL
    job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
    if not job:
        logger.error(f"Job context tracking ID {job_id} missing from database records. Terminating.")
        db.close()
        return False

    job.status = JobStatus.PROCESSING
    db.commit()

    try:
        # Step A: Execute Handwriting OCR layout extraction (AWS Textract)
        logger.info(f"Invoking AWS Textract Form Analysis engine for Job: {job_id}")
        extracted_form = extract_form_fields(file_path_s3)
        job.form_data = extracted_form
        db.commit()

        # Step B: Parse the corresponding Excel sheet cleanly in chunks
        logger.info(f"Invoking Memory-Safe Excel Parser engine for Job: {job_id}")
        extracted_excel = process_excel_chunks(excel_path, chunk_size=200)
        job.excel_data = extracted_excel
        db.commit()

        # Step C: Scrape market/customer intelligence (Playwright + Bright Data)
        logger.info(f"Invoking Headless Web Scraper engine for Job: {job_id}")
        extracted_web = scrape_with_bright_data(target_url)
        job.web_data = extracted_web
        db.commit()

        # Step D: Synthesize structural comparisons via LLM (OpenAI Structured Outputs)
        logger.info(f"Invoking LLM aggregation synthesis schema analyzer for Job: {job_id}")
        final_summary = aggregate_realtime(extracted_form, extracted_excel, extracted_web)

        # Save results and mark job complete
        job.summary_output = final_summary
        job.status = JobStatus.COMPLETED
        logger.info(f"Successfully processed and warehoused data records for Job: {job_id}")

    except Exception as exc:
        db.rollback()
        # Handle auto-retry loops for temporary third-party API or network failures
        if self.request.retries < self.max_retries:
            logger.warning(f"Pipeline intercept anomaly encountered. Retrying task. Error: {str(exc)}")
            raise self.retry(exc=exc)

        # Hard fail if retry thresholds are reached
        job.status = JobStatus.FAILED
        job.error_log = f"Pipeline execution aborted after max retries: {str(exc)}"
        logger.error(f"Critical execution failure for Job {job_id}: {str(exc)}")

    finally:
        # Enforce disk sanitation - clear processed files to keep hard disk free
        for local_path in [file_path_s3, excel_path]:
            if local_path and os.path.exists(local_path):
                try:
                    os.remove(local_path)
                    logger.debug(f"Cleaned up temporary staging file binary path: {local_path}")
                except Exception as clean_err:
                    logger.error(f"Failed to remove staging asset {local_path}: {str(clean_err)}")

        db.commit()
        db.close()
    return True
