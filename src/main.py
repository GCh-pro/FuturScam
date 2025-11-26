import sys
from pathlib import Path

# Add parent directory to path to access app, mappers, helpers, params
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.job_mail_exporter import JobMailExporter  
from app.boond_manager_extractor import (
    fetch_boond_opportunities,
    filter_recent_opportunities,
    transform_boond_to_mongo_format
)
import mappers.pro_unity_mappings as pum
import mappers.mapper_to_mongo as ftm
from helpers import to_serializable
import os
import json
import requests
from datetime import datetime, timezone, date
import params


def save_to_mongodb_api(rfp_document: dict, api_url: str = "http://localhost:8000") -> bool:
    """Save RFP document to MongoDB via API POST /mongodb endpoint. 
    Falls back to UPDATE if document already exists (duplicate key error).
    """
    try:
        # Try POST (create)
        response = requests.post(
            f"{api_url}/mongodb",
            json=rfp_document,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] RFP created successfully: {result.get('id', 'Unknown ID')}")
            return True
        elif response.status_code == 400:
            # Check if it's a duplicate key error
            response_text = response.text.lower()
            if "duplicate key" in response_text or "e11000" in response_text:
                print(f"[RETRY] Document already exists, attempting UPDATE with job_id: {rfp_document.get('job_id')}")
                
                # Try UPDATE instead
                job_id = rfp_document.get('job_id')
                if job_id:
                    update_response = requests.put(
                        f"{api_url}/mongodb/{job_id}",
                        json=rfp_document,
                        timeout=30
                    )
                    
                    if update_response.status_code in [200, 204]:
                        print(f"[OK] RFP updated successfully: {job_id}")
                        return True
                    else:
                        print(f"[ERROR] Failed to update RFP: status {update_response.status_code}")
                        print(f"Response: {update_response.text}")
                        return False
                else:
                    print(f"[ERROR] No job_id found for update fallback")
                    return False
            else:
                print(f"[ERROR] MongoDB API error: status {response.status_code}")
                print(f"Response: {response.text}")
                return False
        else:
            print(f"[ERROR] MongoDB API error: status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"[ERROR] Error connecting to MongoDB API: {e}")
        return False


def cleanup_expired_rfps(api_url: str = "http://localhost:8000") -> int:
    """Get all RFPs and delete those with deadlineAt < today()."""
    try:
        # Get all RFPs
        response = requests.get(f"{api_url}/mongodb", timeout=30)
        
        if response.status_code != 200:
            print(f"[WARN] Failed to get all RFPs: status {response.status_code}")
            return 0
        
        all_rfps = response.json() if isinstance(response.json(), list) else response.json().get("data", [])
        
        today = date.today()
        expired_ids = []
        
        # Find RFPs with deadlineAt < today
        for rfp in all_rfps:
            deadline_str = rfp.get("deadlineAt")
            if deadline_str:
                try:
                    deadline_date = datetime.fromisoformat(deadline_str.replace("Z", "+00:00")).date()
                    if deadline_date < today:
                        expired_ids.append(rfp.get("job_id"))
                except (ValueError, AttributeError):
                    continue
        
        # Delete expired RFPs
        deleted_count = 0
        for rfp_id in expired_ids:
            try:
                delete_response = requests.delete(f"{api_url}/mongodb/{rfp_id}", timeout=30)
                if delete_response.status_code in [200, 204]:
                    deleted_count += 1
                    print(f"[OK] Deleted expired RFP: {rfp_id}")
                else:
                    print(f"[WARN] Failed to delete RFP {rfp_id}: status {delete_response.status_code}")
            except requests.RequestException as e:
                print(f"[WARN] Error deleting RFP {rfp_id}: {e}")
        
        if deleted_count > 0:
            print(f"[CLEANUP] Deleted {deleted_count} expired RFPs")
        return deleted_count
        
    except requests.RequestException as e:
        print(f"[WARN] Error during cleanup: {e}")
        return 0


def cleanup_closed_boond_rfps(boond_data: dict, api_url: str = "http://localhost:8000") -> int:
    """Delete RFPs from MongoDB if their Boond state != 'open' (0)."""
    try:
        deleted_count = 0
        
        for item in boond_data.get("data", []):
            item_id = item.get("id")
            state = item.get("attributes", {}).get("state")
            
            # If state exists and is not 0 (open), mark for deletion from MongoDB
            if state is not None and state != 0 and state != "0":
                try:
                    # Try to delete by job_id
                    delete_response = requests.delete(
                        f"{api_url}/mongodb/{item_id}",
                        timeout=30
                    )
                    if delete_response.status_code in [200, 204]:
                        deleted_count += 1
                        print(f"[OK] Deleted closed Boond RFP: {item_id} (state: {state})")
                    else:
                        # State might be closed, skip if not found
                        if delete_response.status_code != 404:
                            print(f"[WARN] Failed to delete Boond RFP {item_id}: status {delete_response.status_code}")
                except requests.RequestException as e:
                    print(f"[WARN] Error deleting Boond RFP {item_id}: {e}")
        
        if deleted_count > 0:
            print(f"[CLEANUP] Deleted {deleted_count} closed Boond RFPs from MongoDB")
        return deleted_count
        
    except Exception as e:
        print(f"[WARN] Error during Boond cleanup: {e}")
        return 0


def process_boond_opportunities(cutoff_date: datetime = None, api_url: str = "http://localhost:8000"):
    """Fetch and process Boond Manager opportunities."""
    if cutoff_date is None:
        cutoff_date = datetime(2025, 11, 20, tzinfo=timezone.utc)
    
    print("\n[DOWNLOAD] Fetching Boond Manager opportunities...")
    
    data = fetch_boond_opportunities()
    if not data:
        print("[ERROR] No data from Boond Manager API")
        return 0
    
    print(f"[FILTER] Filtering opportunities updated after {cutoff_date.date()}...")
    recent_opportunities = filter_recent_opportunities(data, cutoff_date)
    print(f"[OK] Found {len(recent_opportunities)} recent opportunities")
    
    saved_count = 0
    deleted_count = 0
    
    for opportunity in recent_opportunities:
        try:
            # Check if opportunity is closed (state != 0)
            state = opportunity.get("data", {}).get("state")
            job_id = opportunity.get("data", {}).get("id")
            
            if state is not None and state != 0 and state != "0":
                # Opportunity is closed, delete from MongoDB and skip processing
                print(f"[SKIP] Opportunity {job_id} is closed (state: {state}), deleting from MongoDB...")
                try:
                    delete_response = requests.delete(f"{api_url}/mongodb/{job_id}", timeout=30)
                    if delete_response.status_code in [200, 204]:
                        deleted_count += 1
                        print(f"[OK] Deleted closed opportunity: {job_id}")
                    elif delete_response.status_code != 404:
                        print(f"[WARN] Failed to delete {job_id}: status {delete_response.status_code}")
                except requests.RequestException as e:
                    print(f"[WARN] Error deleting {job_id}: {e}")
                continue  # Skip processing this opportunity
            
            # Opportunity is open, process normally
            rfp_doc = transform_boond_to_mongo_format(opportunity)
            
            # DEBUG: Print skills before API call
            print(f"\n[DEBUG] Document skills: {rfp_doc.get('skills')}")
            print(f"[DEBUG] Full RFP doc: {json.dumps(rfp_doc, indent=2, default=str)}")
            
            if save_to_mongodb_api(rfp_doc, api_url):
                saved_count += 1
        except Exception as e:
            print(f"[WARN] Error processing Boond opportunity: {e}")
    
    print(f"[OK] Successfully saved {saved_count}/{len(recent_opportunities)} Boond RFPs to MongoDB")
    if deleted_count > 0:
        print(f"[CLEANUP] Deleted {deleted_count} closed Boond RFPs from MongoDB")
    return saved_count


def main():
    exporter = JobMailExporter(
        client_id=params.AZURE_CLIENT,
        authority=params.AZURE_URI,
        scopes=["Mail.Read"],
        attachments_dir="attachments",
        init=False
    )
    
    print("[AUTH] Authenticating with Azure...")
    exporter.authenticate()

    print("[EMAIL] Processing emails...")
    exporter.process_emails()

    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)  
    json_folder = os.path.join(parent_dir, "app", "attachments")

    if not os.path.exists(json_folder):
        print(f"[WARN] Folder {json_folder} does not exist.")
        email_saved_count = 0
    else:
        email_saved_count = 0
        for filename in os.listdir(json_folder):
            if filename.endswith(".json"):
                file_path = os.path.join(json_folder, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        mission = ftm.map_json(data, pum.MAPPING, pum.LIST_MAPPINGS)
                        print(json.dumps(mission, default=to_serializable, indent=2, ensure_ascii=False))
                        
                        # Save to MongoDB via API instead of direct insertion
                        if save_to_mongodb_api(mission):
                            email_saved_count += 1
                    
                except Exception as e:
                    print(f"[WARN] Error reading {filename}: {e}")
                finally:
                    # Delete only the processed JSON file
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            print(f"[DELETE] File '{filename}' deleted")
                        except Exception as e:
                            print(f"[WARN] Error deleting '{filename}': {e}")
    
    print(f"\n[OK] Successfully saved {email_saved_count} email RFPs to MongoDB")
    
    # Process Boond opportunities
    boond_saved_count = process_boond_opportunities()
    
    # Clean up expired RFPs (deadlineAt < today)
    expired_count = cleanup_expired_rfps()
    
    print(f"\n[SUMMARY]")
    print(f"  - Email RFPs saved: {email_saved_count}")
    print(f"  - Boond RFPs saved: {boond_saved_count}")
    print(f"  - Expired RFPs deleted: {expired_count}")
    print(f"  - Total RFPs saved: {email_saved_count + boond_saved_count}")


if __name__ == "__main__":
    main()
