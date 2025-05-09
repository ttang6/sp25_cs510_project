import requests
from bs4 import BeautifulSoup
import json
import os
import sys
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config.web_config as web_config

# Configuration
SAVE_PATH = '../data/rawJSON/web'
START_URL = web_config.URL
MAX_PAGES_PER_ROUND = 500

# Create save directory
os.makedirs(SAVE_PATH, exist_ok=True)


# Convert domain to safe filename
def sanitize_domain(domain):
    return re.sub(r'[^\w]', '_', domain).strip('_')


# Check robots.txt restrictions
def is_allowed(url, disallow_cache=None):
    if disallow_cache is None:
        disallow_cache = {}

    parsed = urlparse(url)
    netloc = parsed.netloc
    if netloc in disallow_cache:
        disallow = disallow_cache[netloc]
    else:
        robots_url = f"{parsed.scheme}://{netloc}/robots.txt"
        try:
            response = requests.get(robots_url, timeout=5)
            if response.status_code == 200:
                text = response.text
                disallow = []
                for line in text.split('\n'):
                    if line.strip().lower().startswith('disallow'):
                        _, rule = line.split(':', 1)
                        disallow.append(rule.strip())
                disallow_cache[netloc] = disallow
            else:
                disallow_cache[netloc] = []
        except:
            disallow_cache[netloc] = []

    path = parsed.path
    return not any(path.startswith(rule) for rule in disallow_cache[netloc])


# Extract links from page
def extract_links(soup, base_url, domain):
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href'].strip()
        full_url = urljoin(base_url, href).split('#')[0]
        if re.match(r'^https?://', full_url) and urlparse(full_url).netloc.endswith(domain):
            links.add(full_url)
    return links


# Extract page information
def extract_page_info(url, soup, outlinks, raw_html):
    title = soup.find('title').get_text(strip=True) if soup.find('title') else ''

    # Try common content containers
    content = ''
    for tag in [
        soup.find('article'),
        soup.find('main'),
        soup.find('div', class_='content'),
        soup.find('div', class_='main-content'),
        soup.find('div', class_='post-content'),
    ]:
        if tag:
            content = tag.get_text(strip=True)
            break
    if not content:
        content = soup.get_text(strip=True)[:2000]

    anchor_texts = {a.get_text(strip=True) for a in soup.find_all('a', href=True) if a.get_text(strip=True)}
    return {
        'url': url,
        'title': title,
        'anchor_texts': list(anchor_texts),
        'content': content,
        'outlinks': list(outlinks),
        'raw_html': raw_html
    }


# Crawl a single page
def crawl_page(url, visited, data_buffer, queue, domain, disallow_cache):
    if url in visited or not is_allowed(url, disallow_cache):
        return

    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print(f"Failed to access {url}: Status code {response.status_code}")
            return

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        outlinks = extract_links(soup, url, domain)
        page_info = extract_page_info(url, soup, outlinks, html)
        data_buffer.append(page_info)
        print(f"Crawled page {len(data_buffer)}: {url}")

        # Add new links to queue
        for link in outlinks:
            if link not in visited and link not in queue:
                queue.append(link)
        visited.add(url)

    except Exception as e:
        print(f"Error processing {url}: {e}")


# Save data to JSON file
def save_data(data_buffer, domain, timestamp):
    if data_buffer:
        file_path = os.path.join(SAVE_PATH, f'{domain}_{timestamp}_{len(data_buffer)}.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_buffer, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(data_buffer)} pages to {file_path}")


# Main crawling function
def main():
    domain = urlparse(START_URL).netloc
    sanitized_domain = sanitize_domain(domain)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # e.g., 20250418_123456

    if not is_allowed(START_URL):
        print(f"Start URL {START_URL} is blocked by robots.txt")
        return

    queue = [START_URL]
    visited = set()
    data_buffer = []
    disallow_cache = {}
    round_count = 1

    print("Starting crawl")
    while queue:
        url = queue.pop(0)  # Get the next URL from the queue (FIFO)
        crawl_page(url, visited, data_buffer, queue, domain, disallow_cache)

        if len(data_buffer) >= MAX_PAGES_PER_ROUND:
            print(f"Round {round_count} completed with {len(data_buffer)} pages")
            save_data(data_buffer, sanitized_domain, f"{timestamp}_round{round_count}")
            data_buffer = []
            round_count += 1

    if data_buffer:
        print(f"Final round completed with {len(data_buffer)} pages")
        save_data(data_buffer, sanitized_domain, f"{timestamp}_final")

    print("Crawling completed. All subdomains have been crawled.")


if __name__ == '__main__':
    main()