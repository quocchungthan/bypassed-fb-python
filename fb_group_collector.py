import os
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


class FacebookGroupCollector:
    """
    Collect all group URLs from https://www.facebook.com/groups/joins/?nav_source=tab
    """

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def scroll_to_bottom(self, pause_time=2, max_scrolls=20):
        """Scroll the page multiple times to load more groups."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        for i in range(max_scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause_time)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print(f"[INFO] Reached bottom after {i + 1} scrolls.")
                break
            last_height = new_height

    def get_all_group_urls(self, max_scrolls=20):
        """Visit joined groups page, scroll, and extract all group URLs."""
        print("[INFO] Opening joined groups page...")
        self.driver.get("https://www.facebook.com/groups/joins/?nav_source=tab")
        time.sleep(5)

        self.scroll_to_bottom(max_scrolls=max_scrolls)

        print("[INFO] Extracting group URLs...")
        page_html = self.driver.page_source

        # find pattern like: href="https://www.facebook.com/groups/532455213625163/"
        urls = re.findall(r'href="(https://www\.facebook\.com/groups/\d+/)"', page_html)

        unique_urls = sorted(set(urls))
        print(f"[INFO] Found {len(unique_urls)} unique groups.")

        # save to file for reuse
        os.makedirs("output", exist_ok=True)
        output_path = os.path.join("output", "group_urls.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(unique_urls))
        print(f"[✅] Saved group URLs to {output_path}")

        return unique_urls
