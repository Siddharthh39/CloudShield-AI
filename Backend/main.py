from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

from Backend.database import get_db
from Backend import models, schemas

app = FastAPI(title="API backend for Me-API Playground")


@app.middleware("http")
async def _ensure_cors_headers(request, call_next):
    """Ensure CORS headers are present even on errors."""
    response = await call_next(request)
    response.headers.setdefault("Access-Control-Allow-Origin", "*")
    response.headers.setdefault("Access-Control-Allow-Headers", "*")
    response.headers.setdefault("Access-Control-Allow-Methods", "*")
    return response


def _get_profile_or_404(db: Session, name: Optional[str]):
    """Return profile filtered by name (case-insensitive, trimmed, partial) or the first profile."""
    if name:
        trimmed = name.strip()
        if not trimmed:
            profile = db.query(models.Profile).first()
        else:
            lowered = trimmed.lower()
            profile = (
                db.query(models.Profile)
                .filter(func.lower(models.Profile.name) == lowered)
                .first()
            )
            if not profile:
                profile = (
                    db.query(models.Profile)
                    .filter(models.Profile.name.ilike(f"%{trimmed}%"))
                    .first()
                )
    else:
        profile = db.query(models.Profile).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

"""
----------------------------------------
Health Check
----------------------------------------
"""
@app.get("/health")
def health_check():
    return {"status": "ok"}


def _latest_scan(site):
    return max(site.scans, key=lambda scan: scan.started_at or datetime.min, default=None)


def _scan_payload(scan):
    if not scan:
        return None
    return {
        "id": scan.id,
        "status": scan.status,
        "risk_score": scan.risk_score,
        "grade": scan.grade,
        "summary": scan.summary,
        "started_at": scan.started_at,
        "duration_ms": scan.duration_ms,
        "log_count": scan.log_count,
        "request_count": scan.request_count,
        "blocked_count": scan.blocked_count,
        "findings": scan.findings,
        "log_events": scan.log_events,
    }


def _site_payload(site):
    return {
        "id": site.id,
        "url": site.url,
        "name": site.name,
        "status": site.status,
        "risk_score": site.risk_score,
        "grade": site.grade,
        "summary": site.summary,
        "technology": site.technology,
        "region": site.region,
        "tls_expiry": site.tls_expiry,
        "last_scan_at": site.last_scan_at,
        "latest_scan": _scan_payload(_latest_scan(site)),
    }


def _normalise_url(raw_url: str):
    value = raw_url.strip()
    if not value:
        raise HTTPException(status_code=400, detail="Enter a site URL to analyze")
    if "://" not in value:
        value = f"https://{value}"
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Enter a valid http or https URL")
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}", parsed.hostname or parsed.netloc


def _generic_scan(site, hostname):
    scan = models.SecurityScan(
        site=site,
        scan_key=f"manual-{hostname}",
        status="complete",
        risk_score=38,
        grade="B",
        summary="Baseline analysis completed. A few hardening opportunities should be addressed before production traffic increases.",
        started_at=datetime.now(timezone.utc).replace(tzinfo=None),
        duration_ms=842,
        log_count=1284,
        request_count=1284,
        blocked_count=17,
    )
    scan.findings = [
        models.SecurityFinding(
            finding_key=f"manual-{hostname}-headers",
            severity="medium",
            category="Headers",
            title="Security headers are incomplete",
            description="The baseline response does not advertise a complete defensive header policy.",
            recommendation="Add a strict Content-Security-Policy and review X-Content-Type-Options and Referrer-Policy.",
            evidence={"missing": ["content-security-policy", "permissions-policy"]},
            status="open",
        ),
        models.SecurityFinding(
            finding_key=f"manual-{hostname}-rate-limit",
            severity="low",
            category="Traffic",
            title="Rate limiting is not observable",
            description="The request sample does not show a clear rate-limit response or enforcement signal.",
            recommendation="Set a per-client request budget at the edge and emit limit decisions to your log stream.",
            evidence={"sampled_requests": 1284},
            status="open",
        ),
    ]
    scan.log_events = [
        models.LogEvent(
            event_key=f"manual-{hostname}-event-1",
            timestamp=scan.started_at,
            method="GET",
            path="/",
            status_code=200,
            source_ip="203.0.113.42",
            action="allowed",
            severity="info",
        ),
        models.LogEvent(
            event_key=f"manual-{hostname}-event-2",
            timestamp=scan.started_at,
            method="POST",
            path="/login",
            status_code=429,
            source_ip="198.51.100.19",
            action="rate_limited",
            severity="warning",
        ),
    ]
    return scan

'''
----------------------------------------
use this for local testing
----------------------------------------
'''

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app)
'''
----------------------------------------
for serverless deployment
----------------------------------------
'''
from mangum import Mangum
handler = Mangum(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


"""
----------------------------------------
Profile CRUD
----------------------------------------
"""

# Create Profile
@app.post("/profile", response_model=schemas.ProfileOut)
def create_profile(profile: schemas.ProfileCreate, db: Session = Depends(get_db)):
    db_profile = models.Profile(
        name=profile.name,
        email=profile.email,
        education=profile.education,
    )

    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


# Get Profile
@app.get("/profile", response_model=schemas.ProfileOut)
def get_profile(name: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return _get_profile_or_404(db, name)


# Update Profile
@app.put("/profile", response_model=schemas.ProfileOut)
def update_profile(
    profile: schemas.ProfileUpdate,
    name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    db_profile = _get_profile_or_404(db, name)

    db_profile.name = profile.name
    db_profile.email = profile.email
    db_profile.education = profile.education

    db.commit()
    db.refresh(db_profile)
    return db_profile


"""
----------------------------------------
Query Endpoints
----------------------------------------
"""

# Get Projects (optionally filtered by skill)
@app.get("/projects")
def get_projects(
    skill: Optional[str] = None,
    name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    profile = _get_profile_or_404(db, name)

    projects = profile.projects

    if skill:
        if skill.lower() not in [s.name.lower() for s in profile.skills]:
            return []

    return projects


# Top Skills
@app.get("/skills/top")
def top_skills(
    limit: int = 5,
    name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    profile = _get_profile_or_404(db, name)

    return [s.name for s in profile.skills][:limit]


# Search
@app.get("/search")
def search(
    q: str = Query(..., min_length=1),
    name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    profile = _get_profile_or_404(db, name)

    q = q.lower()

    return {
        "skills": [
            s.name for s in profile.skills
            if q in s.name.lower()
        ],
        "projects": [
            p for p in profile.projects
            if q in p.title.lower() or q in p.description.lower()
        ],
        "work": [
            w for w in profile.work
            if q in w.company.lower() or q in w.role.lower()
        ]
    }


@app.get("/sites")
def list_sites(db: Session = Depends(get_db)):
    sites = db.query(models.MonitoredSite).order_by(models.MonitoredSite.last_scan_at.desc()).all()
    return [_site_payload(site) for site in sites]


@app.get("/sites/{site_id}")
def get_site(site_id: int, db: Session = Depends(get_db)):
    site = db.query(models.MonitoredSite).filter(models.MonitoredSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site analysis not found")
    return _site_payload(site)


@app.post("/sites/analyze")
def analyze_site(request: schemas.AnalyzeRequest, db: Session = Depends(get_db)):
    normalized_url, hostname = _normalise_url(request.url)
    site = db.query(models.MonitoredSite).filter(models.MonitoredSite.url == normalized_url).first()
    if not site:
        site = models.MonitoredSite(
            url=normalized_url,
            name=hostname,
            status="watch",
            risk_score=38,
            grade="B",
            summary="New baseline analysis generated from the submitted URL.",
            technology="Web application",
            region="Local analysis",
            tls_expiry="Not observed",
            last_scan_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(site)
        db.flush()
        site.scans.append(_generic_scan(site, hostname))
        db.commit()
        db.refresh(site)
    return _site_payload(site)
