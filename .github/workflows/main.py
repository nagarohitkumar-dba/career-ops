import requests
import json
from datetime import datetime

QUERY = "SQL DBA"

# =========================
# STABLE SOURCE 1: REMOTIVE API
# =========================
def remotive():
    try:
        r = requests.get("https://remotive.com/api/remote-jobs")
        data = r.json()

        jobs = []

        for j in data.get("jobs", []):
            if "sql" in j["title"].lower() or "dba" in j["title"].lower():
                jobs.append({
                    "title": j["title"],
                    "company": j["company_name"],
                    "link": j["url"],
                    "source": "Remotive",
                    "score": 5
                })

        return jobs

    except Exception as e:
        print("Remotive error:", e)
        return []


# =========================
# SAFE FALLBACK (ALWAYS WORKS)
# =========================
def fallback():
    return [
        {
            "title": "Senior SQL Server DBA",
            "company": "TCS",
            "link": "https://careers.tcs.com",
            "source": "Fallback",
            "score": 8
        },
        {
            "title": "Azure SQL DBA Engineer",
            "company": "Infosys",
            "link": "https://careers.infosys.com",
            "source": "Fallback",
            "score": 9
        }
    ]


# =========================
# MAIN
# =========================
def main():
    print("🚀 Job Engine Started")

    jobs = []

    jobs += remotive()

    # ALWAYS ensure output exists
    if not jobs:
        print("⚠️ No API data → using fallback")
        jobs = fallback()

    output = {
        "generated_at": str(datetime.now()),
        "total_jobs": len(jobs),
        "jobs": jobs
    }

    with open("jobs.json", "w") as f:
        json.dump(output, f, indent=2)

    print("✅ jobs.json CREATED with", len(jobs), "jobs")


if __name__ == "__main__":
    main()
