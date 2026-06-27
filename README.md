# INGRES Groundwater Data Scraper

> **Automated extraction of India's Dynamic Groundwater Resource datasets from the [IN-GRES Portal](https://ingres.iith.ac.in)** — purpose-built as the data-collection backbone for a future AI/RAG Chatbot for policymakers and researchers.

---

## Table of Contents

- [Background and Motivation](#background-and-motivation)
- [What is IN-GRES](#what-is-in-gres)
- [Project Overview](#project-overview)
- [Repository Structure](#repository-structure)
- [How the Scraper Works](#how-the-scraper-works)
- [Key Engineering Challenges and Solutions](#key-engineering-challenges-and-solutions)
- [Scraped Data Output](#scraped-data-output)
- [Installation and Setup](#installation-and-setup)
- [Usage](#usage)
- [Script Versioning and Evolution](#script-versioning-and-evolution)
- [Future Roadmap](#future-roadmap)
- [Disclaimer](#disclaimer)

---

## Background and Motivation

India faces a severe groundwater depletion crisis. Groundwater accounts for approximately:
- **62%** of all irrigation water
- **85%** of rural drinking water supply

Government agencies and water policymakers must periodically assess the state of these resources across **thousands of blocks, mandals, districts, and states** — a process that is currently locked behind a complex, dynamic web portal with no bulk-download API.

Manually navigating the portal to download one file per state × per year × per granularity level would require **hundreds of hours** of tedious, error-prone clicking. This project automates that entire process.

The resulting datasets are intended to serve as the **data layer for an INGRES AI Chatbot**, which is being prototyped by IIT-Hyderabad to help researchers and non-technical government users query groundwater statistics in natural language.

---

## What is IN-GRES

**IN-GRES** (India Groundwater Resource Estimation System) is a GIS-based web application developed collaboratively by:
- **CGWB** — Central Ground Water Board
- **IIT-H** — Indian Institute of Technology, Hyderabad

It provides a Pan-India platform for assessing *Dynamic Ground Water Resources* using the **GEC-2015 methodology**, offering data at multiple administrative granularities:

| Level | Description |
|---|---|
| Country | All-India aggregate |
| State / UT | 28 States + 8 Union Territories |
| District | All districts within a State |
| Block / Mandal / Taluk | Sub-district assessment units |

### Safety Categorization (Stage of Extraction)

| Category | Extraction Level | Meaning |
|---|---|---|
| **Safe** | Less than 70% | Sustainable use |
| **Semi-Critical** | 70% to 90% | Approaching stress |
| **Critical** | 90% to 100% | High-stress zone |
| **Over-Exploited** | Greater than 100% | Extraction exceeds recharge |

Key metrics tracked per region:
- Annual Ground Water Recharge
- Total Extractable Resources
- Total Ground Water Extraction (Irrigation / Domestic / Industry)

---

## Project Overview

This repository contains **two families of Selenium automation scripts** that systematically scrape every state's groundwater reports for every available assessment year:

| Script Family | Report Type | Granularity |
|---|---|---|
| `central_scripts/` | Central / National View | State-level summary per State |
| `state_scripts/` | State-level View | Block / Mandal / Sub-district level |

Scripts are versioned (e.g., `_final`, `_final1`, `_final4`) representing iterative engineering improvements as new edge cases were discovered on the live portal.

---

## Repository Structure

```
INGRES Scrapper/
|
|-- central_scripts/              # Scripts to scrape Central (State-summary) reports
|   |-- central_final.py          # v1 - initial working version
|   |-- central_final1.py         # v2 - improved year selection
|   |-- central_final2.py         # v3 - JS force-click integration
|   |-- central_final3.py         # v4 - retry loop added
|   |-- central_final4.py         # v5 [RECOMMENDED] - final, most stable version
|   |-- central_district.py       # District-level report scraper v1
|   |-- central_district1.py      # District-level report scraper v2
|   +-- central_district2.py      # District-level report scraper v3 [RECOMMENDED]
|
|-- state_scripts/                # Scripts to scrape State-level Block/Mandal reports
|   |-- state_block.py            # v1 - initial version
|   |-- state_block1.py           # v2 - dropdown handling improved
|   |-- state_block2.py           # v3 - Block/Mandal dynamic detection
|   |-- state_block3.py           # v4 - island/region edge case handling
|   +-- state_block4.py           # v5 [RECOMMENDED] - final, most stable version
|
|-- test_scripts/                 # Early exploratory and prototype scripts
|   |-- ingres_assessYr1.py       # Tests assessment year dropdown
|   |-- ingres_btnclk.py          # Tests modal open/close via download button
|   |-- ingres_state1.py          # Tests state selection
|   |-- ingres_state2.py          # Tests state + top-view selection
|   +-- test.py                   # Minimal smoke test
|
|-- Central_TvState_2012-2013/    # Scraped Data: Central view, FY 2012-13
|-- Central_TvState_2016-2017/    # Scraped Data: Central view, FY 2016-17
|-- Central_district_2016-2017/   # Scraped Data: District view, FY 2016-17
|
|-- requirements.txt              # Python package dependencies
+-- README.md                     # This file
```

> Scripts labeled **[RECOMMENDED]** are the production-ready, final versions to use.

---

## How the Scraper Works

The scraper automates the following workflow — repeated for **every state × every available assessment year**:

```
Open INGRES Portal
        |
        v
Click Download Button  <--- On Failure: Retry up to 3 times
        |
        v
Wait for Report Modal to Appear
        |
        v
Select Assessment Year (via JavaScript dispatch)
        |
        v
Select State from multi-select dropdown
        |
        v
Select Top View (Block / Mandal / District / State)
        |
        v
Select All Districts -> Select All Sub-divisions
        |
        v
Click GENERATE REPORT
        |
        v
Monitor download folder for new .xlsx file
        |
        v
Rename: {ReportType}Report_{STATE}_{YEAR}.xlsx
        |
        v
Next State -> (loop continues)
```

---

## Key Engineering Challenges and Solutions

### 1. Conquering the Loading Overlay (ngx-overlay)

**Problem:** The Angular-based portal fires a blocking loading screen after *every* interaction.
Standard Selenium clicks on blocked elements raise `ElementNotInteractableException`.

**Solution:** Every action is followed by an explicit wait that pauses the script until the overlay disappears:

```python
wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "ngx-overlay")))
```

The script *never* proceeds until the portal confirms it has fully processed the previous command.

---

### 2. JavaScript Force-Click (Bypassing UI Intercepts)

**Problem:** The portal's Angular framework intercepts standard Selenium `.click()` and `Select()`
calls at the DOM level, causing silent failures.

**Solution:** JavaScript injection bypasses the UI layer entirely and dispatches Angular-compatible events.

Force a click:
```python
driver.execute_script("arguments[0].click();", element)
```

Force a dropdown value and trigger Angular change detection:
```python
driver.execute_script(
    "arguments[0].value = arguments[1];"
    "arguments[0].dispatchEvent(new Event('input'));"
    "arguments[0].dispatchEvent(new Event('change'));",
    year_select_element, "2016-2017"
)
```

---

### 3. Smart File Renaming (Contextual File Management)

**Problem:** Every downloaded file gets a generic, meaningless name like `stateReport1757869210024.xlsx`.

**Solution:** The script monitors the download directory, detects new `.xlsx` files the moment they appear
(excluding `.crdownload` temp files), and renames them with full context.

Output example: `StateReport_ANDHRA_PRADESH_2016-2017.xlsx`

---

### 4. Dynamic Block vs Mandal Detection

**Problem:** Some states use "BLOCK" as their sub-district unit, others use "MANDAL"
(e.g., Telangana, Andhra Pradesh). A rigid script would crash when the expected label is absent.

**Solution:** The script reads the "Top view" dropdown options at runtime and adapts accordingly:

```python
top_view_options = [o.text for o in Select(top_view_element).options]
if "BLOCK" in top_view_options:
    sub_division_label = "Block"
elif "MANDAL" in top_view_options:
    sub_division_label = "Mandal"
```

All subsequent XPaths are dynamically constructed using the detected label, making the script self-adapting.

---

### 5. Start Fresh Retry Loop (Fault Tolerance)

**Problem:** If a network glitch or UI desync causes a failure midway, the script's internal state
diverges from the portal's displayed state, causing cascading failures.

**Solution:** Each state is wrapped in a try/except with up to **3 retry attempts**. On failure, the
modal is closed and fully re-opened to guarantee a clean slate:

```python
for attempt in range(max_retries):  # max_retries = 3
    try:
        # ... full extraction logic for one state ...
        break  # success - exit retry loop
    except Exception as e:
        # Close and fully reopen the modal before retrying
        driver.find_element(By.XPATH, "//button[@aria-label='Close']").click()
        click_download_button(driver)
```

---

### 6. Island and Region Edge Cases

**Problem:** States like Andaman and Nicobar Islands have a unique "Island" sub-selection level
that standard states do not have.

**Solution:** The script detects an `is_island_case` boolean flag and conditionally handles the
Island dropdown only when applicable, silently skipping it for all other states via try/except blocks.

---

## Scraped Data Output

Files are saved in the format:
```
{ReportType}Report_{STATE_NAME}_{ASSESSMENT_YEAR}.xlsx
```

### Currently Available Datasets

| Folder | Report Type | Year | States Covered |
|---|---|---|---|
| `Central_TvState_2012-2013/` | Central (State View) | 2012-13 | 29 States/UTs |
| `Central_TvState_2016-2017/` | Central (State View) | 2016-17 | 37 States/UTs |
| `Central_district_2016-2017/` | Central (District View) | 2016-17 | 35 States/UTs |

Each `.xlsx` file contains groundwater resource data for all assessment units within that state
for the given fiscal year, including:
- Annual recharge volumes (BCM)
- Total extractable groundwater resources
- Actual extraction volumes by sector (irrigation, domestic, industry)
- Stage of extraction (%) and safety category for each block/mandal

---

## Installation and Setup

### Prerequisites

- Python **3.9+**
- Google Chrome browser (latest stable)
- ChromeDriver — **auto-installed** by `webdriver-manager`; no manual setup needed

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/ingres-scrapper.git
cd "INGRES Scrapper"
```

### Step 2: Create a Virtual Environment

```bash
python -m venv my_env

# Windows
my_env\Scripts\activate

# macOS / Linux
source my_env/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Key Dependencies

| Package | Version | Purpose |
|---|---|---|
| `selenium` | 4.35.0 | Browser automation core |
| `webdriver-manager` | 4.0.2 | Auto ChromeDriver management |
| `pandas` | 2.3.2 | Data processing (future pipeline) |
| `python-dotenv` | 1.1.1 | Environment variable management |
| `requests` | 2.32.5 | HTTP utilities |

---

## Usage

> **Always run the recommended final versions.** Earlier versions are preserved for development history only.

### Scrape Central (State-Summary) Reports

```bash
python central_scripts/central_final4.py
```

### Scrape State-Level (Block/Mandal) Reports

```bash
python state_scripts/state_block4.py
```

### Scrape District-Level Reports

```bash
python central_scripts/central_district2.py
```

### Changing the Target Year

Open the chosen script and update the `target_year` variable near the top:

```python
target_year = "2022-2023"  # Change to your desired assessment year
```

Available assessment years on the portal range from **2012-2013** to **2024-2025**.

### Expected Console Output

```
Reports will be downloaded to: C:\...\INGRES Scrapper\reports
Waiting for page to fully load...
Page is fully loaded.
Download button clicked with JavaScript.

--- Processing year: 2016-2017 ---
  -> Found 37 states.

  - Processing State: ANDHRA PRADESH (Attempt 1/3)
  -> Selected BLOCK from Top view.
  -> Selected all districts.
  -> Selected all Blocks.
  -> Report generation started...
  -> File renamed to: StateReport_ANDHRA_PRADESH_2016-2017.xlsx

Script finished. Closing browser.
```

---

## Script Versioning and Evolution

| Version | Scripts | Key Addition |
|---|---|---|
| v1 | central_final.py, state_block.py | Basic state loop and file download |
| v2 | central_final1.py, state_block1.py | Improved year selection via JS dispatch |
| v3 | central_final2.py, state_block2.py | Full JS force-click; Block/Mandal dynamic detection |
| v4 | central_final3.py, state_block3.py | 3-attempt retry loop; Island edge case handling |
| v5 (RECOMMENDED) | central_final4.py, state_block4.py | Start-fresh modal reset on retry; Region dropdown support |

---

## Future Roadmap

This scraper is **Phase 1** of a larger initiative. The collected Excel files are designed to feed
into a Retrieval-Augmented Generation (RAG) chatbot:

```
User Question (Natural Language)
         |
         v
   INGRES AI Chatbot
         |
   ______|________________________
   |            |                |
   v            v                v
Vector Store  LLM Engine     Data Layer
(Embeddings) (Gemini/GPT-4)  (.xlsx files
                               from Phase 1)
```

**Example questions the chatbot will answer:**
- "Which districts in Rajasthan were Over-Exploited in 2022-23?"
- "Compare groundwater recharge in Punjab from 2012 to 2022."
- "List all Safe blocks in Karnataka for the latest assessment year."
- "What is the total extraction for Telangana mandals in 2020-21?"

**Development Phases:**

- [x] **Phase 1 (Complete):** Automated data scraping — this repository
- [ ] **Phase 2:** Data preprocessing — normalize all .xlsx files into a unified schema
- [ ] **Phase 3:** Vector embedding pipeline — chunk, embed, and store in a vector database (ChromaDB / Pinecone)
- [ ] **Phase 4:** RAG chatbot — LangChain + Gemini / GPT-4 integration
- [ ] **Phase 5:** Web UI — policymaker-friendly natural language chat interface

---

## Disclaimer

This tool is developed for **academic and policy research purposes only**. All data is publicly
accessible through the official INGRES portal operated by CGWB and IIT-Hyderabad. This scraper
does not bypass any authentication mechanisms or access any non-public data. Users are responsible
for complying with the portal's terms of service and applicable data usage policies.

---

Built with Python and Selenium — For India's Groundwater Future

*Developed as a data pipeline for the INGRES AI Chatbot initiative — IIT-Hyderabad*
