import sys
import time
from dotenv import load_dotenv
from fb_tool import copy_to_clipboard

# Load environment variables from .env file
load_dotenv()


class FacebookCommenter:
	def __init__(self, driver):
		self.driver = driver

	def comment_on_post(self, url, comment):
		self.driver.get(url)
		time.sleep(3)
		copy_to_clipboard(comment)
		try:
			cmt_box = self.driver.find_element("css selector", "form[role='presentation'] div[role='textbox']")
			cmt_box.click()
			time.sleep(1)
			cmt_box.send_keys("\ue03d")  # Ctrl+V
			time.sleep(1)
			btn = self.driver.find_element("css selector", "div[contenteditable='true'][role='button']")
			btn.click()
			time.sleep(2)
			current_url = self.driver.current_url
		except Exception as e:
			print(f"[ERROR] Failed to comment: {e}", file=sys.stderr)
			current_url = url
		return current_url
