"""
Mapper for Boond Manager API opportunities to MongoDB format.
Transforms Boond opportunity structure into MissionRequestPending format.
"""

BOOND_TO_MONGO_MAPPING = {
    # company info
    "data.attributes.place": "company.city",
    "data.relationships.company.data.id": "company.company_id",
    "data.relationships.agency.data.id": "company.agency_id",

    # conditions
    "data.attributes.startDate": "conditions.fromAt",
    "data.attributes.endDate": "conditions.toAt",
    "data.attributes.duration": "conditions.duration",

    # top-level fields
    "data.id": "job_id",
    "data.attributes.reference": "job_reference",
    "data.attributes.title": "roleTitle",
    "data.attributes.description": "job_desc",
    "data.attributes.expertiseArea": "expertise_area",

    # dates
    "data.attributes.creationDate": "createdAt",
    "data.attributes.updateDate": "publishedAt",

    # status
    "data.attributes.state": "state",
    "data.attributes.isVisible": "isActive",
}

BOOND_LIST_MAPPINGS = {
    # skills: transform from criteria (which are already skill names)
    "data.attributes.criteria": ("skills", {}, lambda src, dst: {"name": src} if isinstance(src, str) else {"name": src.get("name", src)}),

    # languages from relationship or attributes
    "data.attributes.languages": ("languages", {"language": "language", "level": "level"}, lambda src, dst: dst),
}
