import requests
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0"}

QUERY = "sql server dba"

# =========================
# INDEED
# =========================
def indeed():
    url = f"https://in.indeed.com/jobs?q={QUERY.replace(' ', '+')}"
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    jobs = []

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)

        if "dba" in title.lower() or "sql" in title.lower():
            jobs.append({
                "title": title,
                "link": "https://in.indeed.com" + a["href"],
                "source": "Indeed"
            })

    return jobs


# =========================
# NAUKRI
# =========================
def naukri():
    url = "https://www.naukri.com/sql-server-dba-jobs"
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    jobs = []

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)

        if "dba" in title.lower() or "sql" in title.lower():
            jobs.append({
                "title": title,
                "link": a["href"],
                "source": "Naukri"
            })

    return jobs


# =========================
# CLEAN
# =========================
def clean(jobs):
    seen = set()
    out = []

    for j in jobs:
        key = j["title"] + j["link"]

        if key not in seen:
            seen.add(key)
            out.append(j)

    return out


# =========================
# MAIN
# =========================
def main():
    print("🚀 Running SQL DBA Job Agent")

    jobs = []
    jobs += indeed()
    jobs += naukri()

    jobs = clean(jobs)

    output = {
        "generated_at": str(datetime.now()),
        "total_jobs": len(jobs),
        "jobs": jobs
    }

    with open("jobs.json", "w", encoding="utf-8") as f:
        import json
        json.dump(output, f, indent=2)

    print("✅ jobs.json created with:", len(jobs))


if __name__ == "__main__":
    main()
