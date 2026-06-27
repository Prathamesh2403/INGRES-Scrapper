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
    wait = WebDriverWait(driver, 30)
    
    modal_locator = (By.TAG_NAME, "ngb-modal-window")
    print("Waiting for the report modal to appear...")
    wait.until(EC.visibility_of_element_located(modal_locator))
    print("✅ Report modal is visible.")

    # --- Locators ---
    state_radio_button_locator = (By.XPATH, "//label[text()='State']/preceding-sibling::input[@type='radio']")
    year_dropdown_locator = (By.XPATH, "//label[contains(text(), 'Assessment Year')]/following-sibling::select")
    state_dropdown_locator = (By.XPATH, "//label[contains(text(), 'State')]/following-sibling::select")
    top_view_locator = (By.XPATH, "//label[contains(text(), 'Top view')]/following-sibling::select")
    district_dropdown_locator = (By.XPATH, "//label[contains(text(), 'District')]/following-sibling::ng-multiselect-dropdown")
    district_select_all_locator = (By.XPATH, "//label[contains(text(), 'District')]/following-sibling::ng-multiselect-dropdown//div[text()='Select All']")
    generate_report_locator = (By.XPATH, "//button[contains(., 'GENERATE REPORT')]")
    overlay_locator = (By.CLASS_NAME, "ngx-overlay")

    # --- 1. Select the "State" report type ---
    print("-> Selecting 'State' report type...")
    state_radio_button = wait.until(EC.presence_of_element_located(state_radio_button_locator))
    driver.execute_script("arguments[0].click();", state_radio_button)
    print("  -> Waiting for form to update for State reports...")
    wait.until(EC.invisibility_of_element_located(overlay_locator))

    time.sleep(4)
    
    # --- 2. Get all available states and their values from the new dropdown ---
    print("-> Getting list of all available states...")
    state_select_element = wait.until(EC.presence_of_element_located(state_dropdown_locator))
    select_state_obj = Select(state_select_element)
    all_state_options = [opt for opt in select_state_obj.options if opt.get_attribute("value")]
    # Create a map of state names to their unique values (UUIDs)
    state_map = {opt.text.strip(): opt.get_attribute("value") for opt in all_state_options}
    state_names = list(state_map.keys())
    print(f"  -> Found {len(state_names)} states to process.")
    
    # Using default year
    year_select_element = driver.find_element(*year_dropdown_locator)
    target_year = "2024-2025"
    print(f"  -> Using default Assessment Year: {target_year}")

    for state in state_names:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"\n--- Processing State: {state} (Attempt {attempt + 1}/{max_retries}) ---")
                
                # --- 3. Select the current state using JAVASCRIPT ---
                state_select_element = wait.until(EC.presence_of_element_located(state_dropdown_locator))
                target_state_value = state_map[state]
                print(f"  -> Selecting state: {state} with JavaScript.")
                js_script = f"""
                arguments[0].value = '{target_state_value}';
                arguments[0].dispatchEvent(new Event('input'));
                arguments[0].dispatchEvent(new Event('change'));
                """
                driver.execute_script(js_script, state_select_element)
                wait.until(EC.invisibility_of_element_located(overlay_locator))

                time.sleep(2)
                
                # --- 4. Select "MANDAL" or "BLOCK" from Top view ---
                top_view_element = wait.until(EC.presence_of_element_located(top_view_locator))
                select_top_view = Select(top_view_element)
                top_view_options = [option.text for option in select_top_view.options]

                sub_division_label = None

                if "MANDAL" in top_view_options:
                    select_top_view.select_by_visible_text("MANDAL")
                    sub_division_label = "Mandal"
                    print(f"  -> Selected 'MANDAL' from Top view.")
                elif "BLOCK" in top_view_options:
                    select_top_view.select_by_visible_text("BLOCK")
                    sub_division_label = "Block"
                    print(f"  -> Selected 'BLOCK' from Top view.")
                else:
                    raise Exception("Could not find 'MANDAL' or 'BLOCK' in Top view options.")
                
                wait.until(EC.invisibility_of_element_located(overlay_locator))

                time.sleep(1)
                
                # --- 5. Select all Districts ---
                district_box = wait.until(EC.presence_of_element_located(district_dropdown_locator))
                driver.execute_script("arguments[0].click();", district_box)
                select_all_districts = wait.until(EC.presence_of_element_located(district_select_all_locator))
                driver.execute_script("arguments[0].click();", select_all_districts)
                driver.execute_script("arguments[0].click();", district_box)
                print("  -> Selected 'Select All' for districts.")
                wait.until(EC.invisibility_of_element_located(overlay_locator))

                time.sleep(1)

                # --- 6. Select all Mandals/Blocks ---
                sub_division_dropdown_locator = (By.XPATH, f"//label[contains(text(), '{sub_division_label}')]/following-sibling::ng-multiselect-dropdown")
                sub_division_select_all_locator = (By.XPATH, f"//label[contains(text(), '{sub_division_label}')]/following-sibling::ng-multiselect-dropdown//div[text()='Select All']")
                
                sub_division_box = wait.until(EC.presence_of_element_located(sub_division_dropdown_locator))
                driver.execute_script("arguments[0].click();", sub_division_box)
                select_all_sub_divisions = wait.until(EC.presence_of_element_located(sub_division_select_all_locator))
                driver.execute_script("arguments[0].click();", select_all_sub_divisions)
                driver.execute_script("arguments[0].click();", sub_division_box)
                print(f"  -> Selected 'Select All' for {sub_division_label}s.")
                wait.until(EC.invisibility_of_element_located(overlay_locator))

                # --- 7. Generate and Rename Report ---
                files_before = set(os.listdir(download_dir))
                generate_button = wait.until(EC.element_to_be_clickable(generate_report_locator))
                driver.execute_script("arguments[0].click();", generate_button)
                print("  -> ✅ Report generation started...")

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
                    new_filename = f"StateReport_{safe_state_name}_{target_year}.xlsx"
                    old_filepath = os.path.join(download_dir, downloaded_filename)
                    new_filepath = os.path.join(download_dir, new_filename)
                    
                    time.sleep(1)
                    os.rename(old_filepath, new_filepath)
                    print(f"  -> 📂 File renamed to: {new_filename}")
                else:
                    raise Exception("Download timed out or file not found.")

                break 
            
            except Exception as inner_e:
                print(f"  -> ❌ Error on attempt {attempt + 1} for state {state}.")
                if attempt < max_retries - 1:
                    print(f"  -> Retrying... Error: {inner_e}")
                    # In case of error, refresh the modal to get a clean slate
                    driver.find_element(By.XPATH, "//button[@aria-label='Close']").click()
                    time.sleep(2)
                    click_download_button(driver)
                    wait.until(EC.visibility_of_element_located(modal_locator))
                    state_radio_button = wait.until(EC.element_to_be_clickable(state_radio_button_locator))
                    driver.execute_script("arguments[0].click();", state_radio_button)
                    wait.until(EC.invisibility_of_element_located(overlay_locator))
                else:
                    print(f"  -> ❌ Max retries reached for {state}. Skipping. Final Error: {inner_e}")

except Exception:
    print(f"❌ An error occurred during the main process:")
    traceback.print_exc()

finally:
    print("\nScript finished. Closing browser.")
    driver.quit()