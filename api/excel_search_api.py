from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import pandas as pd
import os

router = APIRouter()

# Load the Excel data
excel_path = os.path.join(os.path.dirname(__file__), '../data/partner_mgmt/Partner_List.xlsx')

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
    print(data.head())  # Debug: Print the first few rows of the data
except RuntimeError as e:
    print(f"Error loading Excel: {e}")
    raise HTTPException(status_code=500, detail=str(e))

def search(data, search_terms: List[str], filter_column: Optional[str] = None, filter_substring: Optional[str] = None):
    if not search_terms:
        raise ValueError("Search terms must be provided")

    # Replace NaN values with an empty string
    data = data.fillna("")

    # Debug: Print the data shape and columns
    print(f"Data shape: {data.shape}")
    print(f"Data columns: {data.columns}")

    # Apply search terms filter across all columns
    results = data[
        data.apply(lambda row: any(term.lower() in str(value).lower() for value in row for term in search_terms), axis=1)
    ]

    # Debug: Print the results
    print(f"Results found: {len(results)}")
    print(results.head())

    # Apply optional substring filter
    if filter_column and filter_substring:
        # Find the actual column name that contains the substring
        matching_columns = [col for col in data.columns if filter_column.lower() in col.lower()]
        if not matching_columns:
            raise ValueError(f"No column found containing '{filter_column}'")
        # Use the first matching column
        actual_column = matching_columns[0]
        results = results[results[actual_column].str.contains(filter_substring, case=False, na=False)]

    return results.to_dict(orient='records')

@router.get("/excel_search")
async def search_endpoint(
    terms: List[str] = Query(..., description="Search terms"),
    filter_column: Optional[str] = Query(None, description="Column to apply substring filter"),
    filter_substring: Optional[str] = Query(None, description="Substring to filter the specified column")
):
    print("Endpoint reached with terms:", terms)
    try:
        results = search(data, terms, filter_column, filter_substring)
    except ValueError as e:
        print("Error during search:", e)
        raise HTTPException(status_code=400, detail=str(e))

    print("Search completed successfully")
    return {"results": results, "query": f"{terms}"}
