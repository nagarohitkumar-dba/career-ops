import requests
import json
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup

# =========================
# CONFIG
# =========================
JOB_KEYWORDS = ["MSSQL DBA", "SQL Server DBA", "SQLDBA", "MSSQL Server DBA"]
JOBS_FILE = "frontend/jobs.json"   # ✅ single definition, points to frontend

# =========================
# EMAIL EXTRACTION HELPER
# =========================
def extract_emails(text):
    return re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)

# =========================
# FILTER HELPER (7-day freshness)
# =========================
def filter_recent_jobs(jobs, days=7):
    cutoff = datetime.now().date() - timedelta(days=days)
    fresh = []
    for job in jobs:
        try:
            posted_date = datetime.strptime(job["posted"], "%Y-%m-%d").date()
            if posted_date >= cutoff:
                fresh.append(job)
        except Exception:
            # If posted date not parseable, keep it
            fresh.append(job)
    return fresh

# =========================
# SOURCE 1: LinkedIn Scraper
# =========================
def linkedin_jobs():
    jobs = []
    try:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

        url = "https://www.linkedin.com/jobs/search/?keywords=SQL%20DBA&location=India&f_TPR=r604800"
        driver.get(url)
        time.sleep(5)

        postings = driver.find_elements(By.CLASS_NAME, "base-card")

        for post in postings[:50]:  # limit to 50 for speed
            try:
                title = post.find_element(By.CLASS_NAME, "base-search-card__title").text
                company = post.find_element(By.CLASS_NAME, "base-search-card__subtitle").text
                location = post.find_element(By.CLASS_NAME, "job-search-card__location").text
                link = post.find_element(By.TAG_NAME, "a").get_attribute("href")

                # Visit job detail page to try extracting emails
                driver.get(link)
                time.sleep(2)
                page_text = driver.page_source
                emails = extract_emails(page_text)

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "posted": str(datetime.now().date()),
                    "apply_link": link,
                    "recruiter_email": emails[0] if emails else None,
                    "source": "LinkedIn",
                    "score": 9
                })
            except Exception:
                continue

        driver.quit()
    except Exception as e:
        print("LinkedIn scraping error:", e)
    return jobs

# =========================
# SOURCE 2: Naukri Scraper
# =========================
def naukri_jobs():
    jobs = []
    try:
        url = "https://www.naukri.com/sql-dba-jobs-in-india"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")

        postings = soup.find_all("article", class_="jobTuple")
        for post in postings[:50]:
            title = post.find("a", class_="title").text.strip()
            company = post.find("a", class_="subTitle").text.strip()
            link = post.find("a", class_="title")["href"]
            desc = post.text
            emails = extract_emails(desc)

            jobs.append({
                "title": title,
                "company": company,
                "location": "India",
                "posted": str(datetime.now().date()),
                "apply_link": link,
                "recruiter_email": emails[0] if emails else None,
                "source": "Naukri",
                "score": 8
            })
    except Exception as e:
        print("Naukri scraping error:", e)
    return jobs

# =========================
# SOURCE 3: Indeed Scraper
# =========================
def indeed_jobs():
    jobs = []
    try:
        url = "https://in.indeed.com/jobs?q=SQL+DBA&l=India&fromage=7"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")

        postings = soup.find_all("div", class_="job_seen_beacon")
        for post in postings[:50]:
            title = post.find("h2").text.strip()
            company = post.find("span", class_="companyName").text.strip()
            link = "https://in.indeed.com" + post.find("a")["href"]
            desc = post.text
            emails = extract_emails(desc)

            jobs.append({
                "title": title,
                "company": company,
                "location": "India",
                "posted": str(datetime.now().date()),
                "apply_link": link,
                "recruiter_email": emails[0] if emails else None,
                "source": "Indeed",
                "score": 7
            })
    except Exception as e:
        print("Indeed scraping error:", e)
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
                desc = j.get("description", "")
                emails = extract_emails(desc)
                jobs.append({
                    "title": j["title"],
                    "company": j["company_name"],
                    "location": j.get("candidate_required_location", "Remote"),
                    "posted": j.get("publication_date", str(datetime.now().date())),
                    "apply_link": j["url"],
                    "recruiter_email": emails[0] if emails else None,
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
# MAIN ENGINE
# =========================
def main():
    print("🚀 Job Engine Started")

    jobs = []
    jobs += linkedin_jobs()
    jobs += naukri_jobs()
    jobs += indeed_jobs()
    jobs += remotive()

    if not jobs:
        print("⚠️ No API data → using fallback")
        jobs = fallback()

    # ✅ Apply 7-day filter
    jobs = filter_recent_jobs(jobs, days=7)

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
