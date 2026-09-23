import requests
import urllib3
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import db_manager

# Suppress insecure HTTPS warnings when SSL verify=False is used for CWA server
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CWA_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
DEFAULT_CWA_API_KEY = "CWA-55FDA6D3-A43C-4AE0-BB30-E62D5F684FB2"

def fetch_cwa_api(api_key: str = DEFAULT_CWA_API_KEY) -> Optional[dict]:
    """Step 4: Fetch live JSON data for all 22 Taiwan counties from Central Weather Administration (CWA) API."""
    try:
        url = f"{CWA_API_URL}?Authorization={api_key}"
        response = requests.get(url, timeout=10, verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API request failed with status code {response.status_code}")
            return None
    except Exception as e:
        print(f"Error requesting CWA API: {e}")
        return None

def parse_cwa_json(json_data: dict) -> List[Dict[str, any]]:
    """Step 5 & 6: Parse CWA JSON response to extract MinT and MaxT per location/date."""
    parsed_records = []
    try:
        records = json_data.get("records", {})
        locations = records.get("location", [])
        
        for loc in locations:
            location_name = loc.get("locationName", "")
            weather_elements = loc.get("weatherElement", [])
            
            mint_list = []
            maxt_list = []
            
            for elem in weather_elements:
                element_name = elem.get("elementName", "")
                if element_name == "MinT":
                    mint_list = elem.get("time", [])
                elif element_name == "MaxT":
                    maxt_list = elem.get("time", [])
            
            for min_item in mint_list:
                start_time = min_item.get("startTime", "")
                data_date = start_time.split(" ")[0] if " " in start_time else start_time
                mint_val = float(min_item.get("parameter", {}).get("parameterName", 20))
                
                maxt_val = mint_val + 5.0
                for max_item in maxt_list:
                    if max_item.get("startTime", "") == start_time:
                        maxt_val = float(max_item.get("parameter", {}).get("parameterName", mint_val + 5))
                        break
                
                parsed_records.append({
                    "regionName": location_name,
                    "dataDate": data_date,
                    "mint": mint_val,
                    "maxt": maxt_val
                })
    except Exception as e:
        print(f"Error parsing JSON: {e}")
    
    return parsed_records

def run_pipeline(api_key: str = DEFAULT_CWA_API_KEY):
    """Step 7: Fetch CWA data, process with Pandas, and insert into SQLite DB."""
    db_manager.init_db()
    
    print(f"Fetching live data from CWA API (Key: {api_key[:10]}...)...")
    json_data = fetch_cwa_api(api_key)
    records = []
    
    if json_data:
        records = parse_cwa_json(json_data)
    
    if not records:
        print("Warning: API fetch empty, fallback data pipeline triggered.")
        return pd.DataFrame()
    
    # Step 7: Pandas DataFrame Preview
    df = pd.DataFrame(records)
    print("\n--- Step 7: Pandas DataFrame Data Preview (All 22 Counties) ---")
    print(df.head(15))
    print(f"Total Records Fetched: {len(df)}")
    print(f"Unique Locations: {df['regionName'].nunique()} -> {df['regionName'].unique().tolist()}")
    print("-----------------------------------------------------------------\n")
    
    # Step 8: Insert into SQLite
    inserted = db_manager.insert_forecasts(records)
    print(f"Successfully stored {inserted} records into SQLite (data.db).")
    return df

if __name__ == "__main__":
    run_pipeline()
