from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Load credentials from environment variables for safety
FB_USERNAME = os.getenv("FB_USERNAME", "your_email_or_phone")
FB_PASSWORD = os.getenv("FB_PASSWORD", "your_password")
profile_path = os.getenv("CHROME_PROFILE_PATH", "invalid")

print(profile_path)

# Launch browser (Chrome in this example)
options = webdriver.ChromeOptions()
# using existing profile to get rid of login part.
options.add_argument(f"--user-data-dir={profile_path}")

# options.add_argument("--disable-notifications")  # prevent popup dialogs
driver = webdriver.Chrome(options=options)

try:
    # Go to Facebook login page
    driver.get("https://www.facebook.com/")
    time.sleep(2)

    # using existing profile to get rid of login part.
    # Find and fill email/phone input
    # email_input = driver.find_element(By.ID, "email")
    # email_input.send_keys(FB_USERNAME)

    # Find and fill password input
    # password_input = driver.find_element(By.ID, "pass")
    # password_input.send_keys(FB_PASSWORD)

    # Press Enter (submit form)
    # password_input.send_keys(Keys.RETURN)

    time.sleep(20)  # wait for login to complete

    # Example: Go to a group or profile page
    driver.get("https://www.facebook.com/me")
    time.sleep(5)

finally:
    driver.quit()
