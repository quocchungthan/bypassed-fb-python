from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# TODO: take the url and cmt, then navigate to the url. Click to cmt box, then paste the cmt from clipboard.
# then return the current url of the post.
# refer to the fb_tool.py for using driver brwosers and code and copy paste command.
# seeking for where to click to cmt box query selector = 'form[role="presentation"] div[role="textbox"]'
# cmt to paste the cmt content from clipboard (copy it when start the function).
# then find the button div[aria-label="Comment"][role="button"] and click it.