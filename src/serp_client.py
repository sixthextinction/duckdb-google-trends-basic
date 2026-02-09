"""
Bright Data SERP API client
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class BrightDataClient:
    """Client for Bright Data SERP API"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        zone: Optional[str] = None,
        country: Optional[str] = None
    ):
        env_api_key = os.getenv("BRIGHT_DATA_API_KEY")
        env_zone = os.getenv("BRIGHT_DATA_ZONE")
        env_country = os.getenv("BRIGHT_DATA_COUNTRY")
        
        self.api_key = api_key or env_api_key
        self.zone = zone or env_zone
        self.country = country or env_country
        self.api_endpoint = "https://api.brightdata.com/request"
        
        if not self.api_key:
            raise ValueError(
                "BRIGHT_DATA_API_KEY must be provided via constructor or environment variable"
            )
        
        if not self.zone:
            raise ValueError(
                "BRIGHT_DATA_ZONE must be provided via constructor or environment variable"
            )
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        })
    
    def search(
        self,
        query: str,
        num_results: int = 10,
        language: Optional[str] = None,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a Google search via Bright Data SERP API"""
        search_url = (
            f"https://www.google.com/search"
            f"?q={requests.utils.quote(query)}"
            f"&num={num_results}"
            f"&brd_json=1"
        )
        
        if language:
            search_url += f"&hl={language}&lr=lang_{language}"
        
        target_country = country or self.country
        
        payload = {
            'zone': self.zone,
            'url': search_url,
            'format': 'json'
        }
        
        if target_country:
            payload['country'] = target_country
        
        try:
            response = self.session.post(
                self.api_endpoint,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Parse body JSON string if present
            if isinstance(result, dict) and 'body' in result:
                if isinstance(result['body'], str):
                    result['body'] = json.loads(result['body'])
                # Return the parsed body content
                return result['body']
            
            return result
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Search request failed with HTTP {e.response.status_code}"
            if e.response.text:
                error_msg += f": {e.response.text[:200]}"
            raise RuntimeError(error_msg) from e
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Search request failed: {e}") from e
