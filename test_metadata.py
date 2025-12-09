#!/usr/bin/env python3
"""
Test script to verify metadata extraction from Boond response
"""

import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mappers.boond_mappings import extract_resource_info_from_included

# Test data from your example
test_data = {
    'data': {
        'id': '841',
        'type': 'opportunity',
        'relationships': {
            'mainManager': {'data': {'id': '1', 'type': 'resource'}},
            'company': {'data': {'id': '293', 'type': 'company'}}
        }
    },
    'included': [
        {
            'id': '1',
            'type': 'resource',
            'attributes': {
                'lastName': 'Pernotte',
                'firstName': 'Clement'
            }
        },
        {
            'id': '293',
            'type': 'company',
            'attributes': {
                'name': 'i-City'
            }
        }
    ]
}

print("[TEST] Testing metadata extraction...")
print("=" * 80)

resource_info = extract_resource_info_from_included(test_data)

print("\n[RESULT] Extracted resource info:")
print(json.dumps(resource_info, indent=2))

print("\n" + "=" * 80)

if resource_info and resource_info.get("name") == "Clement Pernotte":
    print("[OK] Test passed! Metadata extraction works correctly.")
else:
    print("[ERROR] Test failed! Expected 'Clement Pernotte'")
