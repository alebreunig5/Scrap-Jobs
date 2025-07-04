# Job Scraper
This repository contains a Python script designed to scrape job listings from various company career pages, primarily focusing on roles in Argentina. It uses BeautifulSoup for static HTML parsing and Selenium for dynamic content loading and interaction, ensuring comprehensive data collection.

## Features
Multi-Site Scraping: Configurable to scrape job postings from multiple career websites.
Dynamic Content Support: Utilizes Selenium to handle JavaScript-rendered content and pagination (click-based, URL-based, and scroll-based).
Duplicate Job Detection: Prevents adding duplicate job entries using a unique job_id generated from company, position, and link.
Excel Output: Saves all scraped and new job data into a single Excel file, preserving existing custom columns.
Robust Error Handling: Includes error handling for common scraping issues like timeouts and element not found exceptions.
Headless Browse: Runs Chrome browser in headless mode for efficient, background scraping.

## Requirements
To run this script, you'll need the following:

### Python Libraries
You can install these using pip:
```python 
pip install requests beautifulsoup4 pandas openpyxl selenium webdriver-manager
```

### Here's a breakdown of what each library is used for:

requests: For making HTTP requests to fetch web page content (though primarily Selenium is used for most sites due to dynamic content).
bs4 (BeautifulSoup): For parsing HTML and XML documents, making it easy to extract data.
pandas: For data manipulation and analysis, specifically for handling DataFrames and reading/writing Excel files.
openpyxl: A dependency for pandas to read and write .xlsx Excel files.
selenium: An automation tool used to control a web browser. Essential for scraping sites that load content dynamically with JavaScript or require user interaction (like clicking "next page" buttons).
webdriver_manager: Automatically downloads and manages the appropriate ChromeDriver binary for Selenium, simplifying setup.

### Other Requirements
Google Chrome Browser: Selenium requires a Chrome installation on your system to operate.

## Installation
### Clone the repository:
```python 
git clone https://github.com/your-username/JobScraper.git
cd JobScraper
```

### Install the Python dependencies:
```python 
pip install -r requirements.txt
```
(You'll need to create a requirements.txt file if you haven't already. After installing all libraries, you can run pip freeze > requirements.txt in your terminal to generate it.)

## Project Structure
The project has a flat structure for simplicity.

```python
JobScraper/
├── ScrapJobs.py
└── ScrapJobs.xlsx (generated after first run)
```
ScrapJobs.py: The main Python script containing all the scraping logic.
ScrapJobs.xlsx: The Excel file where scraped job data will be stored. This file is created automatically if it doesn't exist, and updated on subsequent runs.

## How it Works
The script operates in the following stages:

### 1. Initialization:

Loads existing job data from ScrapJobs.xlsx (if it exists) into a pandas DataFrame. This data includes a job_id for each entry, which is used to prevent adding duplicates. If the job_id column is missing from an existing Excel file, it's generated for the loaded data.
Initializes a headless Chrome WebDriver using selenium and webdriver_manager. This means the browser runs in the background without a visible UI.

### 2. Site Iteration:
It iterates through each base_url and its config defined in the SITE_CONFIGS dictionary.

### 3. Pagination Handling:
URL-based pagination: For sites like IQVIA, Medpace, Cognizant, Syneos Health, and PSI CRO, the script constructs the next page URL based on a defined url_pattern and increments the page_num or offset_val.
Click-based pagination: For sites like Parexel, IQVIA WorkDay, and Fortrea WorkDay, the script identifies and clicks a "next page" button using a CSS selector. It waits for the button to be clickable and uses JavaScript to click it.
Scroll-based pagination: Currently, the provided configuration does not explicitly use scroll-based pagination as a primary mechanism, but the framework for it ("type": "scroll") is present, indicating future expandability.

### 4. Content Extraction:
After navigating to a page, Selenium fetches the page_source (the full HTML content after dynamic loading).
BeautifulSoup then parses this HTML.
It identifies individual job listings using the job_listing_selector specified in the site's configuration.
For each job listing, it extracts the job title, application link, and location using their respective CSS selectors.
Special handling is implemented for specific sites (e.g., Thermo Fisher Scientific, SerenaGroup, PSI CRO) to correctly extract location or construct absolute links.

### 5. Duplicate Detection:
A unique job_id is generated for each scraped job using a combination of the company name, job title, and application link.
This job_id is compared against a set of existing_job_ids (loaded from the Excel file at the start) to ensure that only truly new jobs are added.

### 6. Data Storage:
New jobs (those not found in existing_job_ids) are appended to a list all_new_jobs.
After all sites have been scraped, all_new_jobs is converted into a pandas DataFrame.
The save_to_excel function is called:
It re-loads the entire existing Excel file to preserve any manual additions or formatting.
It filters df_new_jobs to only include entries not already present in the existing Excel data (again, using job_id).
The new, unique jobs are then concatenated with the existing DataFrame.
The combined DataFrame is saved back to ScrapJobs.xlsx on the Ofertas de Empleo sheet, overwriting the previous content but maintaining all columns.

### 7. Error Handling and Delays:
try-except blocks are used to catch TimeoutException, NoSuchElementException, and generic WebDriverException errors, allowing the script to skip problematic sites or pages without crashing.
time.sleep(random.uniform(x, y)) calls are strategically placed to introduce random delays between requests, mimicking human behavior and reducing the likelihood of being blocked by websites.

## Configuration
The SITE_CONFIGS dictionary is the core of the scraper's configuration. Each key represents a base URL for a company's career page, and its value is a dictionary defining how to scrape that site:

company_name (str): The name of the company.
job_listing_selector (str): CSS selector for a single job listing element (e.g., li, div.job-card).
title_selector (str): CSS selector for the job title within a job listing.
link_selector (str): CSS selector for the link to the job details page within a job listing.
location_selector (str, optional): CSS selector for the job location. If None, the script might use alternative logic or default to 'Location Not Found'.
pagination (dict, optional): Configuration for handling multiple pages of results.
type (str): Can be "url", "click", or "scroll".
url_pattern (str, for "url" type): A template string for constructing paginated URLs (e.g., "https://example.com/jobs?page={page_num}"). Can also include {offset_val} for offset-based pagination.
start_page (int, for "url" type): The starting page number for URL pagination.
max_pages (int): The maximum number of pages or iterations to scrape for a given site.
next_page_selector (str, for "click" type): CSS selector for the "next page" button.
offset_step (int, for "url" type with offset): The number of items to skip per "page" for offset-based pagination.
scroll_delay (int, for "scroll" type): Delay in seconds after each scroll.

## Output
The scraped data is saved to ScrapJobs.xlsx in the root directory. The Excel file will contain the following columns:

Empresa: The name of the company.
Puesto: The title of the job position.
Link de Aplicación: The direct URL to apply for the job.
Ubicacion: The reported location of the job.
Fecha de Registro: The date and time when the job was first recorded by the script.
job_id: A unique identifier for the job, used internally for deduplication.
If you add additional columns manually to ScrapJobs.xlsx (e.g., "Notes", "Status"), the script will preserve these columns and their data when it updates the file, as long as you don't modify the existing Empresa, Puesto, or Link de Aplicación for those rows.
