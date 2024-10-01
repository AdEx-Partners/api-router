import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import json

visited_urls = set()

def get_page_content(url):
    try:
        print(f"Fetching URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None

def parse_html_to_json(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    main_content = soup.find('main')
    if not main_content:
        print("No <main> tag found.")
        return None

    print("Found <main> content.")
    return parse_element(main_content, url)

def parse_element(element, url):
    content = {
        'page-url': url,
        'elements': [],
        'links': set()
    }

    last_element_name = None

    for child in element.descendants:
        if child.name == 'a':
            href = child.get('href')
            if href:
                full_url = urljoin(url, href)
                if should_visit_url(full_url, url):
                    content['links'].add(full_url)
        elif child.name in ['h1', 'h2']:
            text = child.get_text(strip=True)
            if last_element_name == child.name and content['elements']:
                content['elements'][-1][child.name] += f"\n{text}"
            else:
                content['elements'].append({child.name: text})
            last_element_name = child.name
        elif child.name is None and child.string.strip():
            text = child.string.strip()
            if last_element_name == 'text' and content['elements']:
                content['elements'][-1]['text'] += f"\n{text}"
            else:
                content['elements'].append({'text': text})
            last_element_name = 'text'

    content['links'] = list(content['links'])  # Convert set to list to remove duplicates

    return content


def should_visit_url(url, base_url):
    base_url, _ = urldefrag(url)  # Remove the fragment part
    if base_url in visited_urls:
        return False
    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)
    if parsed_url.netloc != parsed_base.netloc:
        return False
    allowed_paths = ['news', 'team', 'services', 'industries', 'corporate', 'contact']
    path_parts = parsed_url.path.strip('/').split('/')
    return len(path_parts) > 0 and path_parts[0] in allowed_paths

def backup_website_to_json(start_url, output_file):
    queue = [start_url]
    first_entry = True

    while queue:
        current_url = queue.pop(0)
        base_current_url, _ = urldefrag(current_url)
        if base_current_url in visited_urls:
            continue

        visited_urls.add(base_current_url)
        html_content = get_page_content(current_url)
        if html_content:
            structured_data = parse_html_to_json(html_content, current_url)
            if structured_data:
                with open(output_file, 'a', encoding='utf-8') as f:
                    if not first_entry:
                        f.write(',\n')
                    json.dump(structured_data, f, ensure_ascii=False, indent=2)
                    first_entry = False
                print(f"Processed {current_url}")

                # Add new links to the queue
                for link in structured_data['links']:
                    base_link, _ = urldefrag(link)
                    if base_link not in visited_urls:
                        queue.append(link)
            else:
                print("No structured data found.")
        else:
            print("Failed to retrieve HTML content.")
"""        if "adexpartners.com/services/ai-transformation/" in current_url:
            return
"""
if __name__ == '__main__':
    start_url = 'https://www.adexpartners.com/'
    output_file = './website_backup.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('[\n')
    backup_website_to_json(start_url, output_file)
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write('\n]\n')
