#!/usr/bin/env python3
"""
Test script to fetch and display Boond Manager opportunities transformed to MongoDB format
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.boond_manager_extractor import (
    fetch_boond_opportunities,
    filter_recent_opportunities,
    transform_boond_to_mongo_format
)


def main():
    print("[TEST] Fetching Boond Manager opportunities...\n")
    
    # Fetch raw opportunities
    data = fetch_boond_opportunities()
    
    if not data:
        print("[ERROR] No data returned")
        return
    
    # Filter recent ones
    cutoff_date = datetime(2025, 11, 21, tzinfo=timezone.utc)
    recent = filter_recent_opportunities(data, cutoff_date)
    
    print(f"[OK] Found {len(recent)} recent opportunities\n")
    print("=" * 100)
    
    # Transform and display
    for idx, opp in enumerate(recent, 1):
        try:
            transformed = transform_boond_to_mongo_format(opp)
            
            print(f"\n[OPP {idx}]")
            print(f"  job_id: {transformed.get('job_id')}")
            print(f"  roleTitle: {transformed.get('roleTitle')}")
            print(f"  company.name: {transformed.get('company', {}).get('name')}")
            print(f"  deadlineAt: {transformed.get('deadlineAt')}")
            print(f"  publishedAt: {transformed.get('publishedAt')}")
            print(f"  skills: {len(transformed.get('skills', []))} skills")
            
        except Exception as e:
            print(f"\n[ERROR {idx}] {e}")
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
