# Web Scraping ETL Pipeline

## Overview

This project is a batch ETL pipeline that extracts book information from **Books to Scrape**, transforms and validates the data, and loads it incrementally into SQL Server.

The pipeline is designed to demonstrate a practical data engineering workflow including:

* Web scraping
* Data transformation and validation
* Incremental data loading
* Insert and update detection
* SQL Server integration
* Batch processing
* Pipeline audit logging
* Error handling
* Data quality checks

## Project Highlights

* Built a batch ETL pipeline that extracts ** book records** from a public website.
* Implemented **retry and timeout handling** for reliable web extraction.
* Added multi-stage **data-quality validation** before database loading.
* Implemented **incremental loading** using the book URL as a stable business key.
* Automatically detects **new records, changed records, and unchanged records**.
* Uses **SQL Server transactions** to maintain consistent database updates.
* Generates a unique **Batch ID** for every pipeline execution.
* Maintains a `PipelineRuns` audit table for monitoring extraction, insertion, update, and failure counts.
* Added application-level **pipeline logging and error handling**.
* Externalized configuration using `.env` and protected local configuration with `.gitignore`.


## Project Architecture

```text
Web_Scraping/
│
├── README.md
│
├── data/
│   ├── raw/
│   │   └── books.csv
│   │
│   └── processed/
│       └── books_clean.csv
│
├── logs/
│   └── pipeline.log
│
├── src/
│   ├── scraper.py
│   ├── transform.py
│   ├── load.py
│   └── pipeline.py
│
└── sql/
```

## ETL Flow

```text
Books to Scrape
       ↓
   scraper.py
       ↓
   Raw CSV
       ↓
  transform.py
       ↓
Processed CSV
       ↓
     load.py
       ↓
   SQL Server
       ↓
  PipelineRuns
       ↓
  Audit / Monitoring
```

## Components

### 1. scraper.py

Extracts book information from Books to Scrape.

The scraper collects:

* Title
* Price
* Availability
* Rating
* Book URL
* Book Key

The scraper also includes:

* HTTP request retries
* Timeout handling
* User-Agent
* HTTP status validation
* Request delay
* Saving collected data even when an error occurs

### 2. transform.py

Reads the raw CSV and prepares the data for loading.

It performs:

* Data cleaning
* Price conversion
* Required-column validation
* Missing-value validation
* Price validation
* Rating validation
* Duplicate validation
* Minimum record-count validation

The cleaned dataset is stored in:

```text
data/processed/books_clean.csv
```

### 3. load.py

Loads the processed data into SQL Server.

The loader performs an incremental load using `BookKey` as the unique business key.

It identifies:

* New records → INSERT
* Existing records with changes → UPDATE
* Existing unchanged records → No database operation

Before loading, it also validates:

* Batch ID
* CSV schema
* Empty dataset
* NULL values
* Negative prices
* Duplicate BookKeys

### 4. pipeline.py

Acts as the orchestration layer.

It:

1. Generates a unique Batch ID.
2. Creates a pipeline-run record.
3. Executes `scraper.py`.
4. Executes `transform.py`.
5. Executes `load.py`.
6. Captures extraction, insertion, and update counts.
7. Updates the pipeline audit record.
8. Records errors when a pipeline step fails.

## Database

The project uses SQL Server with the database:

```text
BookScrapingDB
```

### Books

The `Books` table stores the final book data.

Important columns include:

* `BookID`
* `Title`
* `Price`
* `Availability`
* `Rating`
* `BookKey`
* `BookURL`
* `LoadDate`
* `BatchID`

`BookKey` is based on the book URL and is protected by a unique constraint.

### PipelineRuns

The `PipelineRuns` table provides pipeline-level auditing.

It records:

* Batch ID
* Pipeline name
* Start time
* End time
* Status
* Records extracted
* Records inserted
* Records updated
* Error message

## Incremental Loading

The pipeline does not reload all records every time.

For each run:

```text
New BookKey
    → INSERT

Existing BookKey + changed data
    → UPDATE

Existing BookKey + unchanged data
    → No operation
```

This prevents unnecessary database writes and demonstrates an incremental ETL pattern.

## Running the Pipeline

Activate the virtual environment and run:

```bash
python src\pipeline.py
```

The pipeline generates the Batch ID automatically and passes it through the ETL process.

## Validation

The pipeline has validation at multiple stages.

### Transformation validation

The transformation layer validates the cleaned dataset before it reaches the database.

### Load validation

The loading layer performs an additional safety check before modifying SQL Server.

This provides defense against invalid or unexpected input data.

## Logging

Pipeline execution information is stored in:

```text
logs/pipeline.log
```

The log records events such as:

```text
Starting scraper.py
scraper.py completed successfully
Starting transform.py
transform.py completed successfully
Starting load.py
load.py completed successfully
Pipeline completed successfully
```

Database-level audit information is stored in `PipelineRuns`.

## Example Successful Run

A successful unchanged run can produce:

```text
Records Extracted: 1000
Records Inserted: 0
Records Updated: 0
Status: Success
```

If an existing book changes, the pipeline detects the change and updates only that record.

## Technologies Used

* Python
* Pandas
* Requests
* BeautifulSoup
* SQLAlchemy
* PyODBC
* SQL Server
* SQL Server Management Studio
* PowerShell
* Visual Studio Code

## Key Data Engineering Concepts Demonstrated

This project demonstrates practical concepts including:

* ETL
* Batch processing
* Web scraping
* Data validation
* Data quality checks
* Incremental loading
* Change detection
* Business keys
* Database constraints
* Transaction handling
* Pipeline orchestration
* Error handling
* Audit logging
* SQL Server integration
* Python virtual environments
