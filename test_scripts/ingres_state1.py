from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
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
        wait = WebDriverWait(driver, 40)
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "ngx-overlay")))
        button = wait.until(EC.element_to_be_clickable((By.NAME, "download")))
        try:
            button.click()
            print("✅ Button clicked normally")
        except:
            driver.execute_script("arguments[0].click();", button)
            print("⚡ Button clicked with JavaScript (fallback)")
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
    
    print("Waiting for the 'Assessment Year' dropdown to be present...")
    year_select_element = wait.until(EC.presence_of_element_located(year_dropdown_locator))
    print("🔎 Found the 'Assessment Year' dropdown.")
    
    target_year = "2022-2023"
    print(f"\n- Selecting a single year using JavaScript: {target_year}")
    
    js_script = f"""
    var selectElement = arguments[0];
    selectElement.value = '{target_year}';
    var event = new Event('change', {{ 'bubbles': true }});
    selectElement.dispatchEvent(event);
    """
    driver.execute_script(js_script, year_select_element)
    
    print("  -> Waiting for State dropdown to be ready...")
    state_dropdown_box = wait.until(EC.presence_of_element_located(state_dropdown_box_locator))
    print("  -> Opening State dropdown using JavaScript...")
    driver.execute_script("arguments[0].click();", state_dropdown_box)

    # --- UPDATED LOCATOR BASED ON YOUR FINDING ---
    state_options_locator = (By.XPATH, "//div[@class='dropdown-list']/ul[2]/li")

    print("  -> Waiting for state list to appear...")
    wait.until(EC.visibility_of_element_located(state_options_locator))
    state_elements = driver.find_elements(*state_options_locator)

    state_names = [state.text for state in state_elements if state.text]
    print(f"  -> Found {len(state_names)} states.")

    selected_states = []
    for state_name in state_names:
        print(f"    - Selecting state: {state_name}")
        state_to_click = wait.until(EC.element_to_be_clickable((By.XPATH, f"//li/div[text()='{state_name}']")))
        state_to_click.click()
        selected_states.append(state_name)
        time.sleep(0.5)

    print("  -> Closing State dropdown.")
    driver.execute_script("arguments[0].click();", state_dropdown_box)
    
    print("\n✅ Successfully selected one year and all corresponding states.")

except Exception:
    print(f"❌ An error occurred during processing:")
    traceback.print_exc()

finally:
    print("Closing browser in 5 seconds...")
    time.sleep(5)
    driver.quit()