\set ON_ERROR_STOP on

INSERT INTO profiles (name, email, education)
VALUES ('Siddharth Singh', 'hellosiddharthh@email.com', 'B.Tech CSE')
ON CONFLICT (email) DO UPDATE
SET name = EXCLUDED.name, education = EXCLUDED.education
RETURNING id \gset profile_

INSERT INTO skills (name)
VALUES ('Python'), ('FastAPI'), ('PostgreSQL'), ('AWS')
ON CONFLICT (name) DO NOTHING;

INSERT INTO profile_skills
SELECT :profile_id, id
FROM skills
WHERE NOT EXISTS (
  SELECT 1
  FROM profile_skills
  WHERE profile_id = :profile_id AND skill_id = skills.id
);

INSERT INTO projects (profile_id, title, description)
SELECT
  :profile_id,
  'Portfolio Backend',
  'FastAPI backend hosted with AWS RDS'
WHERE NOT EXISTS (
  SELECT 1 FROM projects
  WHERE profile_id = :profile_id AND title = 'Portfolio Backend'
);

UPDATE links
SET github = 'https://github.com/siddharthh39',
    linkedin = 'https://www.linkedin.com/in/siddharth-singh-python-developer/',
    portfolio = 'https://siddharthh39.github.io/resume/'
WHERE profile_id = :profile_id;

INSERT INTO links (profile_id, github, linkedin, portfolio)
SELECT
  :profile_id,
  'https://github.com/siddharthh39',
  'https://www.linkedin.com/in/siddharth-singh-python-developer/',
  'https://siddharthh39.github.io/resume/'
WHERE NOT EXISTS (
  SELECT 1 FROM links WHERE profile_id = :profile_id
);

-- Cloud Shield demo analyses. These domains are intentionally non-production fixtures.
INSERT INTO monitored_sites (url, name, status, risk_score, grade, summary, technology, region, tls_expiry, last_scan_at)
VALUES ('https://northstar-retail.demo', 'Northstar Retail', 'healthy', 12, 'A', 'Strong baseline controls with only low-priority hardening opportunities.', 'Next.js, CloudFront, AWS WAF', 'us-east-1', '2026-12-18', '2026-10-16 09:42:00')
ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, status = EXCLUDED.status, risk_score = EXCLUDED.risk_score, grade = EXCLUDED.grade, summary = EXCLUDED.summary, technology = EXCLUDED.technology, region = EXCLUDED.region, tls_expiry = EXCLUDED.tls_expiry, last_scan_at = EXCLUDED.last_scan_at
RETURNING id \gset site_northstar_

INSERT INTO security_scans (site_id, scan_key, status, risk_score, grade, summary, started_at, duration_ms, log_count, request_count, blocked_count)
VALUES (:site_northstar_id, 'seed-northstar-2026', 'complete', 12, 'A', 'Strong baseline controls with only low-priority hardening opportunities.', '2026-10-16 09:42:00', 1280, 18420, 18420, 42)
ON CONFLICT (scan_key) DO UPDATE SET site_id = EXCLUDED.site_id, status = EXCLUDED.status, risk_score = EXCLUDED.risk_score, grade = EXCLUDED.grade, summary = EXCLUDED.summary, started_at = EXCLUDED.started_at, duration_ms = EXCLUDED.duration_ms, log_count = EXCLUDED.log_count, request_count = EXCLUDED.request_count, blocked_count = EXCLUDED.blocked_count
RETURNING id \gset scan_northstar_

INSERT INTO security_findings (scan_id, finding_key, severity, category, title, description, recommendation, evidence, status)
VALUES (:scan_northstar_id, 'seed-northstar-csp', 'low', 'Headers', 'CSP can be tightened', 'The policy allows a broad analytics source.', 'Restrict script sources to the approved analytics origin.', '{"header":"content-security-policy","confidence":0.96}', 'open')
ON CONFLICT (finding_key) DO UPDATE SET scan_id = EXCLUDED.scan_id, severity = EXCLUDED.severity, category = EXCLUDED.category, title = EXCLUDED.title, description = EXCLUDED.description, recommendation = EXCLUDED.recommendation, evidence = EXCLUDED.evidence, status = EXCLUDED.status;

INSERT INTO log_events (scan_id, event_key, timestamp, method, path, status_code, source_ip, action, severity)
VALUES (:scan_northstar_id, 'seed-northstar-log-1', '2026-10-16 09:41:34', 'GET', '/checkout', 200, '198.51.100.24', 'allowed', 'info')
ON CONFLICT (event_key) DO UPDATE SET scan_id = EXCLUDED.scan_id, timestamp = EXCLUDED.timestamp, method = EXCLUDED.method, path = EXCLUDED.path, status_code = EXCLUDED.status_code, source_ip = EXCLUDED.source_ip, action = EXCLUDED.action, severity = EXCLUDED.severity;

INSERT INTO monitored_sites (url, name, status, risk_score, grade, summary, technology, region, tls_expiry, last_scan_at)
VALUES ('https://atlas-health.demo', 'Atlas Health', 'watch', 46, 'B', 'The application is reachable and stable, but edge controls leave room for improvement.', 'Django, Nginx, PostgreSQL', 'eu-west-1', '2026-11-04', '2026-10-16 09:38:00')
ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, status = EXCLUDED.status, risk_score = EXCLUDED.risk_score, grade = EXCLUDED.grade, summary = EXCLUDED.summary, technology = EXCLUDED.technology, region = EXCLUDED.region, tls_expiry = EXCLUDED.tls_expiry, last_scan_at = EXCLUDED.last_scan_at
RETURNING id \gset site_atlas_

INSERT INTO security_scans (site_id, scan_key, status, risk_score, grade, summary, started_at, duration_ms, log_count, request_count, blocked_count)
VALUES (:site_atlas_id, 'seed-atlas-2026', 'complete', 46, 'B', 'The application is reachable and stable, but edge controls leave room for improvement.', '2026-10-16 09:38:00', 1640, 9210, 9210, 138)
ON CONFLICT (scan_key) DO UPDATE SET site_id = EXCLUDED.site_id, status = EXCLUDED.status, risk_score = EXCLUDED.risk_score, grade = EXCLUDED.grade, summary = EXCLUDED.summary, started_at = EXCLUDED.started_at, duration_ms = EXCLUDED.duration_ms, log_count = EXCLUDED.log_count, request_count = EXCLUDED.request_count, blocked_count = EXCLUDED.blocked_count;

INSERT INTO security_findings (scan_id, finding_key, severity, category, title, description, recommendation, evidence, status)
SELECT id, 'seed-atlas-rate-limit', 'medium', 'Traffic', 'Login endpoint lacks a visible rate limit', 'Repeated login attempts were observed without a consistent limit response.', 'Apply a route-specific limit at the edge and alert on sustained bursts.', '{"path":"/api/auth/login","burst":87,"window_seconds":60}', 'open'
FROM security_scans WHERE scan_key = 'seed-atlas-2026'
ON CONFLICT (finding_key) DO UPDATE SET scan_id = EXCLUDED.scan_id, severity = EXCLUDED.severity, category = EXCLUDED.category, title = EXCLUDED.title, description = EXCLUDED.description, recommendation = EXCLUDED.recommendation, evidence = EXCLUDED.evidence, status = EXCLUDED.status;

INSERT INTO log_events (scan_id, event_key, timestamp, method, path, status_code, source_ip, action, severity)
SELECT id, 'seed-atlas-log-1', '2026-10-16 09:36:12', 'POST', '/api/auth/login', 429, '203.0.113.18', 'rate_limited', 'warning'
FROM security_scans WHERE scan_key = 'seed-atlas-2026'
ON CONFLICT (event_key) DO UPDATE SET scan_id = EXCLUDED.scan_id, timestamp = EXCLUDED.timestamp, method = EXCLUDED.method, path = EXCLUDED.path, status_code = EXCLUDED.status_code, source_ip = EXCLUDED.source_ip, action = EXCLUDED.action, severity = EXCLUDED.severity;

INSERT INTO monitored_sites (url, name, status, risk_score, grade, summary, technology, region, tls_expiry, last_scan_at)
VALUES ('https://meridian-finance.demo', 'Meridian Finance', 'critical', 78, 'D', 'High-risk signals were detected across authentication, headers, and exposed administrative paths.', 'React, Express, Redis', 'ap-south-1', '2026-10-22', '2026-10-16 09:31:00')
ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name, status = EXCLUDED.status, risk_score = EXCLUDED.risk_score, grade = EXCLUDED.grade, summary = EXCLUDED.summary, technology = EXCLUDED.technology, region = EXCLUDED.region, tls_expiry = EXCLUDED.tls_expiry, last_scan_at = EXCLUDED.last_scan_at
RETURNING id \gset site_meridian_

INSERT INTO security_scans (site_id, scan_key, status, risk_score, grade, summary, started_at, duration_ms, log_count, request_count, blocked_count)
VALUES (:site_meridian_id, 'seed-meridian-2026', 'complete', 78, 'D', 'High-risk signals were detected across authentication, headers, and exposed administrative paths.', '2026-10-16 09:31:00', 2310, 14380, 14380, 24)
ON CONFLICT (scan_key) DO UPDATE SET site_id = EXCLUDED.site_id, status = EXCLUDED.status, risk_score = EXCLUDED.risk_score, grade = EXCLUDED.grade, summary = EXCLUDED.summary, started_at = EXCLUDED.started_at, duration_ms = EXCLUDED.duration_ms, log_count = EXCLUDED.log_count, request_count = EXCLUDED.request_count, blocked_count = EXCLUDED.blocked_count;

INSERT INTO security_findings (scan_id, finding_key, severity, category, title, description, recommendation, evidence, status)
SELECT id, 'seed-meridian-admin', 'critical', 'Exposure', 'Administrative route is publicly reachable', 'The scan observed a successful response from an administrative path outside the trusted network boundary.', 'Place administrative routes behind a private ingress or an identity-aware proxy immediately.', '{"path":"/admin/export","status_code":200,"source":"198.51.100.77"}', 'open'
FROM security_scans WHERE scan_key = 'seed-meridian-2026'
ON CONFLICT (finding_key) DO UPDATE SET scan_id = EXCLUDED.scan_id, severity = EXCLUDED.severity, category = EXCLUDED.category, title = EXCLUDED.title, description = EXCLUDED.description, recommendation = EXCLUDED.recommendation, evidence = EXCLUDED.evidence, status = EXCLUDED.status;

INSERT INTO security_findings (scan_id, finding_key, severity, category, title, description, recommendation, evidence, status)
SELECT id, 'seed-meridian-tls', 'high', 'Transport', 'TLS certificate renewal window is near', 'The certificate expires soon and no automated renewal signal was found in the collected telemetry.', 'Verify automated renewal and alert at least 30 days before expiry.', '{"expires":"2026-10-22","days_remaining":6}', 'open'
FROM security_scans WHERE scan_key = 'seed-meridian-2026'
ON CONFLICT (finding_key) DO UPDATE SET scan_id = EXCLUDED.scan_id, severity = EXCLUDED.severity, category = EXCLUDED.category, title = EXCLUDED.title, description = EXCLUDED.description, recommendation = EXCLUDED.recommendation, evidence = EXCLUDED.evidence, status = EXCLUDED.status;

INSERT INTO log_events (scan_id, event_key, timestamp, method, path, status_code, source_ip, action, severity)
SELECT id, 'seed-meridian-log-1', '2026-10-16 09:28:48', 'GET', '/admin/export', 200, '198.51.100.77', 'allowed', 'critical'
FROM security_scans WHERE scan_key = 'seed-meridian-2026'
ON CONFLICT (event_key) DO UPDATE SET scan_id = EXCLUDED.scan_id, timestamp = EXCLUDED.timestamp, method = EXCLUDED.method, path = EXCLUDED.path, status_code = EXCLUDED.status_code, source_ip = EXCLUDED.source_ip, action = EXCLUDED.action, severity = EXCLUDED.severity;
