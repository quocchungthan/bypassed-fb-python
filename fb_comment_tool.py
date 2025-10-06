import sys
import time
from dotenv import load_dotenv
from selenium.webdriver.common.keys import Keys

# Load environment variables from .env file
load_dotenv()

def remove_non_bmp(text):
    return ''.join(c for c in text if ord(c) <= 0xFFFF)

class FacebookCommenter:
	def __init__(self, driver):
		self.driver = driver

	def comment_on_post(self, url, comment):
		self.driver.get(url)
		time.sleep(3)
		try:
			cmt_box = self.driver.find_element("css selector", "form[role='presentation'] div[role='textbox']")
			cmt_box.click()
			time.sleep(1)
			for part in remove_non_bmp(comment).split('\n'):
				cmt_box.send_keys(part)
				time.sleep(1)
				cmt_box.send_keys(Keys.SHIFT, Keys.ENTER)
				time.sleep(1)

			# Finally press Enter to submit
			cmt_box.send_keys(Keys.ENTER)
			time.sleep(2)
			current_url = self.driver.current_url
		except Exception as e:
			print(f"[ERROR] Failed to comment: {e}", file=sys.stderr)
			current_url = url
		return current_url
