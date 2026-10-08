from pathlib import Path
import sys
import uuid
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

server = os.getenv("SQL_SERVER")
database = os.getenv("SQL_DATABASE")

if not server or not database:
    raise ValueError("SQL_SERVER and SQL_DATABASE must be configured in .env")
if len(sys.argv) != 2:
    print("ERROR: Batch ID is required.")
    print("Usage: python src\\load.py <BatchID>")
    sys.exit(1)

batch_id = sys.argv[1]
try:
    uuid.UUID(batch_id)
except ValueError:
    print("ERROR: Invalid Batch ID. Batch ID must be a valid UUID.")
    sys.exit(1)

# SQL Server connection


connection_string = (
    f"mssql+pyodbc://@{server}/{database}"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)

engine = create_engine(connection_string)

# CSV file location
project_dir = Path(__file__).resolve().parent.parent
input_file = project_dir / "data" / "processed" / "books_clean.csv"

# Read cleaned data
df = pd.read_csv(input_file)

required_columns = [
    "title",
    "price",
    "availability",
    "rating",
    "book_url",
    "book_key"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    print(f"ERROR: Missing required columns: {missing_columns}")
    sys.exit(1)

if df.empty:
    print("ERROR: CSV contains no records.")
    sys.exit(1)

if df[required_columns].isnull().any().any():
    print("ERROR: CSV contains NULL values in required columns.")
    sys.exit(1)

if (df["price"] < 0).any():
    print("ERROR: CSV contains negative prices.")
    sys.exit(1)

if df["book_key"].duplicated().any():
    print("ERROR: CSV contains duplicate BookKeys.")
    sys.exit(1)

df = df.rename(columns={
    "book_key": "BookKey",
    "book_url": "BookURL"
})

df["LoadDate"] = pd.Timestamp.now()
df["BatchID"] = batch_id

# Remove previous data
with engine.begin() as connection:
    
    existing_keys = pd.read_sql(
        text("""SELECT
            BookKey,
            Title,
            Price,
            Availability,
            Rating,
            BookURL
        FROM dbo.Books"""),
        connection
    )

    new_records = df[
        ~df["BookKey"].isin(existing_keys["BookKey"])
    ]
    existing_records = existing_keys.set_index("BookKey")

    updated_records = df[
    df["BookKey"].isin(existing_records.index)
    ].copy()

    updated_records = updated_records[
        (updated_records["title"] != updated_records["BookKey"].map(existing_records["Title"])) |
        (updated_records["price"] != updated_records["BookKey"].map(existing_records["Price"])) |
        (updated_records["availability"] != updated_records["BookKey"].map(existing_records["Availability"])) |
        (updated_records["rating"] != updated_records["BookKey"].map(existing_records["Rating"])) |
        (updated_records["BookURL"] != updated_records["BookKey"].map(existing_records["BookURL"]))
]


    if not new_records.empty:
        new_records.to_sql(
            "Books",
            con=connection,
            schema="dbo",
            if_exists="append",
            index=False
        )

   # Update existing records in batch
    if not updated_records.empty:

        update_query = text("""
            UPDATE dbo.Books
            SET Title = :title,
                Price = :price,
                Availability = :availability,
                Rating = :rating,
                BookURL = :book_url,
                LoadDate = :load_date,
                BatchID = :batch_id
            WHERE BookKey = :book_key
        """)

        update_data = (
            updated_records[
                [
                    "title",
                    "price",
                    "availability",
                    "rating",
                    "BookURL",
                    "LoadDate",
                    "BatchID",
                    "BookKey"
                ]
            ]
            .rename(columns={
                "BookURL": "book_url",
                "LoadDate": "load_date",
                "BatchID": "batch_id",
                "BookKey": "book_key"
            })
            .to_dict("records")
        )

        connection.execute(update_query, update_data)

records_inserted = len(new_records)
records_updated = len(updated_records)

print(f"RECORDS_INSERTED={records_inserted}")
print(f"RECORDS_UPDATED={records_updated}")

