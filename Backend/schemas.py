from datetime import datetime
from typing import Any, Optional, List

from pydantic import BaseModel, EmailStr


class SkillOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class ProjectOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    links: Optional[str] = None

    class Config:
        orm_mode = True


class WorkExperienceOut(BaseModel):
    id: int
    company: str
    role: str
    duration: Optional[str] = None
    description: Optional[str] = None

    class Config:
        orm_mode = True


class LinksOut(BaseModel):
    id: int
    github: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None

    class Config:
        orm_mode = True


class ProfileBase(BaseModel):
    name: str
    email: EmailStr
    education: str


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass


class ProfileOut(ProfileBase):
    id: int
    skills: List[SkillOut] = []
    projects: List[ProjectOut] = []
    work: List[WorkExperienceOut] = []
    links: Optional[LinksOut] = None

    class Config:
        orm_mode = True


class AnalyzeRequest(BaseModel):
    url: str


class FindingOut(BaseModel):
    id: int
    severity: str
    category: str
    title: str
    description: Optional[str] = None
    recommendation: Optional[str] = None
    evidence: Optional[Any] = None
    status: str

    class Config:
        orm_mode = True


class LogEventOut(BaseModel):
    id: int
    timestamp: Optional[datetime] = None
    method: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None
    source_ip: Optional[str] = None
    action: Optional[str] = None
    severity: Optional[str] = None

    class Config:
        orm_mode = True


class ScanOut(BaseModel):
    id: int
    status: str
    risk_score: int
    grade: str
    summary: Optional[str] = None
    started_at: Optional[datetime] = None
    duration_ms: int
    log_count: int
    request_count: int
    blocked_count: int
    findings: List[FindingOut] = []
    log_events: List[LogEventOut] = []

    class Config:
        orm_mode = True


class SiteOut(BaseModel):
    id: int
    url: str
    name: str
    status: str
    risk_score: int
    grade: str
    summary: Optional[str] = None
    technology: Optional[str] = None
    region: Optional[str] = None
    tls_expiry: Optional[str] = None
    last_scan_at: Optional[datetime] = None
    latest_scan: Optional[ScanOut] = None

    class Config:
        orm_mode = True

