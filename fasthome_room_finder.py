import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
BASIC_AUTH_USERNAME=os.getenv("BASIC_AUTH_USERNAME", "your_email_or_phone")
BASIC_AUTH_PASSWORD=os.getenv("BASIC_AUTH_PASSWORD", "your_password")
# load the endlines.json file.

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
