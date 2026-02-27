# IYTE Website Scraper 🕸️

A Python-based web scraping tool designed to systematically crawl, extract, and manage data from `iyte.edu.tr` domains. 

## 🚀 Overview

This repository houses a modular scraping pipeline that not only fetches raw data from the university's web pages but also utilizes AI to process, structure, and validate the collected information into a database.

## 📂 Repository Structure

* **`scrapermain.py`** The core scraping engine. Handles the navigation, targeting, and extraction of web data from the specified URLs.
* **`backfill_ai.py`** An AI-assisted processing script. It evaluates the scraped data, structures complex text, and backfills any missing or unstructured fields.
* **`rowcheck.py`** A data validation utility. Scans the database rows to ensure integrity, spot missing entries, and prevent duplicates after a scrape.
* **`usedb.py`** Database interaction module. Contains the necessary functions to connect, query, insert, and manage the scraped data within the database.
* **`iyte_full_backup/`** Directory reserved for full database and JSON/CSV backups of the extracted data.

## 🛠️ Setup & Installation

1. Clone the repository:
```bash
git clone https://github.com/AlluvianDev/websitescraper.git
cd websitescraper


Ensure you have the necessary Python dependencies installed in your virtual environment (e.g., requests, BeautifulSoup, playwright, database connectors).

Usage
Run the main scraper to begin data extraction:

python scrapermain.py

Check the integrity of your database rows:

python rowcheck.py


Run the AI backfill pipeline to clean and process unstructured data:

python backfill_ai.py

Feel free to suggest new ideas!
