from fastapi import FastAPI, HTTPException, Query
from typing import Optional
import json
import os
import re

app = FastAPI()

# Load the JSON data
data_path = os.path.join(os.path.dirname(__file__), '../data/website_backup.json')

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

CAP_THRESHOLD = 20000  # Number of words

def count_words(text):
    return len(text.split())

def search(data, path_pattern=None, term_pattern=None, include_content=False):
    results = []
    path_regex = re.compile(path_pattern, re.IGNORECASE) if path_pattern else None
    term_regex = re.compile(term_pattern, re.IGNORECASE) if term_pattern else None
    total_words = 0
    path_matches = 0
    term_matches = 0

    for item in data:
        if total_words >= CAP_THRESHOLD:
            break

        path_match = path_regex.search(item['page-url']) if path_regex else False
        term_match = False

        if term_regex:
            for element in item['elements']:
                if any(term_regex.search(str(value)) for value in element.values()):
                    term_match = True
                    term_matches += 1
                    break

        if path_match or term_match:
            if include_content:
                results.append(item)
                total_words += count_words(' '.join(e.get('text', '') for e in item['elements']))
            else:
                results.append({"page-url": item['page-url']})

    return results, path_matches, term_matches

@app.get("/search")
async def search_endpoint(
    path: Optional[str] = Query(None, description="Path pattern to search for, use '|' as delimiter instead of '/'"),
    term: Optional[str] = Query(None, description="Term pattern to search for"),
    include_content: bool = Query(False, description="Whether to include full content in the response")
):
    if not path and not term:
        raise HTTPException(status_code=400, detail="At least one of 'path' or 'term' must be specified.")

    # Replace '|' with '/' for path pattern
    if path:
        path = path.replace('|', '/')

    results, path_matches, term_matches = search(data, path, term, include_content)

    total_words = sum(count_words(' '.join(e.get('text', '') for e in item.get('elements', []))) for item in results)
    capped = total_words >= CAP_THRESHOLD

    response = {
        "results": results,
        "path_matches": path_matches,
        "term_matches": term_matches,
        "capped": capped
    }

    if capped:
        response["note"] = f"CAPPED RESPONSE - {CAP_THRESHOLD} words limit reached. Be more specific to ensure you receive the complete website contents matching your filter criteria."

    return response


# local test: uvicorn main:app --reload