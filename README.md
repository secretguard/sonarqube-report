# SonarQube Full Export Tool

> Export everything from SonarQube into organized CSV files — vulnerabilities, security hotspots, bugs, code smells, and project metrics — with a single interactive script.

---

## Table of Contents

- [What This Script Does](#what-this-script-does)
- [Requirements](#requirements)
- [Installation](#installation)
- [Getting Your Token](#getting-your-token)
- [Running the Script](#running-the-script)
- [Understanding the Output](#understanding-the-output)
- [Example Session](#example-session)
- [Troubleshooting](#troubleshooting)
- [Tested With](#tested-with)
- [Use Case](#use-case)
- [License](#license)

---

## What This Script Does

`sonar_report.py` connects to any SonarQube instance using its REST API and exports the full analysis results for a given project into six structured CSV files.

It covers every category SonarQube reports on:

| File | Contents | SonarQube Category |
|---|---|---|
| `1_project_summary.csv` | Ratings, lines of code, coverage, complexity | Dashboard overview |
| `2_vulnerabilities.csv` | Security vulnerabilities with severity and location | Security |
| `3_security_hotspots.csv` | Hotspots requiring human review, risk level | Security Hotspots |
| `4_reliability_bugs.csv` | Bugs affecting runtime correctness | Reliability |
| `5_maintainability_codesmells.csv` | Code smells with technical debt estimate | Maintainability |
| `6_all_issues.csv` | All issue types combined in one file | All categories |

The script asks you four questions when it runs — no configuration files, no environment variables, no editing required.

---

## Requirements

- Python 3.6 or higher
- `pip3` (Python package manager)
- Network access to your SonarQube instance
- A valid SonarQube user token (`sqp_...`)

Check your Python version:

```bash
python3 --version
```

You need `3.6` or above. If you see `command not found`, install Python first:

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install python3 python3-pip -y

# macOS (using Homebrew)
brew install python3
```

---

## Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/secretguard/sonarqube-report.git
cd sonarqube-report
```

### Step 2 — Install the required library

```bash
pip3 install requests
```

If your system blocks pip without a flag, use:

```bash
pip3 install requests --break-system-packages
```

Verify it installed:

```bash
pip3 show requests
```

You should see the requests package version and location.

### Step 3 — Confirm the script is present

```bash
ls -la sonar_report.py
```

You should see the file listed. If not, check you are in the correct directory with `pwd`.

---

## Getting Your Token

The script requires a **SonarQube User Token** to authenticate with the API. Follow these steps exactly.

### Step 1 — Log in to SonarQube

Open your browser and go to your SonarQube URL, for example:

```
http://localhost:9000
```

Log in with your username and password.

### Step 2 — Go to My Account

Click your **profile avatar or initial** in the top right corner of the page, then click **My Account**.

### Step 3 — Open the Security tab

On the My Account page, click the **Security** tab. You will see a section called **Generate Tokens**.

### Step 4 — Fill in the token form

| Field | What to enter |
|---|---|
| Name | Any label, e.g. `export-token` or `lab-token` |
| Type | Select **User Token** |
| Expires in | Select **No expiration** for lab use, or set a date for production |

### Step 5 — Click Generate

A new token starting with `sqp_` will appear in a highlighted box immediately below the form.

### Step 6 — Copy it immediately

```
sqp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**This is the only time the token value is shown.** If you navigate away or refresh the page, it is gone and you will need to revoke it and generate a new one. Save it somewhere safe before continuing.

---

### Token Types Explained

SonarQube offers three token types. Choose the right one for your purpose:

| Token Type | What It Can Do | Use This For |
|---|---|---|
| **User Token** | Access all projects your account can see, call any API endpoint | This script, report export, API exploration |
| **Project Analysis Token** | Submit scan results for one specific project only | Running `sonar-scanner` on a single project in CI/CD |
| **Global Analysis Token** | Submit scan results for any project on the server | Running `sonar-scanner` across multiple projects in CI/CD |

For this script, always use a **User Token**.

---

### How to Revoke and Generate a New Token

If you lose your token or need to reset it:

1. Go to **My Account → Security**
2. Find the token name in the list
3. Click **Revoke** next to it — the token disappears from the list
4. Scroll up to the **Generate Tokens** form
5. Fill in the name and type again and click **Generate**
6. Copy the new `sqp_` token immediately

Revoking and generating are two separate actions. Revoking does not create a new token automatically.

---

## Running the Script

### Basic run

```bash
python3 sonar_report.py
```

### What the script asks you

The script will prompt you for four inputs. Press **Enter** to accept the default shown in brackets, or type a new value and press Enter.

```
SonarQube URL  [http://localhost:9000]:
Project Key    [dvwa-php-scan]:
Token (sqp_...):
Output folder  [sonar-export]:
```

**SonarQube URL**
The full URL of your SonarQube server including port. Do not include a trailing slash.
Example: `http://localhost:9000`

**Project Key**
The unique identifier of your project in SonarQube. You can find it on the project dashboard URL:
```
http://localhost:9000/dashboard?id=YOUR-PROJECT-KEY
                                     ^^^^^^^^^^^^^^^^
```
Or go to your project → bottom left corner → shows the project key.

**Token**
Paste your `sqp_` token here. The characters will appear as you type — this is normal, the token is not hidden.

**Output folder**
The folder where all CSV files will be saved. It will be created automatically if it does not exist. Defaults to `sonar-export` inside whichever directory you run the script from.

---

### Finding Your Project Key

If you are unsure of your project key:

**Method 1 — From the browser URL**

Open your project in SonarQube. Look at the browser address bar:
```
http://localhost:9000/dashboard?id=dvwa-php-scan
```
The value after `id=` is your project key.

**Method 2 — From the SonarQube API**

```bash
curl -u YOUR_TOKEN: "http://localhost:9000/api/projects/search"
```

This returns a list of all projects and their keys in JSON format.

---

## Understanding the Output

After the script runs successfully, your output folder will contain six CSV files. Here is what each column means.

### 1_project_summary.csv

Overall health metrics for the project.

| Column | Description |
|---|---|
| Metric | Name of the measurement |
| Value | The measured value or rating (A/B/C/D/E) |

Key metrics to look at: Security Rating, Reliability Rating, Maintainability Rating, Vulnerabilities, Security Hotspots, Bugs.

---

### 2_vulnerabilities.csv

Every security vulnerability SonarQube confirmed with high confidence.

| Column | Description |
|---|---|
| Severity | BLOCKER / CRITICAL / HIGH / MEDIUM / LOW |
| Rule | SonarQube rule ID e.g. `php:S5542` |
| File | Source file where the issue is located |
| Line | Line number in the file |
| Message | Human-readable description of the issue |
| Status | OPEN / CONFIRMED / REOPENED |
| Effort | Estimated time to fix e.g. `20min` |
| Debt | Technical debt contribution |
| Author | Developer who introduced the issue (requires SCM) |
| Tags | Associated tags e.g. `cwe`, `owasp-top10` |

---

### 3_security_hotspots.csv

Code patterns that require a human security review before a risk rating can be assigned.

| Column | Description |
|---|---|
| Risk Level | HIGH / MEDIUM / LOW |
| Category | Security category e.g. `sql-injection`, `cryptography` |
| File | Source file |
| Line | Line number |
| Message | Description of the sensitive pattern |
| Status | TO_REVIEW / REVIEWED |
| Resolution | Not reviewed / Safe / Acknowledged / Fixed |
| Author | Developer who wrote the code |

> **Important:** Hotspots are not confirmed vulnerabilities. Each one requires manual review. Mark as Safe if the code is intentional and secure in context, or Acknowledged if a real risk exists that is being tracked.

---

### 4_reliability_bugs.csv

Issues that will or might cause incorrect runtime behaviour.

| Column | Description |
|---|---|
| Severity | BLOCKER / CRITICAL / HIGH / MEDIUM / LOW |
| Rule | Rule ID that flagged the issue |
| File | Source file |
| Line | Line number |
| Message | Description of the bug |
| Status | Current state |
| Effort | Estimated fix time |
| Author | Developer (requires SCM) |

---

### 5_maintainability_codesmells.csv

Issues that do not directly cause security problems but make code harder to maintain and review safely.

| Column | Description |
|---|---|
| Severity | Severity rating |
| Rule | Rule ID |
| File | Source file |
| Line | Line number |
| Message | Description |
| Status | Current state |
| Effort | Estimated fix time |
| Tech Debt | Debt contribution in minutes |

> For security assessments, code smells are lower priority than vulnerabilities and bugs. They belong in a developer backlog rather than a security risk register.

---

### 6_all_issues.csv

All issue types in a single file. Useful for filtering and sorting in Excel or Google Sheets.

| Column | Description |
|---|---|
| Type | VULNERABILITY / BUG / CODE_SMELL / SECURITY_HOTSPOT |
| Severity | Issue severity |
| Rule | Rule ID |
| File | Source file |
| Line | Line number |
| Message | Description |
| Status | Current state |
| Effort | Fix time estimate |
| Debt | Technical debt |
| Author | Developer (requires SCM) |
| Tags | Associated tags |

---

## Example Session

```
=======================================================
  SonarQube Full Export Tool
=======================================================

SonarQube URL [http://localhost:9000]:
Project Key [dvwa-php-scan]:
Token (sqp_...): sqp_745545a302c224ce9749dd36a57736805afeb61f
Output folder [sonar-export]:

Connecting to: http://localhost:9000
Project:       dvwa-php-scan

Authentication OK

[1/6] Fetching project metrics...
  Saved: sonar-export/1_project_summary.csv (15 rows)
[2/6] Fetching vulnerabilities...
  Saved: sonar-export/2_vulnerabilities.csv (6 rows)
[3/6] Fetching security hotspots...
  Saved: sonar-export/3_security_hotspots.csv (87 rows)
[4/6] Fetching reliability issues (bugs)...
  Saved: sonar-export/4_reliability_bugs.csv (386 rows)
[5/6] Fetching maintainability issues (code smells)...
  Saved: sonar-export/5_maintainability_codesmells.csv (2700 rows)
[6/6] Fetching all issues combined...
  Saved: sonar-export/6_all_issues.csv (3092 rows)

=======================================================
  Export Complete
=======================================================
  Output folder : sonar-export/
  Project       : dvwa-php-scan

  Files generated:
  1_project_summary.csv            - Overall metrics
  2_vulnerabilities.csv            - 6 vulnerabilities
  3_security_hotspots.csv          - 87 hotspots
  4_reliability_bugs.csv           - 386 bugs
  5_maintainability_codesmells.csv - 2700 code smells
  6_all_issues.csv                 - 3092 total issues

  Security Rating     : E
  Reliability Rating  : C
  Maintainability     : A
  Vulnerabilities     : 6
  Hotspots            : 87
  Bugs                : 386
  Code Smells         : 2700
=======================================================
```

---

## Troubleshooting

### Authentication failed

```
ERROR: Authentication failed. Check your token.
```

**Cause:** The token is invalid, expired, or was typed incorrectly.

**Fix:**
- Generate a new User Token from My Account → Security
- Make sure you are using a `sqp_` token, not a `sqb_` token
- Check there are no extra spaces when pasting the token

---

### Connection refused or timeout

```
requests.exceptions.ConnectionError
```

**Cause:** The script cannot reach the SonarQube server.

**Fix:**
- Check the URL is correct including the port: `http://localhost:9000`
- Confirm SonarQube is running: `systemctl status sonar` on the server
- Check you are on the same network as the SonarQube server
- If using a hostname, try the IP address instead

---

### JSONDecodeError

```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1
```

**Cause:** The API returned an empty or HTML response instead of JSON.

**Fix:**
Test the API directly with curl:

```bash
curl -u YOUR_TOKEN: "http://localhost:9000/api/authentication/validate"
```

Expected response:
```json
{"valid":true}
```

If you get an HTML page, the URL is wrong or SonarQube is returning an error page.

---

### Project not found

```
Warning: API returned 404
```

**Cause:** The project key does not exist on the server.

**Fix:**
- Double-check the project key from the SonarQube dashboard URL
- Keys are case-sensitive: `dvwa-php-scan` is different from `DVWA-PHP-Scan`
- List all available projects:

```bash
curl -u YOUR_TOKEN: "http://localhost:9000/api/projects/search"
```

---

### pip3 not found

```
Command 'pip3' not found
```

**Fix:**

```bash
# Ubuntu / Debian
sudo apt install python3-pip -y

# Then install requests
pip3 install requests --break-system-packages
```

---

### Empty CSV files

The script ran but CSV files have headers only and no data rows.

**Cause:** The project has been created in SonarQube but no scan has been run yet, or all issues are in a resolved state.

**Fix:**
- Run a sonar-scanner scan on the project first
- In the SonarQube UI, check Issues tab and confirm issues exist with status OPEN

---

## Tested With

| Component | Version |
|---|---|
| SonarQube Community Edition | 10.7.0 |
| Python | 3.10 |
| requests library | 2.31.0 |
| Operating System | Ubuntu 22.04 LTS |

---

## Use Case

Designed for:

- **Security professionals** who need SonarQube findings in CSV for risk registers and audit documentation
- **Developers** who want to review findings in Excel or Google Sheets
- **Trainers** demonstrating SAST output during application security courses
- **Teams** building reporting pipelines who need raw data from SonarQube Community Edition (which has no built-in export)

This script was built during a 15-day Application Security Testing training programme covering SAST, DAST, and vulnerability management using SonarQube, OWASP ZAP, and Nessus.

---

## Related Tools

- [SonarQube](https://www.sonarqube.org/) — Static Application Security Testing platform
- [OWASP ZAP](https://www.zaproxy.org/) — Dynamic Application Security Testing
- [Nessus](https://www.tenable.com/products/nessus) — Infrastructure vulnerability scanning
- [DVWA](https://dvwa.co.uk/) — Damn Vulnerable Web Application (scan target used in testing)

---

## License

MIT License — free to use, modify, and distribute with attribution.

---

*Built during Application Security Testing — SAST & DAST Training | 15-Day Intensive Programme*
