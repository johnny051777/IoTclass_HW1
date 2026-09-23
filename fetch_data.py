import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import db_manager

CWA_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"

def fetch_cwa_api(api_key: str) -> Optional[dict]:
    """Step 4: Fetch JSON data from Central Weather Administration (CWA) API."""
    try:
        url = f"{CWA_API_URL}?Authorization={api_key}"
        response = requests.get(url, timeout=10)
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
            
            # Combine MinT and MaxT by start time / date
            for min_item in mint_list:
                start_time = min_item.get("startTime", "")
                data_date = start_time.split(" ")[0] if " " in start_time else start_time
                mint_val = float(min_item.get("parameter", {}).get("parameterName", 20))
                
                # Find matching MaxT
                maxt_val = mint_val + 5.0  # default offset
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

def generate_sample_data() -> List[Dict[str, any]]:
    """
    Generate realistic 7-day temperature forecast dataset matching infographic.
    Regions: 北部地區, 中部地區, 南部地區, 東北部地區, 東部地區, 東南部地區
    Dates: 2026-04-14 to 2026-04-20
    """
    regions_base = {
        "北部地區": (18.0, 26.0),
        "中部地區": (20.0, 30.0),
        "南部地區": (22.0, 31.0),
        "東北部地區": (17.0, 24.0),
        "東部地區": (19.0, 27.0),
        "東南部地區": (21.0, 29.0)
    }
    
    start_date = datetime(2026, 4, 14)
    sample_records = []
    
    # 7-day variation simulation
    offsets = [
        (0, 0), (1, 1), (2, 2), (1, 0), (0, -1), (1, 1), (2, 0)
    ]
    
    for i in range(7):
        current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        d_min, d_max = offsets[i]
        
        for region, (base_mint, base_maxt) in regions_base.items():
            sample_records.append({
                "regionName": region,
                "dataDate": current_date,
                "mint": round(base_mint + d_min, 1),
                "maxt": round(base_maxt + d_max, 1)
            })
            
    return sample_records

def run_pipeline(api_key: Optional[str] = None):
    """Step 7: Run data pipeline using Pandas for preview and store records into SQLite DB."""
    db_manager.init_db()
    
    records = []
    if api_key:
        print("Fetching live data from CWA API...")
        json_data = fetch_cwa_api(api_key)
        if json_data:
            records = parse_cwa_json(json_data)
    
    if not records:
        print("Using sample weather forecast dataset matching the 7-day Taiwan Weather roadmap...")
        records = generate_sample_data()
    
    # Step 7: Pandas DataFrame Preview
    df = pd.DataFrame(records)
    print("\n--- Step 7: Pandas DataFrame Data Preview ---")
    print(df.head(10))
    print(f"Total Records Processed: {len(df)}")
    print("-------------------------------------------\n")
    
    # Step 8: Insert into SQLite
    inserted = db_manager.insert_forecasts(records)
    print(f"Successfully stored {inserted} new records into SQLite (data.db).")
    return df

if __name__ == "__main__":
    cwa_key = os.environ.get("CWA_API_KEY", None)
    run_pipeline(cwa_key)
