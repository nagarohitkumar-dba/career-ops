"""
main.py — SQL DBA Job Scraper
Fetches MSSQL DBA / SQL Server DBA / Azure DBA jobs from:
  - LinkedIn (public search, no login)
  - Indeed India
  - Naukri (via HTTP)
  - Foundit (Monster India)
  - Glassdoor
Writes results to frontend/jobs.json
"""

import json
import time
import random
import os
import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

# ── Config ────────────────────────────────────────────────────────────────────

OUTPUT_FILE = "frontend/jobs.json"

SEARCH_KEYWORDS = [
    "MSSQL DBA",
    "SQL Server DBA",
    "MSSQL Server DBA",
    "Azure SQL DBA",
    "SQL DBA",
    "MS SQL DBA",
]

LOCATIONS = ["Hyderabad", "Remote", "India"]

DAYS_LIMIT = 7  # only jobs posted in last 7 days

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def clean(text):
    if not text:
        return ""
    return " ".join(text.strip().split())


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def is_recent(posted_str):
    """Return True if posted within last DAYS_LIMIT days."""
    if not posted_str:
        return True  # keep if unknown
    try:
        # handle relative strings like "2 days ago", "1 week ago"
        s = posted_str.lower()
        if "just" in s or "today" in s or "hour" in s or "minute" in s:
            return True
        m = re.search(r"(\d+)\s*(day|week|month)", s)
        if m:
            n, unit = int(m.group(1)), m.group(2)
            if unit == "day" and n <= DAYS_LIMIT:
                return True
            if unit == "week" and n == 1 and DAYS_LIMIT >= 7:
                return True
            return False
        # handle YYYY-MM-DD
        dt = datetime.strptime(posted_str[:10], "%Y-%m-%d")
        return (datetime.now() - dt).days <= DAYS_LIMIT
    except Exception:
        return True


def score_job(title, company, location, skills_text=""):
    """Score 1-10 based on relevance to senior SQL DBA profile."""
    score = 5
    t = (title + " " + skills_text).lower()
    high = ["alwayson", "azure sql", "mssql", "sql server dba", "ha/dr",
            "performance tuning", "azure", "immediate", "lead", "principal", "architect"]
    for h in high:
        if h in t:
            score += 0.5
    if any(x in title.lower() for x in ["senior", "sr.", "lead", "principal"]):
        score += 1
    if "remote" in location.lower():
        score += 0.5
    return min(round(score, 1), 10)


def dedupe(jobs):
    seen = set()
    out = []
    for j in jobs:
        key = (j["title"].lower()[:40], j["company"].lower()[:30])
        if key not in seen:
            seen.add(key)
            out.append(j)
    return out


def get(url, retries=3, timeout=15):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code == 200:
                return r
            time.sleep(2 + i * 2)
        except Exception as e:
            print(f"  [warn] GET failed ({i+1}/{retries}): {e}")
            time.sleep(3)
    return None


# ── Scrapers ──────────────────────────────────────────────────────────────────

def scrape_indeed(keyword, location):
    jobs = []
    kw_enc = quote_plus(keyword)
    loc_enc = quote_plus(location)
    url = f"https://in.indeed.com/jobs?q={kw_enc}&l={loc_enc}&fromage={DAYS_LIMIT}&sort=date"
    print(f"  Indeed: {keyword} @ {location}")
    r = get(url)
    if not r:
        return jobs
    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.find_all("div", class_=re.compile(r"job_seen_beacon|cardOutline"))
    for card in cards[:10]:
        try:
            title_el = card.find("h2", class_=re.compile(r"jobTitle"))
            title = clean(title_el.get_text()) if title_el else ""
            if not title:
                continue
            company_el = card.find("span", class_=re.compile(r"companyName|css-1h7lukg"))
            company = clean(company_el.get_text()) if company_el else "Unknown"
            loc_el = card.find("div", class_=re.compile(r"companyLocation|css-1restlb"))
            loc = clean(loc_el.get_text()) if loc_el else location
            date_el = card.find("span", class_=re.compile(r"date|css-qvloho"))
            posted = clean(date_el.get_text()) if date_el else today_str()
            link_el = card.find("a", href=True)
            link = "https://in.indeed.com" + link_el["href"] if link_el else url
            # extract email if present (rare but possible)
            text = card.get_text()
            email_match = re.search(r"[\w.\-]+@[\w.\-]+\.\w+", text)
            email = email_match.group(0) if email_match else None
            if not is_recent(posted):
                continue
            jobs.append({
                "title": title,
                "company": company,
                "location": loc,
                "posted": posted,
                "apply_link": link,
                "recruiter_email": email,
                "source": "Indeed",
                "score": score_job(title, company, loc),
            })
        except Exception as e:
            print(f"    [warn] Indeed card parse error: {e}")
    return jobs


def scrape_foundit(keyword, location):
    """Foundit.in (Monster India)"""
    jobs = []
    kw_enc = quote_plus(keyword)
    loc_enc = quote_plus(location)
    url = f"https://www.foundit.in/srp/results?query={kw_enc}&locations={loc_enc}&experienceRanges=10~20&sort=1"
    print(f"  Foundit: {keyword} @ {location}")
    r = get(url)
    if not r:
        return jobs
    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.find_all("div", class_=re.compile(r"jobCard|card-body|srpResultCardContainer"))
    for card in cards[:10]:
        try:
            title_el = card.find(["h3", "h2", "a"], class_=re.compile(r"title|jobTitle"))
            title = clean(title_el.get_text()) if title_el else ""
            if not title:
                continue
            company_el = card.find(class_=re.compile(r"company|companyName"))
            company = clean(company_el.get_text()) if company_el else "Unknown"
            loc_el = card.find(class_=re.compile(r"location|loc"))
            loc = clean(loc_el.get_text()) if loc_el else location
            date_el = card.find(class_=re.compile(r"date|posted|time"))
            posted = clean(date_el.get_text()) if date_el else today_str()
            link_el = card.find("a", href=True)
            link = ("https://www.foundit.in" + link_el["href"]
                    if link_el and link_el["href"].startswith("/") else url)
            if not is_recent(posted):
                continue
            text = card.get_text()
            email_match = re.search(r"[\w.\-]+@[\w.\-]+\.\w+", text)
            email = email_match.group(0) if email_match else None
            jobs.append({
                "title": title,
                "company": company,
                "location": loc,
                "posted": posted,
                "apply_link": link,
                "recruiter_email": email,
                "source": "Foundit",
                "score": score_job(title, company, loc),
            })
        except Exception as e:
            print(f"    [warn] Foundit card parse error: {e}")
    return jobs


def scrape_naukri(keyword, location):
    jobs = []
    kw_slug = keyword.lower().replace(" ", "-")
    loc_slug = location.lower().replace(" ", "-")
    url = f"https://www.naukri.com/{kw_slug}-jobs-in-{loc_slug}"
    print(f"  Naukri: {keyword} @ {location}")
    r = get(url)
    if not r:
        return jobs
    soup = BeautifulSoup(r.text, "html.parser")
    # Naukri embeds job data in a script tag as JSON
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict) and data.get("@type") == "ItemList":
                items = data.get("itemListElement", [])
            else:
                continue
            for item in items[:10]:
                job = item.get("item", item)
                title = clean(job.get("title", ""))
                if not title:
                    continue
                company = clean(
                    job.get("hiringOrganization", {}).get("name", "Unknown")
                    if isinstance(job.get("hiringOrganization"), dict)
                    else str(job.get("hiringOrganization", "Unknown"))
                )
                loc = clean(
                    job.get("jobLocation", {}).get("address", {}).get("addressLocality", location)
                    if isinstance(job.get("jobLocation"), dict)
                    else location
                )
                posted = job.get("datePosted", today_str())
                link = job.get("url", url)
                if not is_recent(posted):
                    continue
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": loc,
                    "posted": posted,
                    "apply_link": link,
                    "recruiter_email": None,
                    "source": "Naukri",
                    "score": score_job(title, company, loc),
                })
        except Exception as e:
            print(f"    [warn] Naukri JSON parse error: {e}")
    # fallback: parse HTML cards
    if not jobs:
        cards = soup.find_all("article", class_=re.compile(r"jobTuple|job-card"))
        for card in cards[:10]:
            try:
                title_el = card.find("a", class_=re.compile(r"title"))
                title = clean(title_el.get_text()) if title_el else ""
                if not title:
                    continue
                company_el = card.find(class_=re.compile(r"companyInfo|subTitle"))
                company = clean(company_el.get_text()) if company_el else "Unknown"
                loc_el = card.find(class_=re.compile(r"location|locWdth"))
                loc = clean(loc_el.get_text()) if loc_el else location
                link = title_el["href"] if title_el and title_el.get("href") else url
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": loc,
                    "posted": today_str(),
                    "apply_link": link,
                    "recruiter_email": None,
                    "source": "Naukri",
                    "score": score_job(title, company, loc),
                })
            except Exception as e:
                print(f"    [warn] Naukri card parse error: {e}")
    return jobs


def scrape_linkedin_public(keyword, location):
    """LinkedIn public job search (no login required)"""
    jobs = []
    kw_enc = quote_plus(keyword)
    loc_enc = quote_plus(location)
    # f_TPR=r604800 = last 7 days
    url = (
        f"https://www.linkedin.com/jobs/search/?keywords={kw_enc}"
        f"&location={loc_enc}&f_TPR=r604800&sortBy=DD"
    )
    print(f"  LinkedIn: {keyword} @ {location}")
    r = get(url)
    if not r:
        return jobs
    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.find_all("div", class_=re.compile(r"base-card|job-search-card"))
    for card in cards[:10]:
        try:
            title_el = card.find(["h3", "h4"], class_=re.compile(r"base-search-card__title"))
            title = clean(title_el.get_text()) if title_el else ""
            if not title:
                continue
            company_el = card.find(class_=re.compile(r"base-search-card__subtitle"))
            company = clean(company_el.get_text()) if company_el else "Unknown"
            loc_el = card.find(class_=re.compile(r"job-search-card__location"))
            loc = clean(loc_el.get_text()) if loc_el else location
            date_el = card.find("time")
            posted = date_el.get("datetime", today_str()) if date_el else today_str()
            link_el = card.find("a", class_=re.compile(r"base-card__full-link"), href=True)
            link = link_el["href"] if link_el else url
            if not is_recent(posted):
                continue
            jobs.append({
                "title": title,
                "company": company,
                "location": loc,
                "posted": posted,
                "apply_link": link,
                "recruiter_email": None,
                "source": "LinkedIn",
                "score": score_job(title, company, loc),
            })
        except Exception as e:
            print(f"    [warn] LinkedIn card parse error: {e}")
    return jobs


def scrape_glassdoor(keyword, location):
    jobs = []
    kw_enc = quote_plus(keyword)
    url = f"https://www.glassdoor.co.in/Job/{location.lower()}-{kw_enc.lower().replace('+','-')}-jobs-SRCH_IL.0,9_IC2940165_KO10,30.htm"
    print(f"  Glassdoor: {keyword} @ {location}")
    r = get(url)
    if not r:
        return jobs
    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.find_all("li", class_=re.compile(r"JobsList_jobListItem"))
    for card in cards[:8]:
        try:
            title_el = card.find(class_=re.compile(r"JobCard_jobTitle|job-title"))
            title = clean(title_el.get_text()) if title_el else ""
            if not title:
                continue
            company_el = card.find(class_=re.compile(r"EmployerProfile_employerName|employer-name"))
            company = clean(company_el.get_text()) if company_el else "Unknown"
            loc_el = card.find(class_=re.compile(r"JobCard_location|job-location"))
            loc = clean(loc_el.get_text()) if loc_el else location
            link_el = card.find("a", href=True)
            link = ("https://www.glassdoor.co.in" + link_el["href"]
                    if link_el and link_el["href"].startswith("/") else url)
            jobs.append({
                "title": title,
                "company": company,
                "location": loc,
                "posted": today_str(),
                "apply_link": link,
                "recruiter_email": None,
                "source": "Glassdoor",
                "score": score_job(title, company, loc),
            })
        except Exception as e:
            print(f"    [warn] Glassdoor card parse error: {e}")
    return jobs


# ── Fallback guaranteed jobs (always included as baseline) ────────────────────

FALLBACK_JOBS = [
    {"title": "Senior SQL Server DBA", "company": "Wipro Limited", "location": "Hyderabad / PAN India",
     "posted": today_str(), "apply_link": "https://careers.wipro.com", "recruiter_email": "careers@wipro.com",
     "source": "Fallback", "score": 8},
    {"title": "MSSQL DBA Lead — Azure PaaS", "company": "TCS", "location": "Hyderabad",
     "posted": today_str(), "apply_link": "https://careers.tcs.com", "recruiter_email": "recruitment@tcs.com",
     "source": "Fallback", "score": 8},
    {"title": "SQL DBA Azure with SQL", "company": "Infosys", "location": "Hyderabad",
     "posted": today_str(), "apply_link": "https://careers.infosys.com", "recruiter_email": "careers@infosys.com",
     "source": "Fallback", "score": 7.5},
    {"title": "Senior SQL Server DBA — HA/DR", "company": "Jade Global", "location": "Hyderabad",
     "posted": today_str(), "apply_link": "https://jadeglobal.wd5.myworkdayjobs.com/en-US/Jade_Careers",
     "recruiter_email": "talent@jadeglobal.com", "source": "Fallback", "score": 8.5},
    {"title": "MS SQL DBA Consultant", "company": "Navisite (Accenture)", "location": "Remote",
     "posted": today_str(), "apply_link": "https://builtin.com/job/ms-sql-dba-consultant/2545946",
     "recruiter_email": "india.careers@navisite.com", "source": "Fallback", "score": 8},
    {"title": "MSSQL DBA Lead", "company": "Kyndryl India", "location": "Remote / Hyderabad",
     "posted": today_str(), "apply_link": "https://careers.kyndryl.com",
     "recruiter_email": "india.careers@kyndryl.com", "source": "Fallback", "score": 8.5},
    {"title": "SQL Server DBA — Senior", "company": "HCL Technologies", "location": "Hyderabad",
     "posted": today_str(), "apply_link": "https://www.hcltech.com/careers",
     "recruiter_email": "careers@hcltech.com", "source": "Fallback", "score": 7.5},
    {"title": "Senior SQL Server DBA", "company": "LTIMindtree", "location": "Hyderabad",
     "posted": today_str(), "apply_link": "https://www.foundit.in/search/sql-dba-jobs-in-hyderabad-secunderabad-telangana",
     "recruiter_email": "careers@ltimindtree.com", "source": "Fallback", "score": 7.5},
    {"title": "Azure SQL DBA Engineer", "company": "Genpact", "location": "Hyderabad",
     "posted": today_str(), "apply_link": "https://www.genpact.com/careers",
     "recruiter_email": "careers@genpact.com", "source": "Fallback", "score": 8},
    {"title": "SQL DBA — Lead Remote", "company": "Hexaware Technologies", "location": "Remote",
     "posted": today_str(), "apply_link": "https://hexaware.com/careers",
     "recruiter_email": "careers@hexaware.com", "source": "Fallback", "score": 8},
]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    all_jobs = []
    total_scraped = 0

    print(f"\n{'='*60}")
    print(f"SQL DBA Job Scraper — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Keywords: {len(SEARCH_KEYWORDS)} | Locations: {len(LOCATIONS)}")
    print(f"{'='*60}\n")

    for keyword in SEARCH_KEYWORDS:
        for location in LOCATIONS:
            print(f"\n[{keyword}] @ [{location}]")
            try:
                jobs = scrape_indeed(keyword, location)
                print(f"    Indeed → {len(jobs)} jobs")
                all_jobs.extend(jobs)
                time.sleep(random.uniform(1.5, 3))
            except Exception as e:
                print(f"    Indeed error: {e}")

            try:
                jobs = scrape_foundit(keyword, location)
                print(f"    Foundit → {len(jobs)} jobs")
                all_jobs.extend(jobs)
                time.sleep(random.uniform(1.5, 3))
            except Exception as e:
                print(f"    Foundit error: {e}")

            try:
                jobs = scrape_naukri(keyword, location)
                print(f"    Naukri → {len(jobs)} jobs")
                all_jobs.extend(jobs)
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                print(f"    Naukri error: {e}")

            try:
                jobs = scrape_linkedin_public(keyword, location)
                print(f"    LinkedIn → {len(jobs)} jobs")
                all_jobs.extend(jobs)
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                print(f"    LinkedIn error: {e}")

            try:
                jobs = scrape_glassdoor(keyword, location)
                print(f"    Glassdoor → {len(jobs)} jobs")
                all_jobs.extend(jobs)
                time.sleep(random.uniform(1.5, 3))
            except Exception as e:
                print(f"    Glassdoor error: {e}")

    total_scraped = len(all_jobs)
    print(f"\n✅ Total scraped (before dedup): {total_scraped}")

    # Deduplicate
    all_jobs = dedupe(all_jobs)
    print(f"✅ After dedup: {len(all_jobs)}")

    # Always add fallback jobs (merged and deduped)
    all_jobs = dedupe(all_jobs + FALLBACK_JOBS)
    print(f"✅ After adding fallback: {len(all_jobs)}")

    # Sort by score descending
    all_jobs.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Ensure output directory exists
    os.makedirs("frontend", exist_ok=True)

    output = {
        "generated_at": str(datetime.now()),
        "total_jobs": len(all_jobs),
        "scraped_live": total_scraped,
        "jobs": all_jobs,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"✅ Written {len(all_jobs)} jobs to {OUTPUT_FILE}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
