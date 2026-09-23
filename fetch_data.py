import os
import requests
import urllib3
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import db_manager

# Load environment variables from .env file
def load_env_file(env_path: str = ".env"):
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip("'\"")

load_env_file()

# Suppress SSL warnings for CWA domain
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CWA_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"

def get_cwa_api_key() -> str:
    """Read API Key from .env environment variable CWA_API_KEY."""
    return os.environ.get("CWA_API_KEY", "CWA-55FDA6D3-A43C-4AE0-BB30-E62D5F684FB2")

def fetch_cwa_api(api_key: Optional[str] = None) -> Optional[dict]:
    """Step 4: Fetch live JSON data for all 22 Taiwan counties from CWA API."""
    key = api_key if api_key else get_cwa_api_key()
    try:
        url = f"{CWA_API_URL}?Authorization={key}"
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

def run_pipeline(api_key: Optional[str] = None):
    """Step 7: Fetch CWA data using .env key, process with Pandas, and insert into SQLite DB."""
    db_manager.init_db()
    
    key_used = api_key if api_key else get_cwa_api_key()
    print(f"Fetching live data from CWA API via .env (Key length: {len(key_used)})...")
    json_data = fetch_cwa_api(key_used)
    records = []
    
    if json_data:
        records = parse_cwa_json(json_data)
    
    if not records:
        print("Warning: API fetch returned empty records.")
        return pd.DataFrame()
    
    # Step 7: Pandas DataFrame Preview
    df = pd.DataFrame(records)
    print("\n--- Step 7: Pandas DataFrame Data Preview (.env CWA API) ---")
    print(df.head(15))
    print(f"Total Records Fetched: {len(df)}")
    print("------------------------------------------------------------\n")
    
    # Step 8: Insert into SQLite
    inserted = db_manager.insert_forecasts(records)
    print(f"Successfully stored {inserted} records into SQLite (data.db).")
    return df

if __name__ == "__main__":
    run_pipeline()
