from fastapi import FastAPI, HTTPException
import json
import os
import re

app = FastAPI()

# Load the JSON data
data_path = os.path.join(os.path.dirname(__file__), '../data/website_backup.json')

# Debugging function
def load_json_file(path):
    if not os.path.exists(path):
        raise RuntimeError("File not found")
    if not os.access(path, os.R_OK):
        raise RuntimeError("File is not accessible")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        raise RuntimeError(f"Error reading file: {e}")
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON format: {e}")

try:
    data = load_json_file(data_path)
except RuntimeError as e:
    print(f"Error loading JSON: {e}")
    raise HTTPException(status_code=500, detail=str(e))

# Configurable cap threshold
CAP_THRESHOLD = 20000  # Number of words

def count_words(text):
    return len(text.split())

def search(data, path_pattern=None, element=None, term_pattern=None):
    results = []
    path_regex = re.compile(path_pattern) if path_pattern else None
    term_regex = re.compile(term_pattern) if term_pattern else None
    total_words = 0

    for item in data:
        if total_words >= CAP_THRESHOLD:
            break

        paths = extract_paths([item])
        if path_regex and not any(path_regex.search(path) for path in paths):
            continue

        if element and term_regex:
            if element in item and term_regex.search(item[element]):
                results.append(item)
                total_words += count_words(item.get('text', ''))
        elif not element and term_regex:
            if any(term_regex.search(str(value)) for value in item.values()):
                results.append(item)
                total_words += count_words(item.get('text', ''))
        elif not element and not term_regex:
            results.append(item)
            total_words += count_words(item.get('text', ''))

    return results

def extract_paths(data):
    paths = []

    def recurse_path(path_dict, current_path=""):
        for key, value in path_dict.items():
            new_path = f"{current_path}/{key}" if current_path else key
            paths.append(new_path)
            recurse_path(value, new_path)

    for item in data:
        recurse_path(item['path'])

    return paths

@app.get("/search/{search_type:path}")
async def search_endpoint(search_type: str):
    parts = search_type.split('/')
    path_pattern = None
    element = None
    term_pattern = None

    if 'path' in parts:
        path_index = parts.index('path') + 1
        path_pattern = parts[path_index].replace('*', '.*')

    if 'element' in parts:
        element_index = parts.index('element') + 1
        element = parts[element_index]
        term_pattern = parts[element_index + 1].replace('*', '.*')

    results = search(data, path_pattern, element, term_pattern)

    # Check if the results were capped
    total_words = sum(count_words(item.get('text', '')) for item in results)
    if total_words >= CAP_THRESHOLD:
        return {
            "results": results,
            "note": f"CAPPED RESPONSE - {CAP_THRESHOLD} words limit reached. Be more specific to ensure you receive the complete website contents matching your filter criteria.",
        }

    return {"results": results}
