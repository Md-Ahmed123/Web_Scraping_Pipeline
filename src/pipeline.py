from pathlib import Path
import logging
import subprocess
import sys
import uuid 
from datetime import datetime
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
load_dotenv()

server = os.getenv("SQL_SERVER")
database = os.getenv("SQL_DATABASE")

if not server or not database:
    raise ValueError("SQL_SERVER and SQL_DATABASE must be configured in .env")

# Create logs folder
project_dir = Path(__file__).resolve().parent.parent
log_dir = project_dir / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

log_file = log_dir / "pipeline.log"

# Configure logging
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

batch_id = str(uuid.uuid4())
start_time = datetime.now()

connection_string = (
    f"mssql+pyodbc://@{server}/{database}"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)

engine = create_engine(connection_string)

with engine.begin() as connection:
    connection.execute(
        text("""
            INSERT INTO PipelineRuns
            (BatchID, PipelineName, StartTime, Status)
            VALUES
            (:batch_id, :pipeline_name, :start_time, :status)
        """),
        {
            "batch_id": batch_id,
            "pipeline_name": "BookScraping",
            "start_time": start_time,
            "status": "Running"
        }
    )
print("Batch ID:", batch_id) 
steps = [
    "scraper.py",
    "transform.py",
    "load.py"
]

logging.info("Pipeline started")

records_extracted = 0
records_inserted = 0
records_updated = 0
try:

    for script in steps:

        logging.info(f"Starting {script}")

        command = [
            sys.executable,
            str(project_dir / "src" / script)
                ]

        if script == "load.py":
            command.append(batch_id)

        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            error_message = result.stderr.strip()

            raise RuntimeError(
                f"{script} failed: {error_message}"
            )
                
        if script == "scraper.py":
            for line in result.stdout.splitlines():
                if line.startswith("RECORDS_EXTRACTED="):
                    records_extracted = int(line.split("=")[1])

        if script == "load.py":
            for line in result.stdout.splitlines():

                if line.startswith("RECORDS_INSERTED="):
                    records_inserted = int(line.split("=")[1])

                if line.startswith("RECORDS_UPDATED="):
                    records_updated = int(line.split("=")[1])

        logging.info(f"{script} completed successfully")

    logging.info("Pipeline completed successfully")
    end_time = datetime.now()

    with engine.begin() as connection:
        connection.execute(
            text("""
            UPDATE PipelineRuns
            SET EndTime = :end_time,
                Status = 'Success',
                RecordsExtracted = :records_extracted,
                RecordsInserted= :records_inserted,
                RecordsUpdated = :records_updated
            WHERE BatchID = :batch_id
            """),
            {
            "end_time": end_time,
            "batch_id": batch_id,
            "records_extracted": records_extracted,
            "records_inserted": records_inserted,
            "records_updated": records_updated


         }
    )

except RuntimeError as e:
    end_time = datetime.now()
    error_message = str(e)

    with engine.begin() as connection:
        connection.execute(
            text("""
                UPDATE PipelineRuns
                SET EndTime = :end_time,
                    Status = 'Failed',
                    ErrorMessage = :error_message,
                    RecordsExtracted = :records_extracted,
                    RecordsInserted = :records_inserted,
                    RecordsUpdated = :records_updated
                WHERE BatchID = :batch_id
            """),
            {
                "end_time": end_time,
                "error_message": error_message,
                "records_extracted": records_extracted,
                
                "records_inserted": records_inserted,
                "records_updated": records_updated,
                "batch_id": batch_id
            }
        )

    logging.error(error_message)
    raise
    

finally:

    logging.info("Pipeline execution finished")