import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

KEYWORDS = [
    "SQL Server DBA",
    "SQL DBA",
    "MSSQL DBA",
    "Azure SQL DBA",
    "Production DBA"
]

# =========================
# SCORING ENGINE
# =========================
def score_job(text):
    text = text.lower()
    score = 0

    if "always on" in text:
        score += 10
    if "azure sql" in text:
        score += 10
    if "sql server 2022" in text:
        score += 10
    if "performance tuning" in text:
        score += 8
    if "ha/dr" in text:
        score += 8
    if "senior" in text or "lead" in text:
        score += 12
    if "production" in text:
        score += 6

    return score


# =========================
# INDEED SCRAPER
# =========================
def fetch_indeed():
    jobs = []
    try:
        url = "https://in.indeed.com/jobs?q=sql+server+dba"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=True):
            title = a.get_text(strip=True)
            link = a["href"]

            if title and ("dba" in title.lower() or "sql" in title.lower()):
                jobs.append({
                    "title": title,
                    "link": "https://in.indeed.com" + link,
                    "source": "Indeed"
                })

    except Exception as e:
        print("Indeed error:", e)

    return jobs


# =========================
# NAUKRI SCRAPER
# =========================
def fetch_naukri():
    jobs = []
    try:
        url = "https://www.naukri.com/sql-server-dba-jobs"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a"):
            title = a.get_text(strip=True)
            link = a.get("href")

            if title and ("dba" in title.lower() or "sql" in title.lower()):
                jobs.append({
                    "title": title,
                    "link": link,
                    "source": "Naukri"
                })

    except Exception as e:
        print("Naukri error:", e)

    return jobs


# =========================
# LINKEDIN (SAFE VERSION - API ONLY)
# =========================
def fetch_linkedin():
    """
    LinkedIn scraping DOES NOT work reliably.
    Use official API or RapidAPI.

    This function is safe placeholder so pipeline won't break.
    """

    LI_KEY = os.getenv("LINKEDIN_API_KEY")

    if not LI_KEY:
        print("LinkedIn skipped (no API key)")
        return []

    try:
        # Example placeholder API (RapidAPI / LinkedIn partner APIs)
        url = "https://example-linkedin-api/jobs"

        headers = {
            "Authorization": f"Bearer {LI_KEY}"
        }

        r = requests.get(url, headers=headers)
        data = r.json()

        jobs = []

        for j in data.get("jobs", []):
            jobs.append({
                "title": j.get("title"),
                "link": j.get("url"),
                "source": "LinkedIn"
            })

        return jobs

    except Exception as e:
        print("LinkedIn error:", e)
        return []


# =========================
# DEDUPLICATION
# =========================
def dedupe(jobs):
    seen = set()
    out = []

    for j in jobs:
        key = j["title"] + str(j["link"])
        if key not in seen:
            seen.add(key)
            out.append(j)

    return out


# =========================
# MAIN ENGINE
# =========================
def main():
    jobs = []

    print("🚀 Fetching jobs...")

    jobs += fetch_indeed()
    jobs += fetch_naukri()
    jobs += fetch_linkedin()

    jobs = dedupe(jobs)

    scored = []
    for j in jobs:
        j["score"] = score_job(j["title"])
        scored.append(j)

    top = sorted(scored, key=lambda x: x["score"], reverse=True)[:5]

    print("\n🚨 AI SQL DBA JOBS (TOP 5)\n")

    for i, j in enumerate(top, 1):
        print(f"{i}. {j['title']}")
        print(f"Score: {j['score']}")
        print(f"Source: {j['source']}")
        print(f"Apply: {j['link']}\n")

    print("Run time:", datetime.now())

    # Save output
    with open("jobs.json", "w", encoding="utf-8") as f:
        import json
        json.dump(top, f, indent=2)


if __name__ == "__main__":
    main()
