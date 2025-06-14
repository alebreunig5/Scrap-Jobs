import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
from datetime import datetime
import re
from urllib.parse import urljoin

# --- Selenium Imports ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# --- Configuration Constants ---
OUTPUT_FILE = 'ScrapJobs.xlsx'
# HISTORY_FILE is no longer needed, it will be managed within OUTPUT_FILE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

SITE_CONFIGS = {
    "https://jobs.iqvia.com/en/search-jobs/Argentina/24443/2/3865483/-34/-64/50/2": {
        "company_name": "IQVIA", #FILTRA DE MAS
        "job_listing_selector": "li",
        "title_selector": "h2.job-result-list-heading",
        "link_selector": "a.job-result-list",
        "location_selector": "span.job-location",
        "pagination": {
            "type": "url",
            "url_pattern": "https://jobs.iqvia.com/en/search-jobs/Argentina/24443/{page_num}/3865483/-34/-64/50/2",
            "start_page": 1,
            "max_pages": 15
        }
    },
    "https://careers.iconplc.com/jobs?options=1329&page=1": { 
        "company_name": "ICON plc 2", #Cambie el pagination manualmente
        "job_listing_selector": "div.attrax-vacancy-tile",
        "title_selector": "a.attrax-vacancy-tile__title", 
        "link_selector": "a.attrax-vacancy-tile__title", 
        "location_selector": "div.attrax-vacancy-tile__location-freetext p.attrax-vacancy-tile__item-value",
        "pagination": {
            "type": "url",
            "url_pattern": "https://careers.iconplc.com/jobs?options=1329&page={page_num}",
            "start_page": 1,
            "max_pages": 10
        }
    },
    "https://jobs.parexel.com/en/search-jobs?glat=-34.60049819946289&glon=-58.37409973144531": {
        "company_name": "Parexel",  #FILTRA DE MAS
        "job_listing_selector": "ul#search-results-jobs > li",
        "title_selector": "li > a > h2",
        "link_selector": "li > a",
        "location_selector": "li > a > span.job-location.location-test",
        "pagination": {
            "type": "click",
            "next_page_selector": "button.pagination-view-more[data-view-more-list='search-results-jobs']",
            "max_pages": 15
        }
    },
    "https://jobs.thermofisher.com/global/en/search-results?m=3&location=Remote%2C%20Argentina": {
        "company_name": "Thermo Fisher Scientific", 
        "job_listing_selector": "li.jobs-list-item", 
        "title_selector": "a[data-ph-at-id='job-link'] span", 
        "link_selector": "a[data-ph-at-id='job-link']", 
        "location_selector": None, 
        "pagination": {
            "type": "url", # Cambiado a paginación por URL
            "url_pattern": "https://jobs.thermofisher.com/global/en/search-results?m=3&location=Remote%2C%20Argentina&from={offset_val}&s=1", # **CORREGIDO**: Patrón de URL con offset
            "start_page": 1, # Página inicial (conceptual)
            "max_pages": 15, # Número máximo de páginas
            "offset_step": 10 # Número de elementos a saltar por "página"
        }
    },
    "https://iqvia.wd1.myworkdayjobs.com/en-US/IQVIA?locations=8a3f99567bc501f02cab6b679a01a0c3": {
        "company_name": "IQVIA WorkDay",  #PERFECTO
        "job_listing_selector": "li.css-1q2dra3",
        "title_selector": "a[data-automation-id='jobTitle']",
        "link_selector": "a[data-automation-id='jobTitle']",
        "location_selector": "div[data-automation-id='locations'] dd.css-129m7dg",
        "pagination": {
            "type": "click",
            "next_page_selector": "button[data-uxi-element-id='next']",
            "max_pages": 15
        }
    },
    "https://careers.medpace.com/jobs?keywords=&page=1&sortBy=relevance&country=Argentina": {
        "company_name": "Medpace",   #FUNCIONA PERFECTO
        "job_listing_selector": "mat-expansion-panel.search-result-item",
        "title_selector": "a.job-title-link span[itemprop='title']",
        "link_selector": "a.job-title-link",
        "location_selector": "p.label-container span.label-value.location",
        "pagination": {
            "type": "url",
            "url_pattern": "https://careers.medpace.com/jobs?page={page_num}&sortBy=relevance&locations=Ciudad%20Autonoma%20de%20Buenos%20Aires,,Argentina&location=Argentina&stretch=10&stretchUnit=MILES",
            "start_page": 1,
            "max_pages": 15
        }
    },
    "https://careers.cognizant.com/global-en/jobs/?page=1&location=Argentina&radius=20&cname=Argentina&ccode=AR&pagesize=10#results": {
        "company_name": "Cognizant",    #FUNCIONA PERFECTO
        "job_listing_selector": "div.card.card-job",
        "title_selector": "h2.card-title a.js-view-job",
        "link_selector": "h2.card-title a.js-view-job",
        "location_selector": "ul.list-inline.job-meta li.list-inline-item:first-child",
        "pagination": {
            "type": "url",
            "url_pattern": "https://careers.cognizant.com/global-en/jobs/?page={page_num}&location=Argentina&radius=20&cname=Argentina&ccode=AR&pagesize=10#results",
            "start_page": 1,
            "max_pages": 15
        }
    },
    "https://www.syneoshealth.com/careers/search/jobs/in/buenos-aires-remote": {
        "company_name": "Syneos Health",     #FUNCIONA PERFECTO
        "job_listing_selector": "div.jobs-section__item",
        "title_selector": "div.small-12.large-5.columns h2 a",
        "link_selector": "div.small-12.large-5.columns h2 a",
        "location_selector": "div.small-12.large-4.columns",
        "pagination": {
            "type": "url",
            "url_pattern": "https://www.syneoshealth.com/careers/search/jobs/in/buenos-aires-remote?page={page_num}",
            "start_page": 1,
            "max_pages": 15
        }
    },
    "https://psi-cro.com/careers-breakout/?_sfm_location_country=Argentina": {
        "company_name": "PSI CRO", 
        "job_listing_selector": "article.ecs-post-loop", 
        "title_selector": "h3.elementor-heading-title a", 
        "link_selector": "h3.elementor-heading-title a", 
        "location_selector": "section.elementor-inner-section p.elementor-heading-title",
        "pagination": {
            "type": "url", 
            "url_pattern": "https://psi-cro.com/careers-breakout/?_sfm_location_country=Argentina&sf_paged={page_num}", 
            "start_page": 1, 
            "max_pages": 15 
        }
    },
    "https://fortrea.wd1.myworkdayjobs.com/en-US/Fortrea?locationCountry=e42ad5eac46d4cc9b367ceaef42577c5": {
        "company_name": "Fortrea WorkDay",   #FUNCIONA PERFECTO
        "job_listing_selector": "li.css-1q2dra3",
        "title_selector": "a[data-automation-id='jobTitle']",
        "link_selector": "a[data-automation-id='jobTitle']",
        "location_selector": "div[data-automation-id='locations'] dd.css-129m7dg",
        "pagination": {
            "type": "click",
            "next_page_selector": "button[data-uxi-element-id='next']",
            "max_pages": 15
        }
    },
    "https://recruiting.paylocity.com/recruiting/jobs/All/47c330a1-c2ce-4151-8a72-e5bb2bf9454d/SerenaGroup-Inc?location=Remote%20Worker%20-%20N%2FA&department=All%20Departments": {
        "company_name": "SerenaGroup",
        "job_listing_selector": "div.row.job-listing-job-item",
        "title_selector": "span.job-item-title a", 
        "link_selector": "span.job-item-title a", 
        "location_selector": "div.col-xs-4.location-column span.job-item-normal"
    },
}

# --- Helper Functions ---

def clean_text(text):
    """
    Limpia el texto reemplazando múltiples espacios con un solo espacio
    y eliminando los espacios en blanco iniciales/finales.
    Asegura que la entrada sea tratada como una cadena.
    Args:
        text (str): La cadena de entrada a limpiar.
    Returns:
        str: La cadena limpia.
    """
    if pd.isna(text): # Verifica si es un valor NaN de pandas
        return ''
    text_str = str(text) # Convierte explícitamente a cadena
    if text_str:
        return re.sub(r'\s+', ' ', text_str).strip()
    return ''

def get_full_url(base_url, relative_url):
    """
    Combina una URL base con una URL relativa para crear una URL completa.
    Args:
        base_url (str): La URL base (ej. la página principal del sitio web).
        relative_url (str): La ruta relativa a la oferta de empleo.
    Returns:
        str: La URL completa.
    """
    return urljoin(base_url, relative_url)

def generate_job_id(company, position, link):
    """
    Genera un ID único para una oferta de empleo basado en la empresa, el puesto y el enlace.
    Esto ayuda a identificar ofertas de empleo duplicadas en diferentes ejecuciones del rastreador.
    Args:
        company (str): El nombre de la empresa.
        position (str): El puesto/título de la oferta.
        link (str): El enlace directo a la oferta de empleo.
    Returns:
        str: Un ID de empleo único.
    """
    # Asegúrate de que las entradas sean cadenas antes de limpiar
    clean_company = clean_text(company)
    clean_position = clean_text(position)
    full_link = get_full_url('', clean_text(link)) # clean_text también en el link antes de urljoin

    return f"{clean_company}::{clean_position}::{full_link}"

# --- Main Scraping Function ---

def scrape_jobs():
    all_new_jobs = []
    # Al inicio, carga los IDs de los trabajos existentes desde el archivo Excel
    existing_job_ids = set()
    
    # Definir las columnas principales que el script siempre espera y gestiona
    primary_columns = ['Empresa', 'Puesto', 'Link de Aplicación', 'Ubicacion', 'Fecha de Registro']

    if os.path.exists(OUTPUT_FILE):
        try:
            # Lee el archivo Excel sin especificar 'job_id' para obtener todas las columnas existentes
            existing_df = pd.read_excel(OUTPUT_FILE)
            print(f"Cargado el archivo Excel existente con {len(existing_df)} registros.")

            # Asegúrate de que las columnas principales estén presentes
            for col in primary_columns:
                if col not in existing_df.columns:
                    existing_df[col] = '' # Añade la columna si falta, con valores vacíos

            # Genera job_ids para los datos existentes si aún no están presentes
            if 'job_id' not in existing_df.columns:
                # Usa solo las columnas necesarias para generar el job_id
                existing_df['job_id'] = existing_df.apply(
                    lambda row: generate_job_id(
                        row.get('Empresa', ''), 
                        row.get('Puesto', ''), 
                        row.get('Link de Aplicación', '')
                    ), axis=1
                )
                print(f"Generada la columna 'job_id' para {len(existing_df[existing_df['job_id'].notna()])} registros existentes sin ella.")
            
            existing_job_ids = set(existing_df['job_id'].dropna().tolist())
            print(f"Cargados {len(existing_job_ids)} IDs de trabajos existentes del archivo Excel.")
            
        except Exception as e:
            print(f"Error al cargar o procesar el archivo Excel existente: {e}. Se comenzará con un historial vacío.")
            # global_existing_df ya no es necesario aquí, se gestiona en save_to_excel

    driver = None
    try:
        service = ChromeService(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
        driver = webdriver.Chrome(service=service, options=options)
        print("Chrome WebDriver iniciado en modo headless.")
    except Exception as e:
        print(f"Error al iniciar Chrome WebDriver: {e}. No se puede continuar con el scraping.")
        return [], existing_job_ids # Devuelve una lista vacía y los IDs cargados para que no se pierdan

    for base_url, config in SITE_CONFIGS.items():
        print(f"\nScraping: Empresa: {config['company_name']}")

        pagination_config = config.get("pagination")

        current_iteration = 1
        max_iterations = 1
        consecutive_empty_pages = 0

        if pagination_config:
            if pagination_config["type"] == "url":
                current_iteration = pagination_config.get("start_page", 1)
                max_iterations = pagination_config.get("max_pages", 1)
            elif pagination_config["type"] == "click":
                max_iterations = pagination_config.get("max_pages", 1)
            elif pagination_config["type"] == "scroll":
                max_iterations = pagination_config.get("max_scrolls", 1)

                print(f"  Navegando a la URL base para paginación por scroll: {base_url}")
                driver.get(base_url)
                time.sleep(random.uniform(3, 6))


        while current_iteration <= max_iterations:
            url_to_scrape = base_url

            if pagination_config and pagination_config["type"] == "url":
                if "offset_step" in pagination_config:
                    offset = (current_iteration - 1) * pagination_config["offset_step"]
                    url_to_scrape = pagination_config["url_pattern"].format(offset_val=offset)
                    print(f"  Navegando a la página {current_iteration} (offset {offset}) de {config['company_name']}")
                else:
                    url_to_scrape = pagination_config["url_pattern"].format(page_num=current_iteration)
                    print(f"  Navegando a la página {current_iteration} de {config['company_name']}")
                
                driver.get(url_to_scrape)
                time.sleep(random.uniform(2, 4))

            elif pagination_config and pagination_config["type"] == "click" and current_iteration > 1:
                print(f"  Procesando página {current_iteration} de {config['company_name']} (después de hacer clic en 'Siguiente').")

            elif pagination_config and pagination_config["type"] == "scroll" and current_iteration > 1:
                print(f"  Realizando scroll #{current_iteration-1} para {config['company_name']}")

                old_scroll_height = driver.execute_script("return document.body.scrollHeight;")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(pagination_config.get("scroll_delay", 3))

                new_scroll_height = driver.execute_script("return document.body.scrollHeight;")
                if new_scroll_height <= old_scroll_height:
                    print("  No se cargó contenido nuevo después del scroll. Asumiendo fin de resultados o página.")
                    break

            elif not pagination_config or (pagination_config["type"] != "url" and current_iteration == 1):
                print(f"  Navegando a la página 1 de {config['company_name']} (URL: {base_url})")
                driver.get(base_url)
                time.sleep(random.uniform(2, 4))

            try:
                # Lógica específica para ICON plc (si usa iframe)
                # NOTA: Asegúrate de que "ICON plc" en SITE_CONFIGS es el nombre exacto de la empresa para la que aplica el iframe
                if config["company_name"] == "ICON plc (Original)":
                    print(f"  Detectada {config['company_name']}, intentando cambiar a iframe...")
                    iframe_selector = "#icims_content_iframe"
                    try:
                        iframe_element = WebDriverWait(driver, 60).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, iframe_selector))
                        )
                        driver.switch_to.frame(iframe_element)
                        print(f"  Cambiado a contexto de iframe para {config['company_name']}.")
                    except (TimeoutException, NoSuchElementException) as e:
                        print(f"  Error al encontrar o cambiar a iframe '{iframe_selector}' para {config['company_name']}: {e}. Saltando sitio.")
                        driver.switch_to.default_content()
                        break
                    except Exception as e:
                        print(f"  Ocurrió un error inesperado con el iframe para {config['company_name']}: {e}. Saltando sitio.")
                        driver.switch_to.default_content()
                        break

                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, config["job_listing_selector"]))
                )

                response_html = driver.page_source
                soup = BeautifulSoup(response_html, 'html.parser')

                job_listings = soup.select(config["job_listing_selector"])

                if not job_listings:
                    print(f"  Advertencia: No se encontraron elementos con el selector '{config['job_listing_selector']}' en {url_to_scrape} (Iteración {current_iteration}).")
                    consecutive_empty_pages += 1
                    if consecutive_empty_pages >= 2: # Si dos páginas consecutivas están vacías, salimos
                        print(f"  Dos páginas consecutivas sin resultados para {config['company_name']}. Deteniendo la paginación.")
                        break
                    # Si solo una página está vacía, intentamos la siguiente por si es un error temporal o si hay paginación no lineal
                    current_iteration += 1 # Incrementar incluso si no hay job_listings para intentar la siguiente página/clic
                    time.sleep(random.uniform(2, 4)) # Pequeño delay antes de la siguiente iteración
                    continue # Salta al siguiente bucle while

                found_count_page = 0
                for job_element in job_listings:
                    title_tag = job_element.select_one(config["title_selector"])
                    link_tag = job_element.select_one(config["link_selector"])
                    
                    # Manejo de la ubicación (manteniendo la lógica existente para None y casos específicos)
                    location = 'Location Not Found'
                    if config["company_name"] == "Thermo Fisher Scientific" and link_tag and 'data-ph-at-job-location-text' in link_tag.attrs:
                        location = clean_text(link_tag['data-ph-at-job-location-text'])
                    elif config["company_name"] in ["IQVIA WorkDay", "Fortrea WorkDay", "SerenaGroup", "Medpace", "Cognizant", "Syneos Health"] and config.get("location_selector"):
                        location_tag = job_element.select_one(config["location_selector"])
                        location = clean_text(location_tag.get_text()) if location_tag else 'Location Not Found'
                    elif config["company_name"] == "PSI CRO" and config.get("location_selector"):
                        location_parts = job_element.select(config["location_selector"])
                        if location_parts:
                            location = clean_text("".join([p.get_text() for p in location_parts]))
                        else:
                            location = 'Location Not Found'
                    elif config.get("location_selector"): # Para otros sitios que tienen un selector de ubicación directo
                        location_tag = job_element.select_one(config["location_selector"])
                        location = clean_text(location_tag.get_text()) if location_tag else 'Location Not Found'
                    else: # Caso por defecto si no hay selector de ubicación o es None
                        location = 'Location Not Found'
                        
                    title = clean_text(title_tag.get_text()) if title_tag else 'Title Not Found'
                    
                    # Manejo especial para el enlace de SerenaGroup (Paylocity)
                    if config["company_name"] == "SerenaGroup" and link_tag and 'href' in link_tag.attrs:
                        # Extraer la parte base de la URL para Paylocity para formar enlaces absolutos correctos
                        paylocity_base_url_match = re.match(r'(https?://recruiting\.paylocity\.com/recruiting/jobs/All/[^/]+/[^/]+)/?', base_url)
                        if paylocity_base_url_match:
                            paylocity_base = paylocity_base_url_match.group(1)
                            link = get_full_url(paylocity_base, link_tag['href'])
                        else: # Si no coincide, intentar con la base original
                            link = get_full_url(base_url, link_tag['href'])
                    else:
                        link = get_full_url(base_url, link_tag['href']) if link_tag and 'href' in link_tag.attrs else 'Link Not Found'

                    job_id = generate_job_id(config["company_name"], title, link)

                    if job_id not in existing_job_ids:
                        all_new_jobs.append({
                            'Empresa': config["company_name"],
                            'Puesto': title,
                            'Link de Aplicación': link,
                            'Ubicacion': location,
                            'Fecha de Registro': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'job_id': job_id
                        })
                        found_count_page += 1
                        existing_job_ids.add(job_id)

                print(f"  Se encontraron {found_count_page} TRABAJOS NUEVOS en la iteración {current_iteration}.")

                # Resetear el contador de páginas vacías si se encontraron trabajos
                if found_count_page > 0:
                    consecutive_empty_pages = 0

                if pagination_config and pagination_config["type"] == "click":
                    next_button = None
                    try:
                        next_button = WebDriverWait(driver, 60).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, pagination_config["next_page_selector"]))
                        )
                        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                        driver.execute_script("arguments[0].click();", next_button) # Clic con JavaScript
                        time.sleep(random.uniform(3, 7))
                        current_iteration += 1
                    except (TimeoutException, NoSuchElementException) as e:
                        print(f"  No se pudo encontrar o hacer clic en el botón 'Siguiente' en la iteración {current_iteration}: {e}. Asumiendo que no hay más páginas.")
                        break
                    except Exception as e:
                        print(f"  Ocurrió un error inesperado al hacer clic en 'Siguiente' en la iteración {current_iteration}: {e}. Deteniendo el scraping para este sitio.")
                        break

                elif pagination_config and pagination_config["type"] == "url":
                    current_iteration += 1

                elif pagination_config and pagination_config["type"] == "scroll":
                    current_iteration += 1

                else:
                    break

            except TimeoutException as e:
                print(f"  Tiempo de espera agotado para el elemento en {url_to_scrape} (Iteración {current_iteration}): {e}. Saltando sitio.")
                break
            except WebDriverException as e:
                print(f"  Error de WebDriver en {url_to_scrape} (Iteración {current_iteration}): {e}. Saltando sitio.")
                break
            except Exception as e:
                print(f"  Ocurrió un error inesperado al procesar {url_to_scrape} (Iteración {current_iteration}): {e}. Saltando sitio.")
                break

            finally:
                if config["company_name"] == "ICON plc (Original)": # Asegúrate de usar el nombre exacto
                    try:
                        driver.switch_to.default_content()
                        print(f"  Volviendo al contenido principal para {config['company_name']}.")
                    except Exception as e:
                        print(f"  Error al intentar volver al contenido predeterminado: {e}")

            time.sleep(random.uniform(2, 6))

    if driver:
        driver.quit()
        print("Chrome WebDriver cerrado.")

    return all_new_jobs, existing_job_ids

# --- Data Saving Functions ---

def save_to_excel(df_new_jobs_current_run, all_seen_job_ids_from_run):
    """
    Guarda las nuevas ofertas de empleo en un archivo Excel, agregándolas a los datos existentes
    y asegurando que no se añadan duplicados y se mantengan las columnas adicionales y formatos.
    Args:
        df_new_jobs_current_run (pd.DataFrame): DataFrame que contiene los nuevos trabajos encontrados en la ejecución actual.
        all_seen_job_ids_from_run (set): Conjunto de todos los IDs de trabajo vistos (ejecución actual + historial).
    """
    
    # Columnas que el script gestiona y debe escribir para los nuevos registros
    script_managed_columns = ['Empresa', 'Puesto', 'Link de Aplicación', 'Ubicacion', 'Fecha de Registro', 'job_id']
    
    # 1. Cargar el DataFrame existente completo
    if os.path.exists(OUTPUT_FILE):
        try:
            # Cargar todas las columnas existentes para preservar cualquier columna personalizada
            existing_df_from_excel = pd.read_excel(OUTPUT_FILE, sheet_name='Ofertas de Empleo')
            print(f"Cargado el archivo Excel existente con {len(existing_df_from_excel)} registros.")

            # Asegúrate de que 'job_id' exista en el DataFrame existente para la deduplicación
            if 'job_id' not in existing_df_from_excel.columns:
                existing_df_from_excel['job_id'] = existing_df_from_excel.apply(
                    lambda row: generate_job_id(
                        row.get('Empresa', ''), 
                        row.get('Puesto', ''), 
                        row.get('Link de Aplicación', '')
                    ), axis=1
                )
                print("Se generaron 'job_id' para registros existentes sin ellos.")
            
            existing_excel_job_ids = set(existing_df_from_excel['job_id'].dropna().tolist())

        except Exception as e:
            print(f"Error al cargar el archivo Excel existente: {e}. Se tratará como un archivo nuevo.")
            existing_df_from_excel = pd.DataFrame() # DataFrame vacío si hay error al cargar
            existing_excel_job_ids = set()
    else:
        existing_df_from_excel = pd.DataFrame() # Si no existe, empezar con un DataFrame vacío
        existing_excel_job_ids = set()
        print("Creando un nuevo archivo Excel.")

    # 2. Filtrar los nuevos trabajos para añadir solo los que no están ya en el Excel
    # Asegúrate de que df_new_jobs_current_run tenga la columna 'job_id'
    if not df_new_jobs_current_run.empty and 'job_id' not in df_new_jobs_current_run.columns:
        df_new_jobs_current_run['job_id'] = df_new_jobs_current_run.apply(
            lambda row: generate_job_id(
                row.get('Empresa', ''), 
                row.get('Puesto', ''), 
                row.get('Link de Aplicación', '')
            ), axis=1
        )
    
    # Filtrar los trabajos que ya están en el Excel (usando job_id)
    jobs_to_add_to_excel = df_new_jobs_current_run[~df_new_jobs_current_run['job_id'].isin(existing_excel_job_ids)]

    if not jobs_to_add_to_excel.empty:
        print(f"Se agregaron {len(jobs_to_add_to_excel)} nuevos trabajos al archivo Excel.")
        
        # Asegurarse de que `jobs_to_add_to_excel` tenga todas las columnas del `existing_df_from_excel`
        # para una concatenación limpia.
        all_cols_in_excel = existing_df_from_excel.columns.tolist() if not existing_df_from_excel.empty else []
        for col in jobs_to_add_to_excel.columns:
            if col not in all_cols_in_excel:
                all_cols_in_excel.append(col) # Añade las columnas nuevas si existen en jobs_to_add_to_excel

        # Asegurarse de que `jobs_to_add_to_excel` tenga las columnas de `existing_df_from_excel` (con NaN si no tienen valor)
        for col in all_cols_in_excel:
            if col not in jobs_to_add_to_excel.columns:
                jobs_to_add_to_excel[col] = pd.NA # Añade columnas faltantes con valores nulos

        # Concatenar el DataFrame existente con los nuevos trabajos
        # `jobs_to_add_to_excel` debe tener las mismas columnas que `existing_df_from_excel` para evitar problemas
        final_df_for_excel = pd.concat([existing_df_from_excel, jobs_to_add_to_excel[all_cols_in_excel]], ignore_index=True)
    else:
        final_df_for_excel = existing_df_from_excel
        print("No hay nuevos trabajos para agregar al archivo Excel (ya están presentes o no se encontraron nuevos).")

    # Guardar el DataFrame en Excel, ahora incluyendo la columna 'job_id'
    output_df = final_df_for_excel # Ya no se elimina la columna 'job_id' aquí.

    writer = pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl')
    # Usar sheet_name='Ofertas de Empleo' para asegurar que siempre se escribe en la misma hoja
    output_df.to_excel(writer, index=False, sheet_name='Ofertas de Empleo') 
    writer.close()
    print(f"Hoja de cálculo de trabajos actualizada en '{OUTPUT_FILE}'.")


# --- Main Execution Block ---

if __name__ == "__main__":
    print("--- Iniciando búsqueda de trabajos ---")
    
    new_jobs_list, updated_job_ids_set = scrape_jobs()

    df_new_jobs = pd.DataFrame(new_jobs_list)

    if not df_new_jobs.empty:
        print("\n--- Vista previa de NUEVOS Trabajos Encontrados ---")
        columns_to_show = ['Empresa', 'Puesto', 'Ubicacion', 'Fecha de Registro']
        print(df_new_jobs[columns_to_show].head())
        
    # Llama a save_to_excel con los nuevos trabajos encontrados y el conjunto de todos los IDs vistos
    # La función save_to_excel ahora es responsable de cargar lo existente, filtrar y concatenar.
    save_to_excel(df_new_jobs, updated_job_ids_set)
    
    print("--- Búsqueda de trabajos finalizada ---")

