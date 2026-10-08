from pathlib import Path
import pandas as pd

# File paths
project_dir = Path(__file__).resolve().parent.parent

input_file = project_dir / "data" / "raw" / "books.csv"

# Read raw data

df = pd.read_csv(input_file)

# Validate required columns
required_columns = [
    "title",
    "price",
    "availability",
    "rating",
    "book_url"
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

print("Column validation passed.")

# Validate data values

if df["title"].isna().any():
    raise ValueError("Some books have missing titles.")

if df["price"].isna().any():
    raise ValueError("Some books have missing prices.")

if (df["price"] < 0).any():
    raise ValueError("Some books have negative prices.")

valid_ratings = ["One", "Two", "Three", "Four", "Five"]

invalid_ratings = df[~df["rating"].isin(valid_ratings)]

if not invalid_ratings.empty:
    raise ValueError(
        f"Invalid ratings found:\n{invalid_ratings}"
    )

print("Data quality validation passed.")

# Validate record count

minimum_expected_records = 900

if len(df) < minimum_expected_records:
    raise ValueError(
        f"Unexpectedly low record count: {len(df)}"
    )

print(f"Record count validation passed: {len(df)} records.")

print("Raw data:")
print(df.head())

print("\nData types:")
print(df.dtypes)

# Basic cleaning
df["title"] = df["title"].str.strip()
df["availability"] = df["availability"].str.strip()
df["rating"] = df["rating"].str.strip()
df["book_key"] =df["book_url"].str.strip()

# Check duplicate titles
duplicates = df[df.duplicated(subset=["title"], keep=False)]

print("\nDuplicate titles:")
print(duplicates)

print("\nTotal books after cleaning:", len(df))

# Create processed folder
processed_dir = project_dir / "data" / "processed"
processed_dir.mkdir(parents=True, exist_ok=True)

# Save transformed data
output_file = processed_dir / "books_clean.csv"

df.to_csv(output_file, index=False)

print("Cleaned data saved to:", output_file)