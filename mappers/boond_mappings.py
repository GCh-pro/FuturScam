"""
Mapper for Boond Manager API opportunities to MongoDB format.
Transforms Boond opportunity structure into MissionRequestPending format.

Uses mapper_to_mongo.py generic mapper engine with transformation functions.
"""

###############################################################################
# Enumerations
###############################################################################

# Origin Type Enumeration - maps origin.typeOf integer to text value
ORIGIN_TYPE_ENUM = {
    0: "Prospection",
    1: "Apporteur",
    2: "Collègue",
    3: "Réseau",
    4: "Appel d'offre",
    6: "Client",
    7: "Salon",
    8: "Google",
    9: "Pro-Unity",
    10: "ConnectingExpertise",
    11: "Agrega.io",
    12: "LittleBigConnection"
}

###############################################################################
# Transformation functions for custom logic
###############################################################################

def transform_origin_type(origin_type_id):
    """Convert origin.typeOf integer ID to text value"""
    if origin_type_id is None:
        return "Unknown"
    return ORIGIN_TYPE_ENUM.get(origin_type_id, f"Unknown ({origin_type_id})")

###############################################################################
# Mapping dictionaries for mapper_to_mongo.py engine
###############################################################################

BOOND_TO_MONGO_MAPPING = {
    # company info - maps to nested company object
    "data.attributes.place": "company.city",
    "data.attributes.companyName": "company.name",
    "data.attributes.country": "company.country",
    "data.attributes.street": "company.street",
    "data.attributes.zipcode": "company.zipcode",
    "data.attributes.region": "company.region",

    # conditions
    "data.attributes.startDate": "conditions.fromAt",
    "data.attributes.endDate": "conditions.toAt",
    "data.attributes.startImmediately": "conditions.startImmediately",
    "data.attributes.occupationType": "conditions.occupation",

    # top-level fields
    "data.id": "job_id",
    "data.attributes.reference": "job_reference",
    "data.attributes.title": "roleTitle",
    "data.attributes.description": "job_desc",
    "data.attributes.url": "job_url",
    
    # dates
    "data.attributes.creationDate": "publishedAt",
    "data.attributes.deadline": "deadlineAt",

    # status
    "data.attributes.isActive": "isActive",
    
    # defaults for required fields
    "data.attributes.origin.typeOf": "serviceProvider",
    
    # seniority - default to NS (Not Specified)
    "__constant__NS": "seniority",
    
    # remoteOption - will be set in apply_boond_defaults if not present
}

BOOND_LIST_MAPPINGS = {
    # skills: try from data.attributes.skills first
    "data.attributes.skills": ("skills", {"name": "name", "level": "seniority"}, lambda src, dst: dst),

    # skills from criteria (parsed by SkillBoy) - fallback if skills array is empty
    "data.attributes.criteria": ("skills_from_criteria", {}, lambda src, dst: {"name": src} if isinstance(src, str) else src),

    # languages: transform to expected format
    "data.attributes.languages": ("languages", {"language": "language", "level": "level"}, lambda src, dst: dst),
}


###############################################################################
# Post-mapping transformations
###############################################################################

def extract_company_name_from_included(opportunity: dict) -> str:
    """
    Extract company name from the 'included' section of Boond response.
    
    Boond returns company info in the 'included' array, we need to find the company entry.
    Returns the company name or None if not found.
    """
    try:
        # Boond response can be single object or wrapped in data
        if "data" in opportunity and isinstance(opportunity["data"], dict):
            # Single opportunity response from /information endpoint
            relationships = opportunity.get("data", {}).get("relationships", {})
            included = opportunity.get("included", [])
        else:
            # Shouldn't happen but fallback
            relationships = opportunity.get("relationships", {})
            included = opportunity.get("included", [])
        
        # Get the company relationship ID
        company_id = relationships.get("company", {}).get("data", {}).get("id")
        
        if not company_id:
            return None
        
        # Find the company in the included array
        for item in included:
            if item.get("type") == "company" and item.get("id") == str(company_id):
                name = item.get("attributes", {}).get("name")
                if name:
                    return name
        
        return None
    except Exception as e:
        print(f"[DEBUG] Error extracting company name: {e}")
        return None


def apply_boond_defaults(transformed: dict, original: dict = None) -> dict:
    """
    Apply defaults and post-processing transformations to Boond mapped document.
    
    Ensures:
    - Company name extracted from 'included' section
    - All required fields exist with appropriate defaults
    - deadlineAt set to 9999-12-31 if empty/null
    - Proper data types for all fields
    """
    from datetime import datetime, timedelta
    
    # Extract company name from included section if available
    if original:
        company_name = extract_company_name_from_included(original)
        if not transformed.get("company"):
            transformed["company"] = {}
        if company_name:
            transformed["company"]["name"] = company_name
    
    # Ensure nested objects exist
    if "company" not in transformed or not isinstance(transformed["company"], dict):
        transformed["company"] = {}
    
    if "conditions" not in transformed or not isinstance(transformed["conditions"], dict):
        transformed["conditions"] = {}
    
    # Ensure arrays exist
    if "skills" not in transformed or not isinstance(transformed["skills"], list):
        transformed["skills"] = []
    
    if "languages" not in transformed or not isinstance(transformed["languages"], list):
        transformed["languages"] = []
    
    # Company field defaults
    company = transformed["company"]
    company.setdefault("name", "Unknown Company")
    company.setdefault("city", "Unknown City")
    company.setdefault("country", "Unknown Country")
    company.setdefault("street", "Unknown")
    company.setdefault("zipcode", "00000")
    
    # Fix null/empty region - use city as fallback
    if not company.get("region"):
        company["region"] = company.get("city", "unknown").lower().replace(" ", "_")
    
    # Conditions field defaults
    conditions = transformed["conditions"]
    conditions.setdefault("startImmediately", False)
    conditions.setdefault("occupation", "FullTime")
    conditions.setdefault("fixedMargin", 0.0)
    
    # Ensure dailyRate structure
    if "dailyRate" not in conditions or not isinstance(conditions["dailyRate"], dict):
        conditions["dailyRate"] = {"currency": "EUR", "min": None, "max": None}
    
    dr = conditions["dailyRate"]
    dr.setdefault("currency", "EUR")
    
    # Date handling
    def validate_and_fix_date(date_str, default_value=None):
        """Convert date string to ISO format or return default."""
        if not date_str:
            return default_value
        
        if isinstance(date_str, str):
            if date_str.lower() in ["immediate", "immediat", "asap"]:
                return datetime.now().isoformat()
            try:
                # Try parsing ISO format
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.isoformat()
            except:
                try:
                    # Try other common formats
                    dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
                    return dt.isoformat()
                except:
                    return default_value
        
        return default_value
    
    # Set dates with defaults
    now = datetime.now()
    published_at = validate_and_fix_date(transformed.get("publishedAt"), now.isoformat())
    transformed["publishedAt"] = published_at
    
    # If deadline not set or empty string, default to 9999-12-31
    deadline_at = transformed.get("deadlineAt", "")
    if not deadline_at or deadline_at == "" or deadline_at is None:
        transformed["deadlineAt"] = "9999-12-31T23:59:59"
    else:
        # Validate the deadline if it exists
        deadline_at = validate_and_fix_date(deadline_at, "9999-12-31T23:59:59")
        transformed["deadlineAt"] = deadline_at
    
    # Validate fromAt and toAt
    if "fromAt" in conditions:
        conditions["fromAt"] = validate_and_fix_date(conditions["fromAt"], published_at)
    
    if "toAt" in conditions:
        conditions["toAt"] = validate_and_fix_date(conditions["toAt"], transformed.get("deadlineAt"))
    
    # Ensure job_id exists (critical for API calls)
    if not transformed.get("job_id"):
        transformed["job_id"] = f"boond_{transformed.get('job_reference', 'unknown')}"
    
    # Ensure job_url exists
    if not transformed.get("job_url"):
        transformed["job_url"] = f"https://boond.com/opportunities/{transformed.get('job_id')}"
    
    # Handle skills merging - if skills empty but skills_from_criteria exists, use that
    skills_from_criteria = transformed.pop("skills_from_criteria", [])
    if not transformed["skills"] and skills_from_criteria:
        # Convert criteria skills to proper format if needed
        if skills_from_criteria and isinstance(skills_from_criteria[0], str):
            transformed["skills"] = [{"name": skill, "seniority": "Required"} for skill in skills_from_criteria]
        else:
            transformed["skills"] = skills_from_criteria
    
    # Transform serviceProvider from integer ID to text value
    if "serviceProvider" in transformed:
        transformed["serviceProvider"] = transform_origin_type(transformed["serviceProvider"])
    else:
        transformed["serviceProvider"] = "Unknown"
    
    # Ensure seniority field exists with default "NS" if not set
    if "seniority" not in transformed or not transformed.get("seniority"):
        transformed["seniority"] = "NS"
    
    # Ensure remoteOption field exists with default "NotSpecified" if not set
    if "remoteOption" not in transformed or not transformed.get("remoteOption"):
        transformed["remoteOption"] = "NotSpecified"
    
    # Remove any internal fields that shouldn't be in MongoDB
    transformed.pop("skills_from_criteria", None)
    
    return transformed


