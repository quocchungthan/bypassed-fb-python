import os
import time
from datetime import datetime
from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
import pyperclip
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

import re

def contains_9_digit_sequence(text: str) -> bool:
    """
    Clean the input text by removing spaces and dots,
    then check if it contains a sequence of at least 9 continuous digits.
    Returns True if found, otherwise False.
    """
    if not text:
        return False

    # Remove spaces and dots
    cleaned_text = text.replace(" ", "").replace(".", "")

    # Check for 9 or more continuous digits
    return bool(re.search(r"\d{9,}", cleaned_text))

# Load environment variables from .env file
load_dotenv()

FB_KEYWORDS = [k.strip() for k in os.getenv("FB_KEYWORDS", "keyword1 ,keyword2").split(",") if k.strip()]
BLACK_LIST = [k.strip() for k in os.getenv("BLACK_LIST", "keyword1 ,keyword2").split(",") if k.strip()]
COPY_LINK_TEXT = os.getenv("COPY_LINK_TEXT", "Copy link")


def copy_to_clipboard(text):
    """Copy the given text to the system clipboard."""
    pyperclip.copy(text)
    return True

class FacebookGroupScraper:
    def __init__(self, driver, manage_driver=True):
        self.driver = driver
        self.manage_driver = manage_driver

    def _extract_group_id(self, group_url: str) -> str:
        """Extract group ID or name from a Facebook group URL."""
        try:
            path = urlparse(group_url).path.strip("/")
            parts = path.split("/")
            if len(parts) >= 2 and parts[0] == "groups":
                return parts[1]
            return "unknown_group"
        except Exception:
            return "unknown_group"

    def _scroll_and_capture_posts(self, css_selector: str, max_scrolls: int = 10, scroll_pause: float = 2):
        """Scroll and capture all post containers matching selector."""
        collected_html = set()
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        # TODO: get the inner text of html of the title tag to get the group name.
        group_name = self.driver.title
        print(f"[INFO] Detected group name: {group_name}")
        for i in range(max_scrolls):
            print(f"[INFO] Scrolling iteration {i+1}/{max_scrolls} ...")
            time.sleep(scroll_pause)

            try:
                post_elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
                print(f"[INFO] Found {len(post_elements)} posts so far.")
                for el in post_elements:
                    try:
                        # Check if post contains any of the FB_KEYWORDS
                        post_text = el.text.lower()
                        if contains_9_digit_sequence(post_text) or not any(keyword.lower() in post_text for keyword in FB_KEYWORDS) or any(black_item.lower() in post_text for black_item in BLACK_LIST):
                            print(f"[⏭️] Skipping post (no keywords found) or has blacklist word or has phonenumber")
                            continue

                        # Get HTML
                        html = el.get_attribute("outerHTML")
                        html = "<div> GROUPNAME = " + group_name +  "\n</div>" + "\n" + html;
                        post_pure_html = html.lower()
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
                        time.sleep(1)
                        if post_pure_html.count('/posts/') == 0:
                            # Try clicking the "Share" button
                            try:
                                share_button = el.find_element(By.CSS_SELECTOR, 'span[data-ad-rendering-role="share_button"]')
                                ActionChains(self.driver).move_to_element(share_button).click(share_button).perform()
                                time.sleep(2)

                                # Wait for the popup to appear and find the "Copy link" button
                                copy_link_button = WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located((
                                        By.XPATH, f'//div[@role="button" and (contains(., "{COPY_LINK_TEXT}") or .//span[contains(., "{COPY_LINK_TEXT}")])]'
                                    ))
                                )
                                copy_link_button.click()
                                time.sleep(1)  # wait for clipboard to update

                                post_url = pyperclip.paste()
                                print(f"[🔗] Copied post URL: {post_url}")
                            except Exception as share_err:
                                print(f"[⚠️] Failed to extract post link: {share_err}")
                                post_url = "link_not_found"

                            # Append the copied link at the end of HTML for now
                            html += f"\n<a href=\"{post_url}\"> go to post </a>"

                        collected_html.add(html)

                    except WebDriverException:
                        continue
            except NoSuchElementException:
                pass

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("[INFO] Reached end of scrollable content.")
                break
            last_height = new_height

        return collected_html

    def capture_group_posts_html(self, group_url: str, css_selector: str, max_scrolls: int = 10):
        """Open a group, scroll, and save each post container as separate HTML file."""
        print(f"[INFO] Accessing group: {group_url}")
        group_id = self._extract_group_id(group_url)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("logs", group_id, timestamp)
        os.makedirs(output_dir, exist_ok=True)

        try:
            self.driver.get(group_url)
            time.sleep(5)

            posts_html = self._scroll_and_capture_posts(css_selector, max_scrolls=max_scrolls)
            print(f"[INFO] Total unique posts collected: {len(posts_html)}")

            # Save each post as post_###.html
            for idx, html in enumerate(posts_html, start=1):
                count = html.count('data-ad-rendering-role="story_message"')
                print(f"[🔍] Post {idx:03d} has {count} occurrences of story_message")

                if count > 0:
                    file_path = os.path.join(output_dir, f"post_{idx:03d}.html")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(html)
                    print(f"[✅] Saved post {idx:03d} to {file_path}")
                else:
                    print(f"[⏭️] Skipped post {idx:03d} (no story_message found)")

            print(f"[DONE] Group {group_id}: saved {len(posts_html)} posts to {output_dir}")

        except WebDriverException as e:
            print(f"[ERROR] WebDriver failed for group {group_url}: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error for group {group_url}: {e}")
        finally:
            if self.manage_driver:
                self.driver.quit()
