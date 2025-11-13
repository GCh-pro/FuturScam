from typing import List, Optional
from datetime import datetime


class Company:
    def __init__(self, city: str, contact: Optional[str], country: str, name: str, number: Optional[int],
                 region: str, street: str, zipcode: int):
        self.city = city
        self.contact = contact
        self.country = country
        self.name = name
        self.number = number
        self.region = region
        self.street = street
        self.zipcode = zipcode


class DailyRate:
    def __init__(self, currency: str, max_rate: Optional[float], min_rate: Optional[float]):
        self.currency = currency
        self.max = max_rate
        self.min = min_rate


class Conditions:
    def __init__(self, dailyRate: DailyRate, fixedMargin: float, fromAt: Optional[datetime],
                 occupation: str, startImmediately: bool, toAt: Optional[datetime]):
        self.dailyRate = dailyRate
        self.fixedMargin = fixedMargin
        self.fromAt = fromAt
        self.occupation = occupation
        self.startImmediately = startImmediately
        self.toAt = toAt


class Language:
    def __init__(self, language: str, level: str):
        self.language = language
        self.level = level


class Skill:
    def __init__(self, name: str, seniority: str):
        self.name = name
        self.seniority = seniority


class MissionRequestPending:
    def __init__(self, company: Company, conditions: Conditions, contractor: str, deadlineAt: datetime,
                 isActive: bool, job_desc: str, job_id: str, job_url: str,
                 languages: List[Language], metadata: Optional[str], publishedAt: datetime,
                 remoteOption: str, roleTitle: str, serviceProvider: str, skills: List[Skill]):
        self.company = company
        self.conditions = conditions
        self.contractor = contractor
        self.deadlineAt = deadlineAt
        self.isActive = isActive
        self.job_desc = job_desc
        self.job_id = job_id
        self.job_url = job_url
        self.languages = languages
        self.metadata = metadata
        self.publishedAt = publishedAt
        self.remoteOption = remoteOption
        self.roleTitle = roleTitle
        self.serviceProvider = serviceProvider
        self.skills = skills
