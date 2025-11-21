import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import jwt
import requests

# Add parent directory to sys.path to import params from root
sys.path.insert(0, str(Path(__file__).parent.parent))
import params


def fetch_boond_opportunities():
    """Fetch opportunities from Boond Manager API using JWT authentication."""
    payload = { 
        "clientToken": params.CLIENT_BM,
        "clientKey": params.TOKEN_BM,
        "userToken": params.USER_BM
    }

    # Generate JWT token (HS256)
    jwt_token = jwt.encode(payload, params.TOKEN_BM, algorithm="HS256")
    
    url = "https://ui.boondmanager.com/api/opportunities"
    headers = {
        "X-Jwt-Client-BoondManager": jwt_token,
        "Accept": "application/json"
    }

    response = requests.get(url=url, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: received status code {response.status_code}")
        if not response.headers.get("Content-Type", "").startswith("application/json"):
            print("Server did NOT return JSON!")
            print(response.text[:500])
        return None
    
    return response.json()


def parse_criteria_with_skillboy(criteria_text: str) -> list:
    """Parse criteria text using SkillBoy API to extract skills."""
    skillboy_url = "http://localhost:8000/skillboy"
    
    try:
        response = requests.post(
            skillboy_url,
            json={"text": criteria_text},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            skills = result.get("skills", [])
            return skills
        else:
            print(f"SkillBoy API error: status {response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"Error connecting to SkillBoy API: {e}")
        return []


def filter_recent_opportunities(data: dict, cutoff_date: datetime) -> list:
    """Filter opportunities updated after cutoff_date and fetch their details."""
    filtered_ids = []
    for item in data.get("data", []):
        update_date_str = item.get("attributes", {}).get("updateDate")
        if not update_date_str:
            continue
        
        update_dt = datetime.fromisoformat(update_date_str.replace("Z", "+00:00"))
        if update_dt > cutoff_date:
            filtered_ids.append(item["id"])
    
    # Fetch details for each filtered opportunity
    details = []
    for item_id in filtered_ids:
        response = requests.get(
            f"https://ui.boondmanager.com/api/opportunities/{item_id}/information",
            headers={
                "X-Jwt-Client-BoondManager": jwt.encode(
                    {
                        "clientToken": params.CLIENT_BM,
                        "clientKey": params.TOKEN_BM,
                        "userToken": params.USER_BM
                    },
                    params.TOKEN_BM,
                    algorithm="HS256"
                ),
                "Accept": "application/json"
            }
        )
        
        if response.status_code == 200:
            try:
                opportunity = response.json()
                # Parse criteria using SkillBoy API
                criteria_text = opportunity.get("data", {}).get("attributes", {}).get("criteria", "")
                if criteria_text:
                    skills = parse_criteria_with_skillboy(criteria_text)
                    opportunity["data"]["attributes"]["criteria"] = skills
                details.append(opportunity)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON for opportunity {item_id}: {e}")
        else:
            print(f"Error fetching opportunity {item_id}: status {response.status_code}")
    
    return details


if __name__ == "__main__":
    data = fetch_boond_opportunities()
    if data:
        cutoff = datetime(2025, 11, 17, tzinfo=timezone.utc)
        recent_ids = filter_recent_opportunities(data, cutoff)
        print(json.dumps(recent_ids, indent=4, ensure_ascii=False))
    
