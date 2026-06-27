#incorrect
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import time
import traceback
import os

web = 'https://ingres.iith.ac.in/gecdataonline/misview;locname=INDIA;loctype=COUNTRY;locuuid=ffce9de-24e1-494b-ba7e-0931d8ad6085;component=recharge;period=annual;stateuuid=ffce9de-24e1-494b-ba7e-0931d8ad6085;category=all;year=2024-2025;view=admin;computationType=normal'

# --- Create a directory for reports ---
download_dir = os.path.join(os.getcwd(), "reports")
if not os.path.exists(download_dir):
    os.makedirs(download_dir)
print(f"Reports will be downloaded to: {download_dir}")

# --- Setup Chrome options for custom download path ---
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
  "download.default_directory": download_dir,
  "download.prompt_for_download": False,
  "download.directory_upgrade": True,
  "safebrowsing.enabled": True
})

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

driver.get(web)
driver.maximize_window()

print("Waiting for page to fully load...")
wait = WebDriverWait(driver, 60)
wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
print("✅ Page is fully loaded.")

def click_download_button(driver):
    try:
        time.sleep(4)
        wait = WebDriverWait(driver, 40)
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "ngx-overlay")))
        button = wait.until(EC.element_to_be_clickable((By.NAME, "download")))
        driver.execute_script("arguments[0].click();", button)
        print("⚡ Download button clicked with JavaScript.")
    except Exception as e:
        print(f"❌ Could not click download button: {e}")

click_download_button(driver)
print("Modal should be open now.")

try:
    time.sleep(4)
    wait = WebDriverWait(driver, 30)
    
    modal_locator = (By.TAG_NAME, "ngb-modal-window")
    print("Waiting for the report modal to appear...")
    wait.until(EC.visibility_of_element_located(modal_locator))
    print("✅ Report modal is visible.")

    # --- Locators ---
    year_dropdown_locator = (By.XPATH, "//label[contains(text(), 'Assessment Year')]/following-sibling::select")
    state_dropdown_box_locator = (By.XPATH, "//label[contains(text(), 'State')]/following-sibling::ng-multiselect-dropdown")
    state_options_locator = (By.XPATH, "//div[@class='dropdown-list']/ul[2]/li")
    district_dropdown_locator = (By.XPATH, "//label[contains(text(), 'District')]/following-sibling::ng-multiselect-dropdown")
    # district_select_all_locator = (By.XPATH, "//div[@class='dropdown-list']//div[text()='Select All']")
    # district_select_all_locator = (By.XPATH, "//div[@class='dropdown-list']/ul[1]/li[1]")
    generate_report_locator = (By.XPATH, "//button[contains(., 'GENERATE REPORT')]")
    overlay_locator = (By.CLASS_NAME, "ngx-overlay")

    print("Waiting for the 'Assessment Year' dropdown to be present...")
    year_select_element = wait.until(EC.presence_of_element_located(year_dropdown_locator))
    
    target_year = "2016-2017"
    print(f"\n--- Processing a single year: {target_year} ---")
    
    print(f"  -> Selecting year {target_year} using a more forceful JavaScript event.")
    js_script = f"""
    arguments[0].value = '{target_year}'; 
    arguments[0].dispatchEvent(new Event('input'));
    arguments[0].dispatchEvent(new Event('change'));
    """
    driver.execute_script(js_script, year_select_element)
    time.sleep(1)

    wait.until(EC.invisibility_of_element_located(overlay_locator))
    
    state_dropdown_box = wait.until(EC.presence_of_element_located(state_dropdown_box_locator))
    actions = ActionChains(driver)
    actions.move_to_element(state_dropdown_box).click().perform()
    
    wait.until(EC.visibility_of_element_located(state_options_locator))
    state_elements = driver.find_elements(*state_options_locator)
    state_names = [state.text for state in state_elements if state.text]
    print(f"  -> Found {len(state_names)} states for year {target_year}.")

    actions.move_to_element(state_dropdown_box).click().perform()

    for state in state_names:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"\n  - Processing State: {state} (Attempt {attempt + 1}/{max_retries})")
                
                state_dropdown_box = wait.until(EC.presence_of_element_located(state_dropdown_box_locator))
                actions = ActionChains(driver)
                actions.move_to_element(state_dropdown_box).click().perform()
                
                state_to_click = wait.until(EC.element_to_be_clickable((By.XPATH, f"//li/div[text()='{state}']")))
                state_to_click.click()
                print(f"    -> Selected state: {state}")
                
                actions.move_to_element(state_dropdown_box).click().perform()
                
                time.sleep(2)
                print("    -> Waiting for district data to load...")
                wait.until(EC.invisibility_of_element_located(overlay_locator))
                
                print("    -> Waiting for District dropdown to be clickable...")
                district_box = wait.until(EC.element_to_be_clickable(district_dropdown_locator))
                
                actions = ActionChains(driver)
                actions.move_to_element(district_box).click().perform()
                print("    -> Opened District dropdown.")
                
                # time.sleep(1)
                # --- MORE ROBUST WAIT FOR "SELECT ALL" ---
                print("    -> Waiting for 'Select All' to be visible...")
                # wait.until(EC.visibility_of_element_located(district_select_all_locator))
                select_all_districts = wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[1]/li[1]/div[text()='Select All']")))
                select_all_districts.click()
                
                # actions = ActionChains(driver)
                actions.move_to_element(select_all_districts).click().perform()
                print("    -> Selected 'Select All' for districts.")
                
                actions = ActionChains(driver)
                actions.move_to_element(district_box).click().perform()
                wait.until(EC.invisibility_of_element_located(overlay_locator))

                # --- Generate Report ---
                files_before = set(os.listdir(download_dir))
                generate_button = wait.until(EC.element_to_be_clickable(generate_report_locator))
                driver.execute_script("arguments[0].click();", generate_button)
                print("    -> ✅ Report generation started...")

                downloaded_filename = None
                for _ in range(30): 
                    files_after = set(os.listdir(download_dir))
                    new_files = files_after - files_before
                    if new_files:
                        for filename in new_files:
                            if not filename.endswith('.crdownload'):
                                downloaded_filename = filename
                                break
                    if downloaded_filename:
                        break
                    time.sleep(1)

                if downloaded_filename:
                    safe_state_name = state.replace(' ', '_').replace('&', 'and')
                    new_filename = f"CentralReport_{safe_state_name}_{target_year}.xlsx"
                    old_filepath = os.path.join(download_dir, downloaded_filename)
                    new_filepath = os.path.join(download_dir, new_filename)
                    
                    time.sleep(1)
                    os.rename(old_filepath, new_filepath)
                    print(f"    -> 📂 File renamed to: {new_filename}")
                else:
                    raise Exception("Download timed out or file not found.")

                # --- DESELECT THE STATE TO PREPARE FOR THE NEXT ONE ---
                print(f"    -> Deselecting state: {state} to prepare for next iteration.")
                state_dropdown_box = wait.until(EC.presence_of_element_located(state_dropdown_box_locator))
                actions = ActionChains(driver)
                actions.move_to_element(state_dropdown_box).click().perform()
                state_to_deselect = wait.until(EC.element_to_be_clickable((By.XPATH, f"//li/div[text()='{state}']")))
                state_to_deselect.click()
                actions.move_to_element(state_dropdown_box).click().perform()

                break 
            
            except Exception as inner_e:
                print(f"    -> ❌ Error on attempt {attempt + 1} for state {state}.")
                if attempt < max_retries - 1:
                    print(f"    -> Retrying... Error: {inner_e}")
                    time.sleep(2)
                else:
                    print(f"    -> ❌ Max retries reached for {state}. Skipping. Final Error: {inner_e}")

except Exception:
    print(f"❌ An error occurred during processing:")
    traceback.print_exc()

finally:
    print("\nScript finished. Closing browser.")
    driver.quit()

