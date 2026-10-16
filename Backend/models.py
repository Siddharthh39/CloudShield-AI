from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey, Table, JSON
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

profile_skills = Table(
    "profile_skills",
    Base.metadata,
    Column("profile_id", ForeignKey("profiles.id")),
    Column("skill_id", ForeignKey("skills.id"))
)

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    education = Column(Text)

    skills = relationship("Skill", secondary=profile_skills)
    projects = relationship("Project")
    work = relationship("WorkExperience")
    links = relationship("Links", uselist=False)

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    title = Column(String)
    description = Column(Text)
    links = Column(Text)

class WorkExperience(Base):
    __tablename__ = "work_experience"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    company = Column(String)
    role = Column(String)
    duration = Column(String)
    description = Column(Text)

class Links(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    github = Column(Text)
    linkedin = Column(Text)
    portfolio = Column(Text)


class MonitoredSite(Base):
    __tablename__ = "monitored_sites"

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="healthy")
    risk_score = Column(Integer, nullable=False, default=0)
    grade = Column(String, nullable=False, default="A")
    summary = Column(Text)
    technology = Column(String)
    region = Column(String)
    tls_expiry = Column(String)
    last_scan_at = Column(DateTime)

    scans = relationship("SecurityScan", back_populates="site", cascade="all, delete-orphan")


class SecurityScan(Base):
    __tablename__ = "security_scans"

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("monitored_sites.id"), nullable=False)
    scan_key = Column(String, unique=True, nullable=False)
    status = Column(String, nullable=False, default="complete")
    risk_score = Column(Integer, nullable=False, default=0)
    grade = Column(String, nullable=False, default="A")
    summary = Column(Text)
    started_at = Column(DateTime)
    duration_ms = Column(Integer, default=0)
    log_count = Column(Integer, default=0)
    request_count = Column(Integer, default=0)
    blocked_count = Column(Integer, default=0)

    site = relationship("MonitoredSite", back_populates="scans")
    findings = relationship("SecurityFinding", back_populates="scan", cascade="all, delete-orphan")
    log_events = relationship("LogEvent", back_populates="scan", cascade="all, delete-orphan")


class SecurityFinding(Base):
    __tablename__ = "security_findings"

    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey("security_scans.id"), nullable=False)
    finding_key = Column(String, unique=True, nullable=False)
    severity = Column(String, nullable=False)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    recommendation = Column(Text)
    evidence = Column(JSON)
    status = Column(String, nullable=False, default="open")

    scan = relationship("SecurityScan", back_populates="findings")


class LogEvent(Base):
    __tablename__ = "log_events"

    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey("security_scans.id"), nullable=False)
    event_key = Column(String, unique=True, nullable=False)
    timestamp = Column(DateTime)
    method = Column(String)
    path = Column(String)
    status_code = Column(Integer)
    source_ip = Column(String)
    action = Column(String)
    severity = Column(String)

    scan = relationship("SecurityScan", back_populates="log_events")
