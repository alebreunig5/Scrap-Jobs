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

# Extra
# Step-by-Step Guide to Generating Web Selectors
The goal is to find unique and stable HTML attributes (like class, id, tag names, etc.) that identify the elements you want to extract (job listings, titles, links, locations). We'll primarily use the Chrome Developer Tools, but the process is similar in Firefox or Edge.

## Tools You'll Need
### A Web Browser: Chrome, Firefox, or Edge.

### Developer Tools: Built into your browser (usually accessed by pressing F12 or right-clicking and selecting "Inspect").

## The General Process
### 1. Open the Target Web Page: Navigate to the career page you want to scrape.
### 2. Open Developer Tools: Press F12 (Windows/Linux) or Cmd + Option + I (Mac), or right-click anywhere on the page and select "Inspect" or "Inspect Element."
### 3. Use the Element Inspector Tool: This is the icon that looks like a mouse pointer over a square (often in the top-left of the Developer Tools panel). Click it, then hover over the elements on the web page to highlight them in the DOM (Document Object Model) tree.
### 4. Identify the "Job Listing Container": This is the parent HTML element that encapsulates a single job posting (e.g., a div, li, article). You want a selector that returns all job postings on the page.
### 5. Identify Individual Data Points: Once you have the job listing container, you'll drill down to find the selectors for the job title, application link, and location within that container.
### 6. Test Your Selectors: Use the browser's console or the "Search" feature in the Elements tab to test if your selectors correctly identify the desired elements.

## Breakdown with Examples
```python
<div id="job-listings-container">
    <div class="job-card">
        <h2 class="job-title"><a href="/jobs/senior-dev" data-job-id="12345">Senior Software Developer</a></h2>
        <p class="job-location">Buenos Aires, Argentina</p>
        <span class="job-date">Posted: 2025-07-01</span>
    </div>
    <div class="job-card">
        <h2 class="job-title"><a href="/jobs/junior-analyst" data-job-id="67890">Junior Data Analyst</a></h2>
        <p class="job-location">Remote</p>
        <span class="job-date">Posted: 2025-06-28</span>
    </div>
    </div>
```


## Step 1: Identify the Job Listing Selector (job_listing_selector)
This selector should target the individual containers that hold each job's information.

### 1. Inspect a Job Listing:
Open Developer Tools.
Click the "Select an element in the page to inspect it" tool (the arrow icon).
Hover over one complete job posting on the page. Try to select the largest possible container that only contains one job's details.
Click on it. The corresponding HTML will be highlighted in the "Elements" tab.

### 2. Analyze the HTML: Look for a distinctive class name, ID, or tag.
In our example, each job is within a <div class="job-card">.
A good selector here would be div.job-card or simply .job-card. If there are other div elements with the same class not related to jobs, you might need to be more specific, like div#job-listings-container > div.job-card.

### 3. Test the Selector:
Go to the "Console" tab in Developer Tools.
Type $$('YOUR_SELECTOR_HERE') (for CSS selectors) or $x('YOUR_XPATH_HERE') (for XPath).
For our example: $$('.job-card').
Press Enter.
Check the output. It should return a NodeList or array containing all the job listing elements on the page. If it returns more than you expect, your selector is too broad. If it returns too few, it's too specific or incorrect.
Your job_listing_selector for the example: div.job-card

## Step 2: Identify the Job Title Selector (title_selector)
This selector should target the HTML element containing the job title within a single job listing container.

### 1. Inspect a Job Title:
Still with Developer Tools open, click the "Select an element" tool.
Hover over the job title of one of the postings.
Click on it.

### 2. Analyze the HTML (within the job listing's context):
In our example, the title is inside an <h2> tag with class="job-title", which itself contains an <a> tag.
Good selectors: h2.job-title, .job-title, or if the a tag directly contains the text, h2.job-title a.
Choose the most direct element containing the text. If the title is always within the <a> tag, a might be better.

### 3. Test the Selector:
From the "Elements" tab, right-click on the highlighted job listing container (the one you identified in Step 1).
Select "Copy" -> "Copy selector" (this gives you a full CSS selector from the <html> tag, which is often too specific, but useful for quick testing).
Paste it into the console: $$('body > div#job-listings-container > div.job-card:nth-child(1) > h2.job-title')
More importantly, test your relative selector by mentally applying it within the selected job listing element. Your title_selector in the Python code will be used by job_element.select_one(), meaning it's already scoped to the job_element.
For the example, h2.job-title would be correct for select_one.
Your title_selector for the example: h2.job-title

## Step 3: Identify the Application Link Selector (link_selector)
This selector should target the HTML element whose href attribute contains the URL to the full job description.

### 1. Inspect the Job Link:
Use the "Select an element" tool and click on the job title itself, as the link is often embedded there.

### 2. Analyze the HTML:
In our example, the <a> tag inside the <h2> has the href.
Selector: h2.job-title a or simply a if it's the only link within the job listing that points to the job details. Be specific enough to avoid other links.

### 3. Test the Selector:
$$('h2.job-title a') in the console, but remember this is applied relative to the job_element.
Your link_selector for the example: h2.job-title a

## Step 4: Identify the Location Selector (location_selector)
This selector targets the element containing the job's location.

### 1. Inspect the Location Text:
Use the "Select an element" tool and click on the location text.

### 2. Analyze the HTML:
In our example, the location is within a <p> tag with class="job-location".
Selector: p.job-location or .job-location.

### 3. Test the Selector:
$$('p.job-location') in the console.
Your location_selector for the example: p.job-location

## Step 5: Identify the Next Page Button/Link Selector (next_page_selector for 'click' pagination)
If a site uses "click" pagination, you need a selector for the "Next" button or link.

### 1. Inspect the Pagination Control:
Navigate to a page with a "Next" button or link.
Use the "Select an element" tool and click on the "Next" button/link.

### 2. Analyze the HTML:
Look for distinctive id, class, data- attributes, or even the text content.
Example: <button id="next-page-button">Next</button>, <a class="pagination-link next" href="...">Next »</a>

### 3. Test the Selector:
$$('#next-page-button') or $$('a.pagination-link.next').
Ensure it selects only the "Next" button/link and not other pagination elements.
Your next_page_selector for the example: button#next-page-button or a.pagination-link.next

## Common Selector Types and Best Practices
### CSS Selectors (Recommended for Simplicity)
By Tag Name: div, a, span, li
By Class: .my-class, div.specific-class
By ID: #my-id (IDs should be unique on a page, making them very reliable)
By Attribute: [href], [data-automation-id='jobTitle'], a[target='_blank']
Descendant Selector: div.parent p.child (selects <p class="child"> elements that are descendants of <div class="parent">)
Child Selector: ul > li (selects <li> elements that are direct children of <ul>)
Combinations: div#main-content a.job-link[data-type='full']

## How to Apply This to Your Existing SITE_CONFIGS
Go through each entry in your SITE_CONFIGS dictionary.

### 1. Open the base_url for that company.
### 2. Follow the steps above to identify the job_listing_selector, title_selector, link_selector, and location_selector.
### 3. For pagination:
If type: "url", identify how the page number or offset changes in the URL pattern.
If type: "click", find the next_page_selector for the "Next" button/link.
If type: "scroll", you don't need a specific selector, but you need to confirm that scrolling reveals more content.
By systematically applying these steps for each site, you'll be able to generate robust selectors and fine-tune your existing configurations. It often requires a bit of trial and error, but with practice, you'll become very efficient at it!
