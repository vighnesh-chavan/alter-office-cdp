from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any


class Location(BaseModel):
    state: Optional[str]
    country: Optional[str]
    city: Optional[str]


class Demographics(BaseModel):
    age: Optional[int]
    gender: Optional[str]
    income: Optional[str]
    education: Optional[str]


class IngestData(BaseModel):
    cookie: str
    email: Optional[EmailStr]
    phone_number: Optional[str]
    location: Optional[Location]
    demographics: Optional[Demographics]
    interests: Optional[List[str]]


class IngestRequest(BaseModel):
    data: List[IngestData]


class IngestResponse(BaseModel):
    status: str
    records_processed: int
    errors: List[str] = []


class UserProfileResponse(BaseModel):
    user_profile: Dict[str, Any]


class SimilarUser(BaseModel):
    email: EmailStr
    similarity_score: float


class SimilarUsersResponse(BaseModel):
    cohort: str
    users: List[SimilarUser]
