from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
import time
import traceback

web = 'https://ingres.iith.ac.in/gecdataonline/misview;locname=INDIA;loctype=COUNTRY;locuuid=ffce9de-24e1-494b-ba7e-0931d8ad6085;component=recharge;period=annual;stateuuid=ffce9de-24e1-494b-ba7e-0931d8ad6085;category=all;year=2024-2025;view=admin;computationType=normal'

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

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

    year_dropdown_locator = (By.XPATH, "//label[contains(text(), 'Assessment Year')]/following-sibling::select")
    state_dropdown_box_locator = (By.XPATH, "//label[contains(text(), 'State')]/following-sibling::ng-multiselect-dropdown")
    state_options_locator = (By.XPATH, "//div[@class='dropdown-list']/ul[2]/li")
    top_view_locator = (By.XPATH, "//label[contains(text(), 'Top view')]/following-sibling::select")
    generate_report_locator = (By.XPATH, "//button[contains(., 'GENERATE REPORT')]")
    overlay_locator = (By.CLASS_NAME, "ngx-overlay")

    print("Waiting for the 'Assessment Year' dropdown to be present...")
    year_select_element = wait.until(EC.presence_of_element_located(year_dropdown_locator))
    
    select_obj = Select(year_select_element)
    all_year_values = [opt.get_attribute("value") for opt in select_obj.options]
    print(f"🔎 Found years to process: {all_year_values}")

    for year in all_year_values:
        print(f"\n--- Processing Year: {year} ---")
        
        year_select_element = wait.until(EC.presence_of_element_located(year_dropdown_locator))
        js_script = f"arguments[0].value = '{year}'; arguments[0].dispatchEvent(new Event('change'));"
        driver.execute_script(js_script, year_select_element)
        wait.until(EC.invisibility_of_element_located(overlay_locator))
        
        state_dropdown_box = wait.until(EC.presence_of_element_located(state_dropdown_box_locator))
        actions = ActionChains(driver)
        actions.move_to_element(state_dropdown_box).click().perform()
        
        wait.until(EC.visibility_of_element_located(state_options_locator))
        state_elements = driver.find_elements(*state_options_locator)
        state_names = [state.text for state in state_elements if state.text]
        print(f"  -> Found {len(state_names)} states for year {year}.")

        actions.move_to_element(state_dropdown_box).click().perform()

        for state in state_names:
            try:
                print(f"\n  - Processing State: {state}")
                
                state_dropdown_box = wait.until(EC.presence_of_element_located(state_dropdown_box_locator))
                actions = ActionChains(driver)
                actions.move_to_element(state_dropdown_box).click().perform()
                
                state_to_click = wait.until(EC.element_to_be_clickable((By.XPATH, f"//li/div[text()='{state}']")))
                state_to_click.click()
                print(f"    -> Selected state: {state}")
                
                actions.move_to_element(state_dropdown_box).click().perform()
                wait.until(EC.invisibility_of_element_located(overlay_locator))
                
                top_view_element = wait.until(EC.presence_of_element_located(top_view_locator))
                select_top_view = Select(top_view_element)
                select_top_view.select_by_visible_text("STATE")
                print("    -> Selected 'STATE' from Top view.")

                wait.until(EC.invisibility_of_element_located(overlay_locator))
                
                generate_button = wait.until(EC.element_to_be_clickable(generate_report_locator))
                driver.execute_script("arguments[0].click();", generate_button)
                print("    -> ✅ Report generation started...")
                time.sleep(10)

                state_dropdown_box = wait.until(EC.presence_of_element_located(state_dropdown_box_locator))
                actions = ActionChains(driver)
                actions.move_to_element(state_dropdown_box).click().perform()
                state_to_deselect = wait.until(EC.element_to_be_clickable((By.XPATH, f"//li/div[text()='{state}']")))
                state_to_deselect.click()
                print(f"    -> Deselected state: {state}")
                actions.move_to_element(state_dropdown_box).click().perform()
            
            except Exception as inner_e:
                print(f"    -> ❌ Error processing state {state}. Skipping. Error: {inner_e}")
                driver.refresh()
                click_download_button(driver)
                wait.until(EC.visibility_of_element_located(modal_locator))


except Exception:
    print(f"❌ An error occurred during processing:")
    traceback.print_exc()

finally:
    print("\nScript finished. Closing browser.")
    driver.quit()
