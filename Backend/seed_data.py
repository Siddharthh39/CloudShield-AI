from datetime import datetime

from sqlalchemy.orm import Session

from Backend import models


DEMO_SITES = [
    {
        "url": "https://northstar-retail.demo",
        "name": "Northstar Retail",
        "status": "healthy",
        "risk_score": 12,
        "grade": "A",
        "summary": "Strong baseline controls with only low-priority hardening opportunities.",
        "technology": "Next.js, CloudFront, AWS WAF",
        "region": "us-east-1",
        "tls_expiry": "2026-12-18",
        "scan_key": "seed-northstar-2026",
        "finding": ("low", "Headers", "CSP can be tightened", "The policy allows a broad analytics source.", "Restrict script sources to the approved analytics origin."),
    },
    {
        "url": "https://atlas-health.demo",
        "name": "Atlas Health",
        "status": "watch",
        "risk_score": 46,
        "grade": "B",
        "summary": "The application is reachable and stable, but edge controls leave room for improvement.",
        "technology": "Django, Nginx, PostgreSQL",
        "region": "eu-west-1",
        "tls_expiry": "2026-11-04",
        "scan_key": "seed-atlas-2026",
        "finding": ("medium", "Traffic", "Login endpoint lacks a visible rate limit", "Repeated login attempts were observed without a consistent limit response.", "Apply a route-specific limit at the edge and alert on sustained bursts."),
    },
    {
        "url": "https://meridian-finance.demo",
        "name": "Meridian Finance",
        "status": "critical",
        "risk_score": 78,
        "grade": "D",
        "summary": "High-risk signals were detected across authentication, headers, and exposed administrative paths.",
        "technology": "React, Express, Redis",
        "region": "ap-south-1",
        "tls_expiry": "2026-10-22",
        "scan_key": "seed-meridian-2026",
        "finding": ("critical", "Exposure", "Administrative route is publicly reachable", "The snapshot observed a successful response from an administrative path outside the trusted network boundary.", "Place administrative routes behind a private ingress or an identity-aware proxy immediately."),
    },
    {
        "url": "https://example.com",
        "name": "Example Commerce (demo snapshot)",
        "status": "watch",
        "risk_score": 31,
        "grade": "B",
        "summary": "Public example-domain telemetry is included as a non-production demonstration snapshot.",
        "technology": "Apache, CDN",
        "region": "us-east-1",
        "tls_expiry": "2027-01-15",
        "scan_key": "seed-example-2026",
        "finding": ("low", "Headers", "Security policy coverage should be reviewed", "The demo snapshot does not contain evidence for every recommended response header.", "Confirm the production response policy and add missing headers where appropriate."),
    },
]


def seed_demo_data(db: Session) -> None:
    for item in DEMO_SITES:
        site = db.query(models.MonitoredSite).filter_by(url=item["url"]).one_or_none()
        if site is None:
            site = models.MonitoredSite(url=item["url"])
            db.add(site)
        for key in ("name", "status", "risk_score", "grade", "summary", "technology", "region", "tls_expiry"):
            setattr(site, key, item[key])
        site.last_scan_at = datetime(2026, 10, 16, 9, 42)
        db.flush()

        scan = db.query(models.SecurityScan).filter_by(scan_key=item["scan_key"]).one_or_none()
        if scan is None:
            scan = models.SecurityScan(scan_key=item["scan_key"], site_id=site.id)
            db.add(scan)
        scan.status = "complete"
        scan.risk_score = item["risk_score"]
        scan.grade = item["grade"]
        scan.summary = item["summary"]
        scan.started_at = site.last_scan_at
        scan.duration_ms = 1280
        scan.log_count = 18420
        scan.request_count = 18420
        scan.blocked_count = 42
        db.flush()

        finding = db.query(models.SecurityFinding).filter_by(finding_key=f"{item['scan_key']}-finding").one_or_none()
        if finding is None:
            finding = models.SecurityFinding(finding_key=f"{item['scan_key']}-finding", scan_id=scan.id)
            db.add(finding)
        finding.severity, finding.category, finding.title, finding.description, finding.recommendation = item["finding"]
        finding.evidence = {"source": "seeded demonstration snapshot", "authorized": True}
        finding.status = "open"

        event = db.query(models.LogEvent).filter_by(event_key=f"{item['scan_key']}-log").one_or_none()
        if event is None:
            event = models.LogEvent(event_key=f"{item['scan_key']}-log", scan_id=scan.id)
            db.add(event)
        event.timestamp = site.last_scan_at
        event.method = "GET"
        event.path = "/"
        event.status_code = 200
        event.source_ip = "203.0.113.42"
        event.action = "allowed"
        event.severity = "info"
    db.commit()
