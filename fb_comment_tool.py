import sys
import time
from dotenv import load_dotenv
import os
import random
from selenium.webdriver.common.keys import Keys

# Load environment variables from .env file
load_dotenv()

def remove_non_bmp(text):
    return ''.join(c for c in text if ord(c) <= 0xFFFF)


def get_cmt_image_abspath(filename="cmt.jpeg"):
	"""
	Return the absolute path to the image file in the current directory.
	"""
	return os.path.abspath(filename)

class FacebookCommenter:
	def __init__(self, driver):
		self.driver = driver

	def comment_on_post(self, url, comment):
		if comment is None or comment.strip() == "":
			print("[INFO] No comment to post.")
			return url
		self.driver.get(url)
		time.sleep(6) # take quite long for the inbox to dissapear.
		try:
			cmt_box = self.driver.find_element("css selector", "form[role='presentation'] div[role='textbox']")
			cmt_box.click()
			for part in remove_non_bmp(comment).split('\n'):
				if part.strip() == "":
					continue
				# line for picture f"[IMG{idx+1}] {download_path}"
				if part.startswith("[IMG"):
					img_filename = part.split(" ")[1]
					img_path = get_cmt_image_abspath(img_filename)
					self.upload_comment_image(img_path)
					time.sleep(1)
					continue
				cmt_box.send_keys(part)
				time.sleep(1)
				cmt_box.send_keys(" ");
				cmt_box.send_keys(" ");
				cmt_box.send_keys(Keys.SHIFT, Keys.ENTER)
				time.sleep(1)

			# Optionally attach an image if needed using upload_comment_image
			image_filename = f"cmt{random.choice([1,2])}.jpeg"
			image_path = get_cmt_image_abspath(image_filename)
			self.upload_comment_image(image_path)
			time.sleep(1)
			# Finally press Enter to submit
			cmt_box.send_keys(Keys.ENTER)
			time.sleep(2)
			current_url = self.driver.current_url
		except Exception as e:
			print(f"[ERROR] Failed to comment: {e}", file=sys.stderr)
			current_url = url
		# Remove query parameters from URL if present
		if current_url and "?" in current_url:
			current_url = current_url.split("?")[0]
		return current_url

	def upload_comment_image(self, image_path):
		"""
		Uploads an image to the Facebook comment input field.
		:param image_path: Path to the image file to upload.
		"""
		try:
			# Find the control div containing the file input for image upload
			control_div = self.driver.find_element(
				"css selector",
				'div[id="focused-state-actions-list"] ul > li:nth-child(3) input[type="file"]'
			)
			control_div.send_keys(image_path)
			time.sleep(2)  # Wait for the image to upload
		except Exception as e:
			print(f"[ERROR] Failed to upload image: {e}", file=sys.stderr)
