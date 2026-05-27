import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
from datetime import datetime
import logging
import sys
import lxml

logging.basicConfig(level = logging.INFO,
                    format = '%(asctime)s - %(levelname)s - %(message)s',
                    handlers = [
                        logging.FileHandler('job_scraper.log'),
                        logging.StreamHandler()
                    ])
log = logging.getLogger(__name__)


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
}

BASE_URL = 'https://www.python.org/jobs/'

def fetch_job_listings(keyword):
    try:
        log.info(f'Fetching job listings for {keyword}...')
        response = requests.get(BASE_URL, headers= HEADERS, timeout = 10)
        response.raise_for_status()
    
    except requests.exceptions.RequestException as e:
        log.error(f'Error fetching job listings: {e}')

    soup = bs(response.text, 'lxml')

    job_list = soup.find('ol', class_='list-recent-jobs')

    if not job_list:
        log.warning(f'No job listings found for {keyword}.')
        sys.exit(1)
    
    cards = job_list.find_all('li')
    log.info(f'Found {len(cards)} job listings for {keyword}.')

    all_jobs = []
    for card in cards:
        job = extract_job(card)
        if job:
            all_jobs.append(job)
        # At the end of fetch_job_listings(), before return
    if keyword:
        all_jobs = [job for job in all_jobs 
                    if keyword.lower() in job['title'].lower() 
                    or keyword.lower() in job['company'].lower()]
        log.info(f'After filtering: {len(all_jobs)} jobs match "{keyword}"')
    return all_jobs

def extract_job(card):
    try:
        company_span = card.find('span', class_='listing-company-name')

        # Title is the <a> tag inside listing-company-name
        title   = company_span.find('a').text.strip()
        job_url = 'https://www.python.org' + company_span.find('a')['href']

        # Company name is plain text after <br/> tag
        # Get all text, remove the badge and title, keep what's left
        br_tag  = company_span.find('br')
        company = br_tag.next_sibling.strip() if br_tag else 'Not specified'

        # Location
        location_tag = card.find('span', class_='listing-location')
        location = ' '.join(location_tag.text.split()) if location_tag else 'Not specified'

        return {
            'title'      : title,
            'company'    : company,
            'link'       : job_url,
            'location'   : location,
            'scraped_at' : datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
        }

    except AttributeError as e:
        log.warning(f'Skipping card — missing field: {e}')
        return None

def save_to_csv(jobs,keyword):
    if not jobs:
        log.warning('No jobs to save.')
        return
    
    file_name = f'{keyword.replace(" ","_")}_listings_{datetime.now().strftime("%d-%m-%y_%H-%m-%S")}.csv'
    df = pd.DataFrame(jobs)
    df.to_csv(file_name, index = False)
    log.info(f'Saved {len(jobs)} jobs to {file_name}')
    print(f'File saved {file_name}')



if __name__ == '__main__':
    keyword = input('Enter Job Title: ').strip()
    jobs = fetch_job_listings(keyword)

    if jobs:
        save_to_csv(jobs,keyword)
        print(f'Total jobs scrapped: {len(jobs)}')
        print('\nSample Listings:')
        for job in jobs[:3]:
            print(f'{job["title"]} at {job["company"]} in {job["location"]}')
    else:
        print(f'No jobs found for {keyword}.')


