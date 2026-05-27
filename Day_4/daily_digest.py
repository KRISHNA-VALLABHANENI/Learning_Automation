import os
import sys
import time
import logging
import smtplib
import schedule
import threading
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

password = os.getenv('MAIL_PASSWORD')
sender_email = os.getenv('SENDER_EMAIL')
receiver_email = input("Enter the receivers mail address: ")

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    handlers = {
        logging.FileHandler('digest.log'),
        logging.StreamHandler()
    }
)
log = logging.getLogger(__name__)

KEYWORDS = ['Python', 'Engineer', 'Developer']  # jobs to search
BASE_URL  = 'https://www.python.org/jobs/'
HEADERS   = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def validate_env():
    required = ['SENDER_EMAIL', 'MAIL_PASSWORD']
    missing = [m for m in required if not os.getenv(m)]
    if missing:
        log.error(f'Missing Environment Variables: {missing}.')
        sys.exit(1)

def scrape_jobs(keyword):
    """
    Scrape Python.org jobs and filter by keyword.
    Returns list of job dicts.
    """
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        log.error(f"Scraping failed: {e}")
        return []

    soup     = BeautifulSoup(response.text, 'lxml')
    job_list = soup.find('ol', class_='list-recent-jobs')

    if not job_list:
        log.warning("Job list not found.")
        return []

    jobs = []
    for card in job_list.find_all('li'):
        try:
            company_span = card.find('span', class_='listing-company-name')
            title        = company_span.find('a').text.strip()
            job_url      = 'https://www.python.org' + company_span.find('a')['href']
            br_tag       = company_span.find('br')
            company      = br_tag.next_sibling.strip() if br_tag else 'N/A'
            location_tag = card.find('span', class_='listing-location')
            location     = ' '.join(location_tag.text.split()) if location_tag else 'N/A'

            if keyword.lower() in title.lower():
                jobs.append({
                    'title'   : title,
                    'company' : company,
                    'location': location,
                    'url'     : job_url
                })
        except AttributeError:
            continue

    log.info(f"Found {len(jobs)} jobs for '{keyword}'")
    return jobs

def email_body(all_jobs):
    lines = []
    lines.append(f'Daily Job Digest - {datetime.now().strftime("%d %b %Y")}\n')
    lines.append('=' * 50)

    total = sum(len(v) for v in all_jobs.values())
    lines.append(f"Total jobs found: {total}\n")

    for keyword, jobs in all_jobs.items():
        lines.append(f"\n[ {keyword} — {len(jobs)} listings ]")
        lines.append("-" * 40)

        if not jobs:
            lines.append("  No listings found today.")
            continue

        for job in jobs:
            lines.append(f"  Title    : {job['title']}")
            lines.append(f"  Company  : {job['company']}")
            lines.append(f"  Location : {job['location']}")
            lines.append(f"  Link     : {job['url']}")
            lines.append("")

    lines.append("=" * 50)
    lines.append("Sent by your Python Automation Script")
    return "\n".join(lines)
def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    try:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f'The mail has been sent to {receiver_email}')
        return True

    except smtplib.SMTPAuthenticationError:
        print(f'Authentication failed. Check the password')
        return False
    
    except smtplib.SMTPException as e:
        log.error(f"SMTP error: {e}")
        return False
    
    finally:
        server.quit()


def run_digest():
    """
    Main job function — scrape all keywords, build email, send it.
    This is what gets scheduled.
    """
    log.info("Starting daily digest job...")

    all_jobs = {}
    for keyword in KEYWORDS:
        all_jobs[keyword] = scrape_jobs(keyword)

    body    = email_body(all_jobs)
    subject = f"Job Digest — {datetime.now().strftime('%d %b %Y')}"

    success = send_email(subject, body)

    if success:
        log.info("Digest complete.")
    else:
        log.error("Digest failed — email not sent.")

def run_scheduler():
    """Runs in background thread — keeps checking for pending jobs."""
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    validate_env()

    # Schedule digest every day at 07:30
    schedule.every().day.at("07:30").do(run_digest)

    # For testing — also run immediately on start
    log.info("Running digest immediately for test...")
    run_digest()

    # Start scheduler in background thread
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()

    log.info("Scheduler started. Digest will run daily at 07:30.")
    log.info("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        log.info("Scheduler stopped.")


