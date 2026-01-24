# 🌍 Dynamic Country EPG Generator

A high-performance, automated EPG (Electronic Program Guide) fetcher powered by **WebGrab+Plus** and **GitHub Actions**. This repository generates XMLTV files for specific countries on-demand via external API calls or via a daily schedule.

## 🚀 Key Features
* **Dynamic Scraping:** Responds to external `repository_dispatch` requests for any country code.
* **Internet Bypass:** Pre-configured to defeat the "No Internet !! Cannot run without it" error in GitHub environments.
* **Recursive Scraper Matching:** Automatically finds the correct `.ini` file within the SiteIni subfolders (e.g., Canada, USA, etc.).
* **Daily Updates:** Automatically refreshes at 03:00 UTC daily.

---

## 🛠️ How It Works



1.  **Trigger:** An external script sends a POST request to this repo.
2.  **Config Generation:** `filter_wg_channels.py` scans the `siteini.pack` for verified scrapers and builds a custom `WebGrab++.config.xml`.
3.  **Bypass Execution:** Docker runs WebGrab+Plus using the `skipcheck` flag to bypass the GitHub Runner's network restrictions.
4.  **Storage:** The resulting `{COUNTRY}.xml` file is saved in the `epg_db/` folder and pushed back to the repository.

---

## 📡 Triggering from an External Script

You can trigger this generator from any application using the GitHub API. This allows you to integrate EPG generation into your own playlist managers or servers.

### 1. Requirements
* A **GitHub Personal Access Token (PAT)** with `repo` scope.
* Your **GitHub Username** and **Repository Name**.

### 2. Python Example
```python
import requests

def trigger_epg(country_code):
    USERNAME = "YOUR_USERNAME"
    REPO = "YOUR_REPO_NAME"
    TOKEN = "YOUR_GITHUB_PAT"
    
    url = f"[https://api.github.com/repos/](https://api.github.com/repos/){USERNAME}/{REPO}/dispatches"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    
    data = {
        "event_type": "run_webgrab",
        "client_payload": {
            "country": country_code.upper() # e.g., 'CA', 'US', 'GB'
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 204:
        print(f"✅ Success: EPG generation started for {country_code}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")

# Example: Trigger for Canada
trigger_epg("CA")
