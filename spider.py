import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import os
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime

# Configuration
SAVE_PATH = './RawJSON'
START_URL = 'https://grainger.illinois.edu/'
MAX_PAGES = 10
MAX_C = 10  # Maximum concurrent requests

# Create save directory
os.makedirs(SAVE_PATH, exist_ok=True)


# Convert domain to safe filename
def sanitize_domain(domain):
    return re.sub(r'[^\w]', '_', domain).strip('_')


# Check robots.txt restrictions (async)
async def is_allowed(url, session, disallow_cache=None):
    if disallow_cache is None:
        disallow_cache = {}

    parsed = urlparse(url)
    netloc = parsed.netloc
    if netloc in disallow_cache:
        disallow = disallow_cache[netloc]
    else:
        robots_url = f"{parsed.scheme}://{netloc}/robots.txt"
        try:
            async with session.get(robots_url, timeout=5) as response:
                if response.status == 200:
                    text = await response.text()
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


# Crawl a single page (async)
async def crawl_page(url, session, visited, data_buffer, queue, domain, semaphore, disallow_cache):
    async with semaphore:
        if url in visited or not await is_allowed(url, session, disallow_cache):
            return

        try:
            async with session.get(url, timeout=5) as response:
                if response.status != 200:
                    print(f"Failed to access {url}: Status code {response.status}")
                    return

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                outlinks = extract_links(soup, url, domain)
                page_info = extract_page_info(url, soup, outlinks, html)
                data_buffer.append(page_info)
                print(f"Crawled page {len(data_buffer)}: {url}")

                # Add new links to queue
                for link in outlinks:
                    if link not in visited:
                        await queue.put(link)
                visited.add(url)

        except Exception as e:
            print(f"Error processing {url}: {e}")


# Main crawling function
async def main():
    domain = urlparse(START_URL).netloc
    sanitized_domain = sanitize_domain(domain)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # e.g., 20250418_123456

    async with aiohttp.ClientSession() as session:
        if not await is_allowed(START_URL, session):
            print(f"Start URL {START_URL} is blocked by robots.txt")
            return

        queue = asyncio.Queue()
        await queue.put(START_URL)
        visited = set()
        data_buffer = []
        semaphore = asyncio.Semaphore(MAX_C)
        disallow_cache = {}

        print(f"Starting crawl with up to {MAX_C} concurrent requests")
        while not queue.empty() and len(data_buffer) < MAX_PAGES:
            # Collect tasks for concurrent execution
            tasks = []
            for _ in range(min(queue.qsize(), MAX_C)):
                if not queue.empty():
                    url = await queue.get()
                    tasks.append(
                        crawl_page(url, session, visited, data_buffer, queue, domain, semaphore, disallow_cache))

            if tasks:
                await asyncio.gather(*tasks)

        # Save all data to a single JSON file
        if data_buffer:
            file_path = os.path.join(SAVE_PATH, f'{sanitized_domain}_{timestamp}.json')
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_buffer, f, ensure_ascii=False, indent=4)
            print(f"Saved {len(data_buffer)} pages to {file_path}")

        print("Crawling completed.")


if __name__ == '__main__':
    asyncio.run(main())