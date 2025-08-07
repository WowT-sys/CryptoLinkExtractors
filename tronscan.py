import requests
import threading
import time
import re
import tldextract
from concurrent.futures import ThreadPoolExecutor

API_KEY = 'TRONSCAN-API-KEY'
API_URL = 'https://apilist.tronscanapi.com/api/tokens/overview'
HEADERS = {'db262768-7656-460a-9aef-7f80a309c48a': API_KEY}
OUTPUT = 'trc_token_url.txt'
RATE_LIMIT = 5
TOKENS_PER_PAGES = 500
MAX_RETRIES = 3
semaphore = threading.BoundedSemaphore(value=RATE_LIMIT)
total_links = 0
processed_links = 0
rate_limit_errors = 0
other_errors = 0
lock = threading.Lock()

def is_valid_domain(url):
    extracted = tldextract.extract(url)
    return bool(extracted.suffix)

def clean_url(url):
    url = url.lower().strip()
    url = re.sub(r'https?://(www\.)?', '', url)
    url = url.split('/')[0]
    if is_valid_domain(url):
        return url
    return None

def fetch_tokens(start):
    global rate_limit_errors, other_errors
    params = {
        'start': start,
        'limit': TOKENS_PER_PAGES,
        'filter': 'all',
        'showAll': 1
    }
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(API_URL, headers=HEADERS, params=params)
            response.raise_for_status()
            return response.json().get('tokens', [])
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                with lock:
                    rate_limit_errors += 1
                print(f"[Rate Limit Error] Too many requests. Retrying in {2 ** retries} seconds...")
            else:
                with lock:
                    other_errors += 1
                print(f"[API Error] {e}")
        except requests.RequestException as e:
            with lock:
                other_errors += 1
            print(f"[Requests Error] {e}")
        retries += 1
        time.sleep(2 ** retries)
    return []

def extract_urls(tokens, url_set):
    global total_links, processed_links
    for token in tokens:
        raw_url = token.get('projectSite')
        if raw_url:
            cleaned_url = clean_url(raw_url)
            if cleaned_url:
                with lock:
                    if cleaned_url not in url_set:
                        url_set.add(cleaned_url)
                        with open(OUTPUT, 'a', encoding='utf-8') as f:
                            f.write(f"{cleaned_url}\n")
                        total_links += 1
        with lock:
            processed_links += 1

def worker(start, url_set):
    with semaphore:
        tokens = fetch_tokens(start)
        if tokens:
            extract_urls(tokens, url_set)
        time.sleep(1 / RATE_LIMIT)

def main():
    global total_links, processed_links, rate_limit_errors, other_errors
    banner = r"""
   _______ _____  ____  _   _  _____   _____  ___   _   _ 
  |__   __|_   _/ __ \| \ | |/ ____| |  __ \|__ \ | \ | |
     | |    | || |  | |  \| | (___   | |__) |  ) ||  \| |
     | |    | || |  | | . ` |\___ \  |  _  /  / / | . ` |
     | |   _| || |__| | |\  |____) | | | \ \ / /_ | |\  |
     |_|  |_____\____/|_| \_|_____/  |_|  \_\____||_| \_|
     """
    print(banner)
    url_set = set()
    start = 0
    open(OUTPUT, 'w', encoding='utf-8').close()
    with ThreadPoolExecutor(max_workers=RATE_LIMIT) as executor:
        while True:
            future = executor.submit(worker, start, url_set)
            future.result()
            print(f"Processed: {processed_links} | Total Saved: {total_links} | Rate Limit Errrors: {rate_limit_errors} | Other Errors: {other_errors}")
            if len(fetch_tokens(start)) < TOKENS_PER_PAGES:
                break
            start += TOKENS_PER_PAGES
            print("\n Extraction complete!")
            print(f" Total Unique Links Extracted: {total_links}")
            print(f" Rate Limit Errors Encountered: {rate_limit_errors}")
            print(f" Other Errors Encountered: {other_errors}")

if __name__ == "__main__":
    main()