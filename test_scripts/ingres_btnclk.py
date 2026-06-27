from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import re
import time
import requests
import os
import json


# Website
web = 'https://ingres.iith.ac.in/gecdataonline/misview;locname=INDIA;loctype=COUNTRY;locuuid=ffce954d-24e1-494b-ba7e-0931d8ad6085;component=recharge;period=annual;stateuuid=ffce954d-24e1-494b-ba7e-0931d8ad6085;category=all;year=2024-2025;view=admin;computationType=normal'

# Setup Chrome with auto driver management
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

driver.get(web)
driver.maximize_window()

def click_download_button(driver):
    try:
        wait = WebDriverWait(driver, 40)

        # 🔹 Wait until overlay disappears or is removed
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "ngx-overlay")))

        # 🔹 Wait for the button
        button = wait.until(
            EC.presence_of_element_located((By.NAME, "download"))
        )

        try:
            # First try normal Selenium click
            wait.until(EC.element_to_be_clickable((By.NAME, "download")))
            button.click()
            print("✅ Button clicked normally")
        except:
            # If intercepted, use JavaScript click as fallback
            driver.execute_script("arguments[0].click();", button)
            print("⚡ Button clicked with JavaScript (fallback)")

    except Exception as e:
        print("❌ Could not click button:", e)

# Call the function
click_download_button(driver)

# Wait for download to finish
time.sleep(10)

driver.quit()