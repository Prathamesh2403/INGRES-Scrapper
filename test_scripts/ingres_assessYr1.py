from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

web = 'https://ingres.iith.ac.in/gecdataonline/misview;locname=INDIA;loctype=COUNTRY;locuuid=ffce954d-24e1-494b-ba7e-0931d8ad6085;component=recharge;period=annual;stateuuid=ffce954d-24e1-494b-ba7e-0931d8ad6085;category=all;year=2024-2025;view=admin;computationType=normal'

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

driver.get(web)
driver.maximize_window()

def click_download_button(driver):
    try:
        wait = WebDriverWait(driver, 40)
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "ngx-overlay")))
        
        button = wait.until(
            EC.presence_of_element_located((By.NAME, "download"))
        )
        
        try:
            wait.until(EC.element_to_be_clickable((By.NAME, "download")))
            button.click()
            print("✅ Button clicked normally")
        except:
            driver.execute_script("arguments[0].click();", button)
            print("⚡ Button clicked with JavaScript (fallback)")
            
    except Exception as e:
        print("❌ Could not click button:", e)

click_download_button(driver)
print("Modal should be open now.")

try:
    wait = WebDriverWait(driver, 20)
    year_dropdown_locator = (By.XPATH, "//label[contains(text(), 'Assessment Year')]/following-sibling::select")

    print("Waiting for the 'Assessment Year' dropdown...")
    year_select_element = wait.until(EC.presence_of_element_located(year_dropdown_locator))
    print("🔎 Found the 'Assessment Year' dropdown.")
    
    select_object = Select(year_select_element)
    
    all_years = [option.get_attribute('value') for option in select_object.options]
    print(f"🗓️ Years to process: {all_years}")

    for year in all_years:
        year_select_element = wait.until(EC.presence_of_element_located(year_dropdown_locator))
        select_object = Select(year_select_element)

        print(f"\n- Selecting year: {year}")
        select_object.select_by_value(year)
        
        time.sleep(2) 
    
    print("\n✅ Successfully looped through all available years.")

except Exception as e:
    print(f"❌ An error occurred while processing the years: {e}")

finally:
    print("Closing browser in 5 seconds...")
    time.sleep(5)
    driver.quit()