import os
from dotenv import load_dotenv
import json
import requests
import random
from html import unescape
from bs4 import BeautifulSoup
import base64

# Load environment variables from .env file
load_dotenv()
BASIC_AUTH_USERNAME=os.getenv("BASIC_AUTH_USERNAME", "your_email_or_phone")
BASIC_AUTH_PASSWORD=os.getenv("BASIC_AUTH_PASSWORD", "your_password")

# Load endlines.json
with open("endlines.json", encoding="utf-8") as f:
	endlines = json.load(f)

def get_suggestions(caption, groupname=None):
	"""
	Calls the suggestion API and returns plain text suggestions with random endlines.
	"""
	if groupname:
		full_caption = f"CAPTION: {caption} - IN GROUP: {groupname}"
	else:
		full_caption = caption
	url = "https://fasthomehanoi.vn/api/product-facebook/suggestions"
	userpass = f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}"
	b64 = base64.b64encode(userpass.encode()).decode()
	headers = {"Authorization": f"Basic {b64}"}
	payload = {"caption": full_caption}
	try:
		resp = requests.post(url, json=payload, headers=headers, timeout=60)
		if resp.status_code != 200:
			print(f"[ERROR] API call failed: status={resp.status_code}, response={resp.text}")
			data = []
		else:
			data = resp.json()
	except requests.exceptions.Timeout:
		print(f"[ERROR] API call timed out after 60 seconds.")
		data = []
	except requests.exceptions.RequestException as e:
		print(f"[ERROR] API call failed: {e}")
		if hasattr(e, 'response') and e.response is not None:
			print(f"[ERROR] Response: status={e.response.status_code}, body={e.response.text}")
		data = []

	suggestions = []
	if data and isinstance(data, list):
		for item in data:
			# html_content = item.get("productDescription", "")
			pictureUrls = item.get("pictureUrls", [])
			isLookingForRental = item.get("isLookingForRental", False)
			if isLookingForRental == False:
				return None
			if pictureUrls and isinstance(pictureUrls, list):
				for idx, picUrl in enumerate(pictureUrls):
					download_path = f"cmt{idx+1}.webp"
					try:
						img_resp = requests.get(picUrl, timeout=30)
						if img_resp.status_code == 200:
							with open(download_path, "wb") as img_file:
								img_file.write(img_resp.content)
							suggestions.append(f"[IMG{idx+1}] {download_path}")
						else:
							print(f"[ERROR] Failed to download image: {picUrl}, status={img_resp.status_code}")
					except requests.exceptions.Timeout:
						print(f"[ERROR] Image download timed out after 30 seconds.")
					except requests.exceptions.RequestException as e:
						print(f"[ERROR] Image download failed: {e}")
			# Sanitize HTML to plain text
			# soup = BeautifulSoup(unescape(html_content), "html.parser")
			# plain_text = soup.get_text(separator="\n").strip()
			# suggestions.append(plain_text)
	if suggestions:
		# Separate suggestions by 2 line breaks
		result = random.choice(endlines) + "\n" + "\n\n".join(suggestions)
	else:
		# No suggestions, use first endline
		result = random.choice(endlines)
	return result
