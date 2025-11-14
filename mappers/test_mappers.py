MAPPING = {
    # company info
    "org.label": "company.name",
    "org.hq.addr.street": "company.street",
    "org.hq.addr.zip": "company.zipcode",
    "org.hq.addr.city": "company.city",
    "org.hq.addr.country": "company.country",
    "org.hq.regionName": "company.region",

    # job details
    "jobDetails.identifier": "job_id",
    "jobDetails.summary": "job_desc",
    "jobDetails.url": "job_url",

    # timings
    "timings.deadline": "deadlineAt",
    "timings.publication": "publishedAt",
    "timings.start.from": "conditions.fromAt",
    "timings.start.to": "conditions.toAt",
    "timings.start.immediate": "conditions.startImmediately",

    # payment/conditions
    "payment.currency": "conditions.dailyRate.currency",
    "payment.range.low": "conditions.dailyRate.min",
    "payment.range.high": "conditions.dailyRate.max",
    "payment.marginFixed": "conditions.fixedMargin",

    # contractor & active flag
    "collaboration.contractorName": "contractor",
    "collaboration.isClosedFlag": "isActive"
}
LIST_MAPPINGS = {
    # languages → simple copy
    "langs": (
        "languages",
        {"lang": "language", "level": "level"},
        lambda src, dst: dst
    ),

    # skills → simple copy
    "techStack.requiredSkills": (
        "skills",
        {"label": "name", "xp": "seniority"},
        lambda src, dst: dst
    )
}