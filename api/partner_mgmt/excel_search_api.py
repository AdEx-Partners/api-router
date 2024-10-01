from fastapi import FastAPI, HTTPException, Query
from typing import List
import pandas as pd
import os

app = FastAPI()

# Load the Excel data
excel_path = r"C:\Users\DirkSchlossmacher\Downloads\Partner List.xlsx"

def load_excel_file(path):
    if not os.path.exists(path):
        raise RuntimeError("File not found")
    if not os.access(path, os.R_OK):
        raise RuntimeError("File is not accessible")
    try:
        df = pd.read_excel(path)
        return df
    except Exception as e:
        raise RuntimeError(f"Error reading Excel file: {e}")

try:
    data = load_excel_file(excel_path)
except RuntimeError as e:
    print(f"Error loading Excel: {e}")
    raise HTTPException(status_code=500, detail=str(e))

def search(data, columns: List[str], search_terms: List[str]):
    if not columns or not search_terms:
        raise ValueError("Both columns and search terms must be provided")

    # Replace NaN values with an empty string
    data = data.fillna("")

    results = data[
        data[columns].apply(lambda row: any(term.lower() in str(row[col]).lower() for col in columns for term in search_terms), axis=1)
    ]
    return results.to_dict(orient='records')

@app.get("/search")
async def search_endpoint(
    columns: List[str] = Query(..., description="Columns to search in"),
    terms: List[str] = Query(..., description="Search terms")
):
    try:
        results = search(data, columns, terms)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"results": results}
