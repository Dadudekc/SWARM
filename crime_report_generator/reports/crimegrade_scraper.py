import time
from typing import Dict, Any
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


def fetch_crimegrade_data(zip_code: str, headless: bool = True) -> Dict[str, Any]:
    """
    Scrape CrimeGrade.org for the given ZIP code.
    Returns a dict with safety grade, crime rates, and summary stats.
    """
    url = f"https://crimegrade.org/safest-places-in-{zip_code}/"
    options = uc.ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(30)
    data = {"zip_code": zip_code, "source": "CrimeGrade.org"}
    
    try:
        driver.get(url)
        time.sleep(3)  # Wait for JS to render

        # Extract safety grade
        try:
            grade_elem = driver.find_element(By.CSS_SELECTOR, 'div.grade-letter')
            data["safety_grade"] = grade_elem.text.strip()
        except NoSuchElementException:
            data["safety_grade"] = None

        # Extract crime rate per 1,000
        try:
            rate_elem = driver.find_element(By.XPATH, "//*[contains(text(),'crime rate per 1,000 residents')]")
            rate_text = rate_elem.text
            data["crime_rate_per_1000"] = rate_text.split()[0]
        except NoSuchElementException:
            data["crime_rate_per_1000"] = None

        # Extract detailed stats
        stats = {}
        try:
            # Wait for stats blocks to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.stats-block'))
            )
            
            stat_blocks = driver.find_elements(By.CSS_SELECTOR, 'div.stats-block')
            for block in stat_blocks:
                try:
                    label = block.find_element(By.CSS_SELECTOR, 'div.stats-label').text.strip()
                    value = block.find_element(By.CSS_SELECTOR, 'div.stats-value').text.strip()
                    stats[label] = value
                except Exception:
                    continue
        except Exception:
            pass
        data["summary_stats"] = stats

        # Extract neighborhood safety scores
        neighborhoods = []
        try:
            neighborhood_blocks = driver.find_elements(By.CSS_SELECTOR, 'div.neighborhood-block')
            for block in neighborhood_blocks:
                try:
                    name = block.find_element(By.CSS_SELECTOR, 'div.neighborhood-name').text.strip()
                    grade = block.find_element(By.CSS_SELECTOR, 'div.neighborhood-grade').text.strip()
                    neighborhoods.append({
                        "name": name,
                        "grade": grade
                    })
                except Exception:
                    continue
        except Exception:
            pass
        data["neighborhoods"] = neighborhoods

        # Extract crime type breakdown
        crime_types = {}
        try:
            crime_blocks = driver.find_elements(By.CSS_SELECTOR, 'div.crime-type-block')
            for block in crime_blocks:
                try:
                    crime_type = block.find_element(By.CSS_SELECTOR, 'div.crime-type').text.strip()
                    rate = block.find_element(By.CSS_SELECTOR, 'div.crime-rate').text.strip()
                    crime_types[crime_type] = rate
                except Exception:
                    continue
        except Exception:
            pass
        data["crime_types"] = crime_types

    except TimeoutException:
        data["error"] = "Timeout loading CrimeGrade.org page."
    except Exception as e:
        data["error"] = str(e)
    finally:
        driver.quit()
    
    return data 