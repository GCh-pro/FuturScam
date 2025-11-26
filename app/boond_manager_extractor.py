import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import jwt
import requests

# Add parent directory to sys.path to import params from root
sys.path.insert(0, str(Path(__file__).parent.parent))
import params
from mappers.boond_mappings import BOOND_TO_MONGO_MAPPING, BOOND_LIST_MAPPINGS
from mappers.mapper_to_mongo import map_json


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


def check_skillboy_health(skillboy_url: str = "http://localhost:8000") -> bool:
    """Check if SkillBoy API is healthy."""
    try:
        response = requests.get(
            f"{skillboy_url}/skillboy/health",
            timeout=10
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


def parse_criteria_with_skillboy(criteria_text: str, skillboy_url: str = "http://localhost:8000") -> list:
    """Parse criteria text using SkillBoy API to extract skills.
    Returns empty list if SkillBoy is unavailable."""
    
    try:
        response = requests.post(
            f"{skillboy_url}/skillboy",
            json={"text": criteria_text},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            skills = result.get("skills", [])
            return skills
        else:
            print(f"[WARN] SkillBoy API error: status {response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"[WARN] SkillBoy unavailable: {e}")
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
    
    # Check SkillBoy health once before processing
    skillboy_available = check_skillboy_health()
    if not skillboy_available:
        print("[WARN] SkillBoy API unavailable, will skip skills parsing")
    
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
            },
            timeout=30
        )
        
        if response.status_code == 200:
            try:
                opportunity = response.json()
                print(opportunity)
                # Parse criteria using SkillBoy API only if available
                if skillboy_available:
                    # Concatenate criteria and description for better skill extraction
                    criteria_text = opportunity.get("data", {}).get("attributes", {}).get("criteria", "")
                    description_text = opportunity.get("data", {}).get("attributes", {}).get("description", "")
                    combined_text = f"{criteria_text}\n{description_text}".strip()
                    
                    if combined_text:
                        skills = parse_criteria_with_skillboy(combined_text)
                        opportunity["data"]["attributes"]["criteria"] = skills
                details.append(opportunity)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON for opportunity {item_id}: {e}")
        else:
            print(f"Error fetching opportunity {item_id}: status {response.status_code}")
    
    return details


def transform_boond_to_mongo_format(opportunity: dict) -> dict:
    """Transform Boond opportunity to MongoDB RFP format using mapper engine."""
    from mappers.boond_mappings import (
        BOOND_TO_MONGO_MAPPING,
        BOOND_LIST_MAPPINGS,
        apply_boond_defaults
    )
    from mappers.mapper_to_mongo import map_json
    
    # Use the generic mapper engine
    transformed = map_json(opportunity, BOOND_TO_MONGO_MAPPING, BOOND_LIST_MAPPINGS)
    
    # Apply post-mapping transformations and defaults (pass original for company extraction)
    transformed = apply_boond_defaults(transformed, opportunity)
    
    return transformed




if __name__ == "__main__":
    data = fetch_boond_opportunities()
    if data:
        cutoff = datetime(2025, 11, 21, tzinfo=timezone.utc)
        recent_opportunities = filter_recent_opportunities(data, cutoff)
        
        print(f"Found {len(recent_opportunities)} recent opportunities")
        
        # Transform each opportunity to MongoDB format (actual saving happens in src/main.py)
        for opportunity in recent_opportunities:
            try:
                rfp_doc = transform_boond_to_mongo_format(opportunity)
                print(f"Transformed: {rfp_doc.get('job_id')} - {rfp_doc.get('roleTitle')}")
            except Exception as e:
                print(f"Error processing opportunity: {e}")
    
