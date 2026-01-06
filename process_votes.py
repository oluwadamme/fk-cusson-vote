import csv
import requests
import time
import random
import os
import glob
import logging

# --- Configuration ---
URL = "https://www.cussonsbaby.com.ng/wp-admin/admin-ajax.php"
ENTRY_ID = '282'
NONCE = '4d27efc39a'
STATE_FILE = "progress.txt"
LOG_FILE = "voting.log"
MAX_PER_RUN = 50 

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# User-Agent list for rotation to avoid fingerprints
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
]

def load_processed_emails():
    """Reads the state file to see which emails are already used."""
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, 'r') as f:
        return set(line.strip().lower() for line in f if line.strip())

def load_all_emails():
    """Loads and deduplicates emails from all matching CSV files."""
    emails = set()
    csv_files = glob.glob("MOCK_DATA*.csv")
    logger.info("Scanning data sources for emails...")
    for file_path in csv_files:
        count_in_file = 0
        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    email = row.get('email')
                    if email:
                        emails.add(email.strip().lower())
                        count_in_file += 1
            logger.info(f"Loaded {count_in_file} emails from {file_path}")
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
    return sorted(list(emails))

def send_vote(session, email):
    """Sends a single vote using a shared session."""
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': 'https://www.cussonsbaby.com.ng/',
        'Origin': 'https://www.cussonsbaby.com.ng',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': f'baby_competition_voted={ENTRY_ID}'
    }
    
    payload = {
        'action': 'baby_competition_vote',
        'entry_id': ENTRY_ID,
        'voter_email': email,
        'nonce': NONCE,
    }

    try:
        response = session.post(URL, headers=headers, data=payload, timeout=15)
        if response.status_code == 200:
            if '"success":true' in response.text:
                logger.info(f"SUCCESS: {email}")
                return True
            else:
                logger.warning(f"REJECTED: {email} | Response: {response.text[:100]}")
        else:
            logger.error(f"HTTP ERROR: {email} | Status: {response.status_code}")
    except Exception as e:
        logger.error(f"CONNECTION ERROR: {email} | {e}")
    return False

def main():
    processed = load_processed_emails()
    all_emails = load_all_emails()
    
    to_process = [e for e in all_emails if e not in processed]
    
    logger.info("--- Progress Summary ---")
    logger.info(f"Total Unique Emails: {len(all_emails)}")
    logger.info(f"Already Processed:   {len(processed)}")
    logger.info(f"Remaining:           {len(to_process)}")
    
    if not to_process:
        logger.info("All emails processed. Task complete!")
        return

    random.shuffle(to_process)
    batch = to_process[:MAX_PER_RUN]
    logger.info(f"Starting batch of {len(batch)} emails...")
    
    session = requests.Session()
    
    try:
        for idx, email in enumerate(batch):
            success = send_vote(session, email)
            if success:
                with open(STATE_FILE, 'a') as f:
                    f.write(email + "\n")
            
            if idx < len(batch) - 1:
                wait_time = random.uniform(5, 25)
                logger.info(f"Waiting {wait_time:.1f}s before next request...")
                time.sleep(wait_time)
                
    except KeyboardInterrupt:
        logger.info("Process stopped by user.")
    
    logger.info("Batch complete.")

if __name__ == "__main__":
    main()
