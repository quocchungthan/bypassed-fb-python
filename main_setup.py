from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os
from fb_tool import FacebookGroupScraper
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Load credentials from environment variables for safety
FB_USERNAME = os.getenv("FB_USERNAME", "your_email_or_phone")
FB_PASSWORD = os.getenv("FB_PASSWORD", "your_password")
FB_KEYWORDS = [k.strip() for k in os.getenv("FB_KEYWORDS", "keyword1 ,keyword2").split(",") if k.strip()]
profile_path = os.getenv("CHROME_PROFILE_PATH", "invalid")

print(profile_path)

# Launch browser (Chrome in this example)
options = webdriver.ChromeOptions()
# using existing profile to get rid of login part.
options.add_argument(f"--user-data-dir={profile_path}")
options.add_argument("--disable-notifications")
options.add_argument("--start-maximized")

options.add_argument("--lang=vi-VN")
options.add_experimental_option(
    "prefs",
    {
        "intl.accept_languages": "vi-VN,vi",
        "translate_whitelists": {},  # don't force translation
        "translate.enabled": False,  # disable auto-translation
    },
)

# options.add_argument("--disable-notifications")  # prevent popup dialogs
driver = webdriver.Chrome(options=options)
scraper = FacebookGroupScraper(driver=driver, manage_driver=False)  # we manage quitting in main

try:
    # Go to Facebook login page
    driver.get("https://www.facebook.com/")
    time.sleep(2)
    # # Example: Go to a group or profile page
    driver.get("https://www.facebook.com/me")
    time.sleep(1000) # time for login if needed and setting up zalo, languages for the browser profile.

finally:
    driver.quit()
