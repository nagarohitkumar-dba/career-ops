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
# SOURCE 1: LinkedIn (scraping via API/HTML fetch)
# =========================
def linkedin_jobs():
    jobs = []
    try:
        # Placeholder: Replace with Selenium/Playwright scraping
        jobs.append({
            "title": "SQL Server DBA",
            "company": "Wipro",
            "location": "Hyderabad",
            "posted": str(datetime.now().date()),
            "apply_link": "https://linkedin.com/jobs/view/12345",
            "recruiter_email": None,
            "source": "LinkedIn",
            "score": 9
        })
    except Exception as e:
        print("LinkedIn error:", e)
    return jobs

# =========================
# SOURCE 2: Naukri
# =========================
def naukri_jobs():
    jobs = []
    try:
        # Placeholder: Replace with Naukri scraping logic
        jobs.append({
            "title": "Senior SQL DBA",
            "company": "Cognizant",
            "location": "Hyderabad",
            "posted": str(datetime.now().date()),
            "apply_link": "https://naukri.com/job/45678",
            "recruiter_email": None,
            "source": "Naukri",
            "score": 8
        })
    except Exception as e:
        print("Naukri error:", e)
    return jobs

# =========================
# SOURCE 3: Jooble
# =========================
def jooble_jobs():
    jobs = []
    try:
        # Placeholder: Replace with Jooble scraping logic
        jobs.append({
            "title": "Cloud SQL DBA",
            "company": "TechVedika",
            "location": "Hyderabad (Remote)",
            "posted": str(datetime.now().date()),
            "apply_link": "https://jooble.org/job/78910",
            "recruiter_email": None,
            "source": "Jooble",
            "score": 7
        })
    except Exception as e:
        print("Jooble error:", e)
    return jobs

# =========================
# SOURCE 4: Remotive API
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
# SAFE FALLBACK
# =========================
def fallback():
    return [
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
    jobs += linkedin_jobs()
    jobs += naukri_jobs()
    jobs += jooble_jobs()
    jobs += remotive()

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
