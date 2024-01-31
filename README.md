# Canvas Grades to Google Sheets Automation

## Description
This Python script automates the process of transferring grades and due dates from Canvas LMS to a Google Sheets document. It's designed to streamline the analysis and organization of academic data, making end-of-semester grade evaluations more efficient.

## Features
- Fetches course data from Canvas LMS using the Canvas API.
- Organizes and processes data in Python.
- Automatically updates a Google Sheets document with fetched data.
- Can handle multiple courses and creates separate sheets for each.

## Prerequisites
- Basic understanding of Python.
- Canvas LMS access with API key.
- Google Cloud account with Google Sheets API enabled.
- Python libraries: `requests`, `gspread`, `pandas`, `oauth2client`.

## Setup
1. Clone the repository to your local machine.
2. Install required Python libraries: `pip install requests gspread pandas oauth2client`.
3. Obtain Canvas API access token from your Canvas LMS settings.
4. Set up Google Sheets API and download the credentials file.
5. Update the script with your API tokens, course IDs, and Google Sheets details.

## Usage
Run the script with Python:
```bash
python Canvas_to_Google_Sheets.py

## Automation
To automate the script, use a task scheduler:
- On Windows: Use Task Scheduler.
- On macOS/Linux: Use cron jobs.

## Note
This project is for educational purposes. Please ensure compliance with Canvas LMS and Google Sheets API terms of use.
