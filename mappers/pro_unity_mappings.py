import mappers

MAPPING = {
    # company
    "locationInfo.mainLocation.city": "company.city",
    "companyInfo.companyName": "company.name",
    "locationInfo.mainLocation.country": "company.country",
    "locationInfo.mainLocation.street": "company.street",
    "locationInfo.mainLocation.zipCode": "company.zipcode",
    "locationInfo.mainLocation.region": "company.region",

    # conditions
    "budgetInfo.currencyInfo.symbol": "conditions.dailyRate.currency",
    "budgetInfo.minDailyRate": "conditions.dailyRate.min",
    "budgetInfo.maxDailyRate": "conditions.dailyRate.max",
    "budgetInfo.fixedMargin": "conditions.fixedMargin",
    "budgetInfo.startDate": "conditions.fromAt",
    "budgetInfo.endDate": "conditions.toAt",
    "budgetInfo.canStartImmediately": "conditions.startImmediately",
    "budgetInfo.occupation": "conditions.occupation",

    # top-level
    "contractingPartyName": "contractor",
    "publicationInfo.applicationDeadline": "deadlineAt",
    "publicationInfo.publishDate": "publishedAt",
    "jobUrl": "job_url",
    "id": "job_id",
    "description": "job_desc",
    "roleInfo.roles[0].name": "roleTitle",
    "contractingPartyName": "serviceProvider",
    "publicationInfo.isClosed": "isActive",
}

###############################################################################
# LIST_MAPPINGS: déclarer ici comment convertir une liste source -> liste dest
# clé: chemin vers la liste dans source
# valeur: tuple(dest_list_path, item_field_map, optional_transform_fn)
# item_field_map: mapping champ source (clé dans item) -> champ dest (clé dans dest item)
# optional_transform_fn(item, mapped_item) -> can modify mapped_item (useful pour formater)
###############################################################################



LIST_MAPPINGS = {
    # skills: transform chaque élément {'name':..., 'seniority':...} -> same structure in dest 'skills'
    "skillInfo.skills": ("skills", {"name": "name", "seniority": "seniority"}, lambda src, dst: dst),


    "languageInfo.languageGroups": ("languages", {"language": "language", "level": "level"}, lambda src, dst: dst),

}