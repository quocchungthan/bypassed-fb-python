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
		full_caption = f"{groupname} {caption}"
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
			html_content = item.get("productDescription", "")
			# Sanitize HTML to plain text
			soup = BeautifulSoup(unescape(html_content), "html.parser")
			plain_text = soup.get_text(separator="\n").strip()
			suggestions.append(plain_text)
	if suggestions:
		# Separate suggestions by 2 line breaks
		result = "\n\n".join(suggestions)
		# Add a random endline
		result += "\n" + random.choice(endlines)
	else:
		# No suggestions, use first endline
		result = endlines[0]
	return result

# TODO: take the caption (including the name of the group there)
# calling the POST https://fasthomehanoi.vn/api/product-facebook/suggestions
# {
#  "caption": "groupname + caption text"
# }
# with basic auth (BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD)
# sample of response body: [
#[
#	{
#		"productDescription": "string", // the html content of the suggestion
#    "score": 0
#	},
#		{
#		"productDescription": "string",
#		"score": 0
#	}
#	]
# we sanitize the html, and keep the plain text in the diffrent line breaks. different suggestions, separate 2 line breaks.
# add endline randomly from endlines.json or the endlines[0] if no record return from the api.
