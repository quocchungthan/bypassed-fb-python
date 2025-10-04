import csv
import os
import time
from selenium.webdriver.common.by import By

from fb_post_parser import extract_post_data  # 👈 Import the helper

class FacebookGroupScraper:
    def __init__(self, driver, manage_driver=False):
        self.driver = driver
        self.manage_driver = manage_driver

    def scroll_page(self, scroll_pause: float = 2.5, max_scroll: int = 5):
        """Scroll gradually to load more posts."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        for _ in range(max_scroll):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def get_recent_posts(self, group_url: str, limit: int = 10, wait_after_load: float = 5.0):
        """Visit a Facebook group page and extract recent posts."""
        self.driver.get(group_url)
        time.sleep(wait_after_load)
        self.scroll_page()

        posts = self.driver.find_elements(By.CSS_SELECTOR, "div[role='article']")
        posts_data = []

        for post in posts[:limit]:
            post_info = extract_post_data(post, group_url)
            if post_info:
                posts_data.append(post_info)

        return posts_data

    def _load_existing_post_ids(self, csv_path: str):
        """Return set of post_ids already saved in CSV (for deduplication)."""
        if not os.path.exists(csv_path):
            return set()
        post_ids = set()
        try:
            with open(csv_path, newline='', encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "post_id" in row:
                        post_ids.add(row["post_id"])
        except Exception:
            pass
        return post_ids

    def save_to_csv(self, data: list, output_path: str = "output/posts.csv"):
        """Append new post data to CSV (skip duplicates by post_id)."""
        if not data:
            return

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fieldnames = ["post_id", "group_url", "post_time", "post_link", "caption", "isSentToTelegram"]

        existing_ids = self._load_existing_post_ids(output_path)
        new_data = [d for d in data if d["post_id"] not in existing_ids]

        if not new_data:
            print("No new posts to save (all duplicates).")
            return

        write_header = not os.path.exists(output_path) or os.path.getsize(output_path) == 0

        with open(output_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerows(new_data)

        print(f"✅ Saved {len(new_data)} new posts ({len(existing_ids)} skipped duplicates).")

    def close(self):
        if self.manage_driver:
            try:
                self.driver.quit()
            except Exception:
                pass
