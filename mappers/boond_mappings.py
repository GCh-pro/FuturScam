"""
Mapper for Boond Manager API opportunities to MongoDB format.
Transforms Boond opportunity structure into MissionRequestPending format.

Uses mapper_to_mongo.py generic mapper engine with transformation functions.
"""
from datetime import datetime, timedelta
from typing import Any, Tuple, Callable, Dict

###############################################################################
# Transformation functions for custom logic
###############################################################################

def validate_and_fix_date(date_value: Any) -> str:
    """Convert various date formats to ISO format. Handle 'immediate' string."""
    if not date_value:
        return None
    if isinstance(date_value, str):
        # Handle "immediate" or similar invalid strings
        if date_value.lower() in ["immediate", "", "null"]:
            return None
        # Try to parse as ISO date
        try:
            datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            return date_value  # Already valid ISO
        except:
            return None
    return None


def get_default_deadline(published_at: str) -> str:
    """Calculate deadline as 7 days after published date."""
    try:
        if published_at:
            pub_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        else:
            pub_dt = datetime.now()
        return (pub_dt + timedelta(days=7)).isoformat()
    except:
        return (datetime.now() + timedelta(days=7)).isoformat()


def get_default_url(job_id: str) -> str:
    """Generate default job URL from job_id."""
    if job_id:
        return f"https://platform.pro-unity.com/opportunities/{job_id}"
    return "https://platform.pro-unity.com/opportunities/unknown"


def fix_region_null(region_value: Any, company_dict: Dict) -> str:
    """Ensure region is always a string, never null. Use city as fallback."""
    if region_value:
        return str(region_value).lower()
    # Fallback to city
    city = company_dict.get("city", "unknown")
    return str(city).lower() if city else "unknown"


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
    "data.attributes.serviceProvider": "serviceProvider",
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

def apply_boond_defaults(transformed: Dict[str, Any], original: Dict[str, Any]) -> Dict[str, Any]:
    """Apply default values and fix invalid data after mapping."""
    from mappers.mapper_to_mongo import map_json
    
    # Ensure company object exists and has all required fields
    if "company" not in transformed:
        transformed["company"] = {}
    
    company = transformed["company"]
    company.setdefault("name", "Unknown Company")
    company.setdefault("city", "Unknown")
    company.setdefault("country", "Unknown")
    company.setdefault("street", "")
    company.setdefault("zipcode", "")
    
    # Fix region: never null
    if "region" in company and not company["region"]:
        company["region"] = company.get("city", "Unknown").lower()
    elif "region" not in company:
        company["region"] = company.get("city", "Unknown").lower()
    
    # Ensure conditions object exists
    if "conditions" not in transformed:
        transformed["conditions"] = {}
    
    conditions = transformed["conditions"]
    conditions.setdefault("startImmediately", False)
    conditions.setdefault("occupation", "FullTime")
    conditions.setdefault("dailyRate", {"currency": "€", "min": None, "max": None})
    conditions.setdefault("fixedMargin", 0.0)
    
    # Fix invalid date strings in fromAt/toAt
    if "fromAt" in conditions and conditions["fromAt"]:
        fixed = validate_and_fix_date(conditions["fromAt"])
        if not fixed:
            conditions["fromAt"] = datetime.now().isoformat()
        else:
            conditions["fromAt"] = fixed
    
    if "toAt" in conditions and conditions["toAt"]:
        fixed = validate_and_fix_date(conditions["toAt"])
        if not fixed:
            conditions["toAt"] = (datetime.now() + timedelta(days=90)).isoformat()
        else:
            conditions["toAt"] = fixed
    
    # Merge skills from criteria (SkillBoy parsed) if skills is empty
    if "skills_from_criteria" in transformed and transformed["skills_from_criteria"]:
        if not transformed.get("skills"):
            # If no skills from data.attributes.skills, use criteria-based skills
            transformed["skills"] = transformed["skills_from_criteria"]
        # Remove the temporary field
    if "skills_from_criteria" in transformed:
        del transformed["skills_from_criteria"]
    
    # Ensure arrays exist
    transformed.setdefault("skills", [])
    transformed.setdefault("languages", [])
    
    # Ensure booleans
    transformed.setdefault("isActive", False)
    
    # Ensure serviceProvider
    transformed.setdefault("serviceProvider", "Boond Manager")
    
    # Ensure publishedAt
    if "publishedAt" not in transformed or not transformed.get("publishedAt"):
        pub_date = original.get("data", {}).get("attributes", {}).get("creationDate")
        if not pub_date:
            pub_date = original.get("data", {}).get("attributes", {}).get("updateDate")
        if not pub_date:
            pub_date = datetime.now().isoformat()
        transformed["publishedAt"] = pub_date
    
    # Ensure deadlineAt (required)
    if "deadlineAt" not in transformed or not transformed.get("deadlineAt"):
        deadline = original.get("data", {}).get("attributes", {}).get("deadline")
        if deadline:
            fixed = validate_and_fix_date(deadline)
            if fixed:
                transformed["deadlineAt"] = fixed
            else:
                transformed["deadlineAt"] = get_default_deadline(transformed.get("publishedAt"))
        else:
            transformed["deadlineAt"] = get_default_deadline(transformed.get("publishedAt"))
    
    # Ensure job_url (required)
    if "job_url" not in transformed or not transformed.get("job_url"):
        transformed["job_url"] = get_default_url(transformed.get("job_id"))
    
    return transformed
