import requests
import json
import re
from datetime import datetime

# =========================
# CONFIG
# =========================
JOB_KEYWORDS = ["MSSQL DBA", "SQL Server DBA", "SQLDBA", "MSSQL Server DBA"]
LOCATIONS = ["Hyderabad", "Remote"]
JOBS_FILE = "jobs.json"

# =========================
# SOURCE 1: Remotive API
# =========================
def remotive():
    try:
        r = requests.get("https://remotive.com/api/remote-jobs")
        data = r.json()

        jobs = []
        for j in data.get("jobs", []):
            if any(k.lower() in j["title"].lower() for k in JOB_KEYWORDS):
                jobs.append({
                    "title": j["title"],
                    "company": j["company_name"],
                    "location": j.get("candidate_required_location", "Remote"),
                    "posted": j.get("publication_date", str(datetime.now().date())),
                    "apply_link": j["url"],
                    "recruiter_email": None,
                    "source": "Remotive",
                    "score": 5
                })
        return jobs

    except Exception as e:
        print("Remotive error:", e)
        return []

# =========================
# SOURCE 2: Custom Fetch (Mock LinkedIn/Hyderabad Remote)
# =========================
def fetch_jobs():
    # Placeholder: Replace with Selenium/Playwright scraping logic
    jobs = [
        {
            "title": "SQL Server DBA",
            "company": "ABC Tech",
            "location": "Hyderabad",
            "posted": str(datetime.now().date()),
            "apply_link": "https://linkedin.com/jobs/view/12345",
            "recruiter_email": "hr@abctech.com",
            "source": "LinkedIn",
            "score": 9
        },
        {
            "title": "MSSQL DBA",
            "company": "XYZ Solutions",
            "location": "Remote",
            "posted": str(datetime.now().date()),
            "apply_link": "https://linkedin.com/jobs/view/67890",
            "recruiter_email": None,
            "source": "LinkedIn",
            "score": 8
        }
    ]
    return jobs

# =========================
# SAFE FALLBACK
# =========================
def fallback():
    return [
        {
            "title": "Senior SQL Server DBA",
            "company": "TCS",
            "location": "Hyderabad",
            "posted": str(datetime.now().date()),
            "apply_link": "https://careers.tcs.com",
            "recruiter_email": None,
            "source": "Fallback",
            "score": 7
        },
        {
            "title": "Azure SQL DBA Engineer",
            "company": "Infosys",
            "location": "Remote",
            "posted": str(datetime.now().date()),
            "apply_link": "https://careers.infosys.com",
            "recruiter_email": None,
            "source": "Fallback",
            "score": 6
        }
    ]

# =========================
# EMAIL EXTRACTION HELPER
# =========================
def extract_emails(text):
    return re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)

# =========================
# MAIN ENGINE
# =========================
def main():
    print("🚀 Job Engine Started")

    jobs = []

    # Try Remotive
    jobs += remotive()

    # Add custom fetch (LinkedIn mock)
    jobs += fetch_jobs()

    # Ensure output exists
    if not jobs:
        print("⚠️ No API data → using fallback")
        jobs = fallback()

    output = {
        "generated_at": str(datetime.now()),
        "total_jobs": len(jobs),
        "jobs": jobs
    }

    with open(JOBS_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"✅ {JOBS_FILE} CREATED with {len(jobs)} jobs")

if __name__ == "__main__":
    main()
