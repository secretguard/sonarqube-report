import requests
import csv
import json
import os

def get_input(prompt, default=None):
    if default:
        value = input(prompt + " [" + default + "]: ").strip()
        return value if value else default
    return input(prompt + ": ").strip()

def fetch_paged(base_url, endpoint, params, token):
    all_items = []
    page = 1
    while True:
        params["p"] = page
        params["ps"] = 500
        resp = requests.get(
            base_url + endpoint,
            params=params,
            auth=(token, "")
        )
        if resp.status_code != 200:
            print("  Warning: API returned " + str(resp.status_code) + " for " + endpoint)
            break
        data = resp.json()
        items = data.get("issues", data.get("hotspots", data.get("components", [])))
        all_items.extend(items)
        total = data.get("total", data.get("paging", {}).get("total", 0))
        if len(all_items) >= total or not items:
            break
        page += 1
    return all_items

def fetch_metrics(base_url, project, token):
    metric_keys = [
        "bugs", "vulnerabilities", "code_smells",
        "security_hotspots", "security_rating",
        "reliability_rating", "sqale_rating",
        "coverage", "duplicated_lines_density",
        "ncloc", "lines", "functions", "classes",
        "complexity", "cognitive_complexity",
        "security_review_rating"
    ]
    resp = requests.get(
        base_url + "/api/measures/component",
        params={
            "component": project,
            "metricKeys": ",".join(metric_keys)
        },
        auth=(token, "")
    )
    if resp.status_code != 200:
        return {}
    measures = resp.json().get("component", {}).get("measures", [])
    return {m["metric"]: m.get("value", "N/A") for m in measures}

def rating_label(value):
    ratings = {"1.0": "A", "2.0": "B", "3.0": "C", "4.0": "D", "5.0": "E"}
    return ratings.get(str(value), value)

def write_csv(filename, headers, rows):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print("  Saved: " + filename + " (" + str(len(rows)) + " rows)")

print("")
print("=" * 55)
print("  SonarQube Full Export Tool")
print("=" * 55)
print("")

SONAR_URL = get_input("SonarQube URL", "http://localhost:9000").rstrip("/")
PROJECT = get_input("Project Key")
TOKEN = get_input("Token (sqp_...)")
OUTPUT_DIR = get_input("Output folder name"")

print("")
print("Connecting to: " + SONAR_URL)
print("Project:       " + PROJECT)
print("")

# Test connection
test = requests.get(
    SONAR_URL + "/api/authentication/validate",
    auth=(TOKEN, "")
)
if test.status_code != 200 or not test.json().get("valid"):
    print("ERROR: Authentication failed. Check your token.")
    exit(1)
print("Authentication OK")
print("")

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 1. Project summary metrics ──────────────────────────
print("[1/6] Fetching project metrics...")
metrics = fetch_metrics(SONAR_URL, PROJECT, TOKEN)

summary_rows = [
    ["Lines of Code",          metrics.get("ncloc", "N/A")],
    ["Total Lines",            metrics.get("lines", "N/A")],
    ["Functions",              metrics.get("functions", "N/A")],
    ["Classes",                metrics.get("classes", "N/A")],
    ["Complexity",             metrics.get("complexity", "N/A")],
    ["Cognitive Complexity",   metrics.get("cognitive_complexity", "N/A")],
    ["Bugs",                   metrics.get("bugs", "N/A")],
    ["Vulnerabilities",        metrics.get("vulnerabilities", "N/A")],
    ["Code Smells",            metrics.get("code_smells", "N/A")],
    ["Security Hotspots",      metrics.get("security_hotspots", "N/A")],
    ["Security Rating",        rating_label(metrics.get("security_rating", "N/A"))],
    ["Reliability Rating",     rating_label(metrics.get("reliability_rating", "N/A"))],
    ["Maintainability Rating", rating_label(metrics.get("sqale_rating", "N/A"))],
    ["Coverage (%)",           metrics.get("coverage", "0.0")],
    ["Duplications (%)",       metrics.get("duplicated_lines_density", "N/A")],
]

write_csv(
    OUTPUT_DIR + "/1_project_summary.csv",
    ["Metric", "Value"],
    summary_rows
)

# ── 2. Vulnerabilities ───────────────────────────────────
print("[2/6] Fetching vulnerabilities...")
vulns = fetch_paged(SONAR_URL, "/api/issues/search",
    {"projectKeys": PROJECT, "types": "VULNERABILITY", "statuses": "OPEN,CONFIRMED,REOPENED"},
    TOKEN)

vuln_rows = []
for i in vulns:
    vuln_rows.append([
        i.get("severity"),
        i.get("rule"),
        i.get("component", "").split(":")[-1],
        i.get("line", ""),
        i.get("message"),
        i.get("status"),
        i.get("effort", ""),
        i.get("debt", ""),
        i.get("author", ""),
        ",".join(i.get("tags", []))
    ])

write_csv(
    OUTPUT_DIR + "/2_vulnerabilities.csv",
    ["Severity","Rule","File","Line","Message","Status","Effort","Debt","Author","Tags"],
    vuln_rows
)

# ── 3. Security Hotspots ─────────────────────────────────
print("[3/6] Fetching security hotspots...")
hotspots_resp = requests.get(
    SONAR_URL + "/api/hotspots/search",
    params={"projectKey": PROJECT, "ps": 500},
    auth=(TOKEN, "")
)

hotspot_rows = []
if hotspots_resp.status_code == 200:
    hotspots = hotspots_resp.json().get("hotspots", [])
    for h in hotspots:
        hotspot_rows.append([
            h.get("vulnerabilityProbability"),
            h.get("securityCategory", ""),
            h.get("component", "").split(":")[-1],
            h.get("line", ""),
            h.get("message"),
            h.get("status"),
            h.get("resolution", "Not reviewed"),
            h.get("author", "")
        ])
    write_csv(
        OUTPUT_DIR + "/3_security_hotspots.csv",
        ["Risk Level","Category","File","Line","Message","Status","Resolution","Author"],
        hotspot_rows
    )
else:
    print("  Warning: Could not fetch hotspots")

# ── 4. Reliability (Bugs) ────────────────────────────────
print("[4/6] Fetching reliability issues (bugs)...")
bugs = fetch_paged(SONAR_URL, "/api/issues/search",
    {"projectKeys": PROJECT, "types": "BUG", "statuses": "OPEN,CONFIRMED,REOPENED"},
    TOKEN)

bug_rows = []
for i in bugs:
    bug_rows.append([
        i.get("severity"),
        i.get("rule"),
        i.get("component", "").split(":")[-1],
        i.get("line", ""),
        i.get("message"),
        i.get("status"),
        i.get("effort", ""),
        i.get("author", "")
    ])

write_csv(
    OUTPUT_DIR + "/4_reliability_bugs.csv",
    ["Severity","Rule","File","Line","Message","Status","Effort","Author"],
    bug_rows
)

# ── 5. Maintainability (Code Smells) ────────────────────
print("[5/6] Fetching maintainability issues (code smells)...")
smells = fetch_paged(SONAR_URL, "/api/issues/search",
    {"projectKeys": PROJECT, "types": "CODE_SMELL", "statuses": "OPEN,CONFIRMED,REOPENED"},
    TOKEN)

smell_rows = []
for i in smells:
    smell_rows.append([
        i.get("severity"),
        i.get("rule"),
        i.get("component", "").split(":")[-1],
        i.get("line", ""),
        i.get("message"),
        i.get("status"),
        i.get("effort", ""),
        i.get("debt", "")
    ])

write_csv(
    OUTPUT_DIR + "/5_maintainability_codesmells.csv",
    ["Severity","Rule","File","Line","Message","Status","Effort","Tech Debt"],
    smell_rows
)

# ── 6. All issues combined ───────────────────────────────
print("[6/6] Fetching all issues combined...")
all_issues = fetch_paged(SONAR_URL, "/api/issues/search",
    {"projectKeys": PROJECT, "statuses": "OPEN,CONFIRMED,REOPENED"},
    TOKEN)

all_rows = []
for i in all_issues:
    all_rows.append([
        i.get("type"),
        i.get("severity"),
        i.get("rule"),
        i.get("component", "").split(":")[-1],
        i.get("line", ""),
        i.get("message"),
        i.get("status"),
        i.get("effort", ""),
        i.get("debt", ""),
        i.get("author", ""),
        ",".join(i.get("tags", []))
    ])

write_csv(
    OUTPUT_DIR + "/6_all_issues.csv",
    ["Type","Severity","Rule","File","Line","Message","Status","Effort","Debt","Author","Tags"],
    all_rows
)

# ── Final summary ────────────────────────────────────────
print("")
print("=" * 55)
print("  Export Complete")
print("=" * 55)
print("  Output folder : " + OUTPUT_DIR + "/")
print("  Project       : " + PROJECT)
print("")
print("  Files generated:")
print("  1_project_summary.csv      - Overall metrics")
print("  2_vulnerabilities.csv      - " + str(len(vuln_rows)) + " vulnerabilities")
print("  3_security_hotspots.csv    - " + str(len(hotspot_rows)) + " hotspots")
print("  4_reliability_bugs.csv     - " + str(len(bug_rows)) + " bugs")
print("  5_maintainability_codesmells.csv - " + str(len(smell_rows)) + " code smells")
print("  6_all_issues.csv           - " + str(len(all_rows)) + " total issues")
print("")
print("  Security Rating     : " + rating_label(metrics.get("security_rating", "N/A")))
print("  Reliability Rating  : " + rating_label(metrics.get("reliability_rating", "N/A")))
print("  Maintainability     : " + rating_label(metrics.get("sqale_rating", "N/A")))
print("  Vulnerabilities     : " + str(metrics.get("vulnerabilities", "N/A")))
print("  Hotspots            : " + str(metrics.get("security_hotspots", "N/A")))
print("  Bugs                : " + str(metrics.get("bugs", "N/A")))
print("  Code Smells         : " + str(metrics.get("code_smells", "N/A")))
print("=" * 55)
