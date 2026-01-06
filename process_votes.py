import csv
import requests
import time
import random
import os
import glob
import sys

# Configuration
URL = "https://www.cussonsbaby.com.ng/wp-admin/admin-ajax.php"
ENTRY_ID = '282'
NONCE = '4d27efc39a'
STATE_FILE = "progress.txt"
MAX_PER_RUN = 50  # Number of emails to process per GitHub Action execution

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
        return set(line.strip() for line in f if line.strip())

def load_all_emails():
    """Loads and deduplicates emails from all matching CSV files."""
    emails = set()
    csv_files = glob.glob("MOCK_DATA*.csv")
    print(f"--- Scanning Data Sources ---")
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
            print(f"Found {count_in_file} emails in {file_path}")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    return sorted(list(emails))

def send_vote(session, email):
    """Sends a single vote using a shared session for better performance."""
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
                print(f"[SUCCESS] {email}")
                return True
            else:
                print(f"[REJECTED] {email} | Response: {response.text[:100]}")
        else:
            print(f"[FAILED] {email} | Status: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] {email} | {e}")
    return False

def main():
    processed = load_processed_emails()
    all_emails = load_all_emails()
    
    to_process = [e for e in all_emails if e not in processed]
    
    print(f"\n--- Progress Summary ---")
    print(f"Total Unique Emails: {len(all_emails)}")
    print(f"Already Processed:   {len(processed)}")
    print(f"Remaining:           {len(to_process)}")
    
    if not to_process:
        print("\nAll emails processed. Task complete!")
        return

    # Shuffle to avoid sequential patterns that look like bots
    random.shuffle(to_process)
    
    # Process a chunk
    batch = to_process[:MAX_PER_RUN]
    print(f"Starting batch of {len(batch)} emails...\n")
    
    session = requests.Session() # Reuse connections for optimization
    
    try:
        for idx, email in enumerate(batch):
            success = send_vote(session, email)
            if success:
                # Immediate persistence to avoid losing progress if the script crashes
                with open(STATE_FILE, 'a') as f:
                    f.write(email + "\n")
            
            # Anti-detection: Random long pauses
            if idx < len(batch) - 1:
                wait_time = random.uniform(5, 25)
                print(f"   (Pausing {wait_time:.1f}s...)")
                time.sleep(wait_time)
                
    except KeyboardInterrupt:
        print("\nStopped by user.")
    
    print("\nBatch complete. Next run will continue automatically.")

if __name__ == "__main__":
    main()
