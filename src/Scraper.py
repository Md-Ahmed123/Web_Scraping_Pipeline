import time
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")

if not BASE_URL:
    raise ValueError("BASE_URL is not configured in .env")

# --- HTTP session with retries + timeout ---
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
session.mount("https://", HTTPAdapter(max_retries=retries))
session.headers.update({"User-Agent": "Mozilla/5.0"})

# --- Output path anchored to the script location ---
out_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "books.csv"

book_data = []
url = BASE_URL

try:
    while url:
        print("Scraping:", url)

        try:
            response = session.get(url, timeout=(5, 15))
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Stopping at {url}: {e}")
            break

        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        for book in soup.select("article.product_pod"):
            book_data.append({
                "title": book.h3.a["title"],
                "price": float(book.select_one(".price_color").text.replace("£", "")),
                "availability": book.select_one(".availability").text.strip(),
                "rating": book.select_one(".star-rating")["class"][1],
                "book_url": urljoin(url, book.select_one("h3 a")["href"])

            })

        next_button = soup.select_one("li.next a")
        url = urljoin(url, next_button["href"]) if next_button else None

        time.sleep(0.5)  # be polite to the server

finally:
    # Save whatever was collected, even if something failed
    if book_data:
        df = pd.DataFrame(book_data)
        df.to_csv(out_file, index=False)
        print(f"RECORDS_EXTRACTED={len(df)}")
        print("Data saved to:", out_file)
        print(df.head())
    else:
        print("No data collected.")