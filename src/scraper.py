"""
SERP snapshot fetcher
"""

import time
from datetime import datetime
from typing import List, Optional

from serp_client import BrightDataClient
from duckdb_manager import DuckDBManager


def fetch_snapshots(keywords: List[str], num_results: int = 10, delay: float = 1.0):
    """
    Fetch SERP snapshots for keywords and store in DuckDB
    
    Args:
        keywords: List of search keywords
        num_results: Number of results per keyword
        delay: Delay between API calls (seconds)
    """
    client = BrightDataClient()
    
    with DuckDBManager() as db:
        print(f"Fetching snapshots for {len(keywords)} keywords...")
        
        for idx, keyword in enumerate(keywords):
            try:
                # Fetch SERP results
                serp_data = client.search(keyword, num_results=num_results)
                
                # Extract organic results
                organic_results = []
                if isinstance(serp_data, dict) and 'organic' in serp_data:
                    organic_results = serp_data['organic']
                
                if organic_results:
                    # Insert snapshot
                    db.insert_snapshot(organic_results, keyword)
                    print(f"[{idx+1}/{len(keywords)}] '{keyword}': {len(organic_results)} results")
                else:
                    print(f"[{idx+1}/{len(keywords)}] '{keyword}': No results found")
                
                # Rate limiting
                if idx < len(keywords) - 1:
                    time.sleep(delay)
            
            except Exception as e:
                print(f"Error fetching '{keyword}': {e}")
                continue
        
        total = db.get_snapshot_count()
        print(f"\nTotal snapshots in database: {total}")
