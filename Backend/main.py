from datetime import datetime, timezone
import json
import logging
import os
import ipaddress
import socket
import time
from time import perf_counter
import uuid
from functools import lru_cache
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

from Backend.database import get_db
from Backend import models, schemas

app = FastAPI(title="API backend for Me-API Playground")
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _cognito_jwks():
    region = os.getenv("COGNITO_REGION", os.getenv("AWS_REGION", "ap-south-1"))
    pool_id = os.getenv("COGNITO_USER_POOL_ID")
    if not pool_id:
        raise HTTPException(status_code=503, detail="Cognito is not configured")
    url = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"
    with urlopen(url, timeout=5) as response:
        return json.load(response)["keys"]


@lru_cache(maxsize=1)
def _gemini_api_key():
    secret_arn = os.getenv("GEMINI_API_KEY_SECRET_ARN")
    if not secret_arn:
        raise HTTPException(status_code=503, detail="Google Gemini is not configured")
    try:
        secret = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION")).get_secret_value(
            SecretId=secret_arn
        )
        value = json.loads(secret["SecretString"])
        api_key = value.get("api_key")
    except (BotoCoreError, ClientError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail="Google Gemini credentials are unavailable") from exc
    if not api_key or api_key == "configure-me":
        raise HTTPException(status_code=503, detail="Google Gemini API key has not been configured")
    return api_key


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if os.getenv("AUTH_REQUIRED", "false").lower() != "true" and credentials is None:
        return {"username": "local-demo", "groups": ["User"]}
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="A Cognito bearer token is required")

    region = os.getenv("COGNITO_REGION", os.getenv("AWS_REGION", "ap-south-1"))
    pool_id = os.getenv("COGNITO_USER_POOL_ID")
    client_id = os.getenv("COGNITO_APP_CLIENT_ID")
    issuer = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"
    try:
        claims = jwt.decode(
            credentials.credentials,
            _cognito_jwks(),
            algorithms=["RS256"],
            issuer=issuer,
            options={"verify_aud": False},
        )
    except (JWTError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid Cognito token") from exc
    if claims.get("token_use") == "access" and claims.get("client_id") != client_id:
        raise HTTPException(status_code=401, detail="Token was issued for another client")
    if claims.get("token_use") == "id" and claims.get("aud") != client_id:
        raise HTTPException(status_code=401, detail="Token was issued for another client")
    return claims


def _subject(user):
    subject = user.get("sub")
    if not subject:
        raise HTTPException(status_code=401, detail="Token has no user subject")
    return subject


def _is_admin(user):
    groups = user.get("cognito:groups", []) or user.get("groups", [])
    configured_admins = {
        email.strip().lower()
        for email in os.getenv("ADMIN_EMAILS", "").split(",")
        if email.strip()
    }
    return (
        "Admin" in groups
        or user.get("email", "").lower() in configured_admins
    )


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
        "owner_sub": site.owner_sub,
        "approval_status": site.approval_status,
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


def _public_hostname(hostname):
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise HTTPException(status_code=400, detail="The site hostname does not resolve") from exc
    if not addresses or any(ipaddress.ip_address(address).is_private or ipaddress.ip_address(address).is_loopback for address in addresses):
        raise HTTPException(status_code=400, detail="Private and internal network targets are not allowed")


def _passive_scan(site, url, hostname):
    scan_started = perf_counter()
    started_at = datetime.now(timezone.utc).replace(tzinfo=None)
    request = Request(url, headers={"User-Agent": "CloudShield-Passive-Scanner/1.0"})
    try:
        with urlopen(request, timeout=8) as response:
            headers = {key.lower(): value for key, value in response.headers.items()}
            status_code = response.status
    except Exception as exc:
        raise HTTPException(status_code=502, detail="The site could not be reached for passive analysis") from exc

    missing = [
        header for header in (
            "content-security-policy",
            "strict-transport-security",
            "x-content-type-options",
            "referrer-policy",
        ) if header not in headers
    ]
    risk_score = min(90, len(missing) * 15 + (10 if status_code >= 400 else 0))
    grade = "A" if risk_score < 20 else "B" if risk_score < 45 else "C" if risk_score < 70 else "D"
    scan = models.SecurityScan(
        site=site, scan_key=f"passive-{uuid.uuid4()}", status="complete",
        risk_score=risk_score, grade=grade,
        summary=f"Passive HTTPS analysis completed for {hostname}. {len(missing)} recommended controls were not observed.",
        started_at=started_at, duration_ms=0, log_count=1, request_count=1,
        blocked_count=0,
    )
    if missing:
        scan.findings.append(models.SecurityFinding(
            finding_key=f"passive-{uuid.uuid4()}",
            severity="high" if len(missing) >= 3 else "medium",
            category="Headers", title="Recommended security headers are missing",
            description="The passive response did not include all baseline defensive headers.",
            recommendation="Review and configure the missing headers in the site's production edge or application.",
            evidence={"missing_headers": missing, "status_code": status_code, "authorized": True},
            status="open",
        ))
    scan.log_events.append(models.LogEvent(
        event_key=f"passive-{uuid.uuid4()}", timestamp=started_at, method="GET",
        path="/", status_code=status_code, source_ip="passive-check",
        action="observed", severity="info",
    ))
    site.status, site.risk_score, site.grade = ("healthy" if risk_score < 30 else "watch" if risk_score < 60 else "critical"), risk_score, grade
    site.summary, site.last_scan_at = scan.summary, started_at
    scan.duration_ms = round((perf_counter() - scan_started) * 1000)
    return scan


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
def list_sites(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    user = _user
    query = db.query(models.MonitoredSite)
    if not _is_admin(user):
        query = query.filter(models.MonitoredSite.owner_sub == _subject(user))
    sites = query.order_by(models.MonitoredSite.last_scan_at.desc()).all()
    return [_site_payload(site) for site in sites]


@app.get("/sites/{site_id}")
def get_site(site_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    query = db.query(models.MonitoredSite).filter(models.MonitoredSite.id == site_id)
    if not _is_admin(_user):
        query = query.filter(models.MonitoredSite.owner_sub == _subject(_user))
    site = query.first()
    if not site:
        raise HTTPException(status_code=404, detail="Site analysis not found")
    return _site_payload(site)


@app.post("/sites/analyze")
def analyze_site(
    request: schemas.AnalyzeRequest,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    user = _user
    normalized_url, hostname = _normalise_url(request.url)
    site = db.query(models.MonitoredSite).filter(
        models.MonitoredSite.url == normalized_url,
        models.MonitoredSite.owner_sub == _subject(user),
    ).first()
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
            owner_sub=_subject(user),
            approval_status="pending_approval",
        )
        db.add(site)
        db.flush()
        db.commit()
        db.refresh(site)
    return _site_payload(site)


@app.post("/sites/register")
def register_site(
    request: schemas.SiteRegistrationRequest,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    normalized_url, hostname = _normalise_url(request.url)
    _public_hostname(hostname)
    if db.query(models.MonitoredSite).filter_by(url=normalized_url).first():
        raise HTTPException(status_code=409, detail="This site is already registered")
    site = models.MonitoredSite(
        url=normalized_url, name=request.name or hostname, status="pending",
        risk_score=0, grade="-", summary="Awaiting administrator approval before passive diagnostics.",
        technology="Not analyzed", region="Pending", tls_expiry="Not analyzed",
        owner_sub=_subject(_user), approval_status="pending_approval",
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return _site_payload(site)


@app.post("/sites/{site_id}/scan")
def scan_site(site_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    query = db.query(models.MonitoredSite).filter(models.MonitoredSite.id == site_id)
    if not _is_admin(_user):
        query = query.filter(models.MonitoredSite.owner_sub == _subject(_user))
    site = query.first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    if site.approval_status != "approved":
        raise HTTPException(status_code=409, detail="An administrator must approve this site before scanning")
    _public_hostname(urlparse(site.url).hostname or "")
    scan = _passive_scan(site, site.url, urlparse(site.url).hostname or "")
    db.add(scan)
    db.commit()
    db.refresh(site)
    return _site_payload(site)


@app.get("/admin/sites")
def pending_sites(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    if not _is_admin(_user):
        raise HTTPException(status_code=403, detail="Administrator role required")
    return [_site_payload(site) for site in db.query(models.MonitoredSite).filter_by(approval_status="pending_approval").all()]


@app.post("/admin/sites/{site_id}/approve")
def approve_site(site_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    if not _is_admin(_user):
        raise HTTPException(status_code=403, detail="Administrator role required")
    site = db.query(models.MonitoredSite).filter_by(id=site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    site.approval_status = "approved"
    site.status = "watch"
    site.summary = "Approved. Ready for passive diagnostics."
    db.commit()
    return _site_payload(site)


@app.post("/ai/explain", response_model=schemas.AiExplainOut)
def explain_finding(
    request: schemas.AiExplainRequest,
    _user=Depends(get_current_user),
):
    model_id = os.getenv("GEMINI_MODEL_ID", "gemini-3.8-flash")
    prompt = (
        "You are a defensive website security analyst. Analyze the finding using only the supplied "
        "evidence. Do not claim malware, spyware, hacking, exploitation, compromise, or a specific "
        "CVE was detected unless the evidence explicitly proves it. Distinguish observed evidence "
        "from plausible risk scenarios. Return these labeled sections concisely:\n"
        "Explanation: what was observed and why it matters.\n"
        "Threat scenarios: realistic attack techniques or abuse that this weakness can enable, "
        "without claiming they occurred.\n"
        "Detection status: state clearly what this passive check did not test, including malware "
        "and spyware detection when applicable.\n"
        "Recommendation: prioritized remediation steps.\n"
        "Verification: a quick way to confirm the fix.\n\n"
        f"Severity: {request.severity}\nTitle: {request.title}\n"
        f"Description: {request.description}\nExisting recommendation: {request.recommendation or 'None'}\n"
        f"Evidence: {json.dumps(request.evidence or {})}"
    )
    request_body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 300, "temperature": 0.2},
    }).encode()
    text_output = None
    last_error = None
    for attempt in range(2):
        try:
            gemini_request = Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
                f"?key={_gemini_api_key()}",
                data=request_body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(gemini_request, timeout=8) as response:
                response_body = json.load(response)
            text_output = response_body["candidates"][0]["content"]["parts"][0]["text"].strip()
            break
        except HTTPException:
            raise
        except HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:1000]
            logger.error("Google Gemini returned HTTP %s: %s", exc.code, body)
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 1:
                break
            time.sleep(0.25)
        except (TimeoutError, URLError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            logger.error("Google Gemini response failed: %s", exc)
            last_error = exc
            if attempt == 1:
                break
            time.sleep(0.25)

    if text_output is None:
        logger.warning("Using local explanation fallback after Gemini failure: %s", last_error)
        text_output = (
            f"Explanation: The {request.severity} finding '{request.title}' was identified from "
            "the supplied passive evidence.\n"
            "Threat scenarios: Depending on the missing control, attackers may abuse browser "
            "confusion, content injection, or information leakage; this scan does not show that "
            "any attack occurred.\n"
            "Detection status: Malware, spyware, and compromise were not detected or ruled out by "
            "this passive response check.\n"
            f"Recommendation: {request.recommendation or 'Review the supplied evidence and apply remediation after validation.'}\n"
            "Verification: Repeat the passive check and confirm the relevant control is present."
        )
        model_id = "local-test-fallback"

    explanation = text_output
    recommendation = request.recommendation or "Review the generated guidance against the supplied evidence before applying changes."
    if "Recommendation:" in text_output:
        explanation, recommendation = text_output.split("Recommendation:", 1)
        explanation = explanation.replace("Explanation:", "").strip()
        recommendation = recommendation.strip()
    if not explanation:
        explanation = "The model returned no explanation for this finding."
    return {"explanation": explanation, "recommendation": recommendation, "model": model_id}
