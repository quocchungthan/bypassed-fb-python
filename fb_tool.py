# fb_tool.py
import csv
import os
import re
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


class FacebookGroupScraper:
    def __init__(self, driver, manage_driver=False):
        """
        driver: an existing selenium webdriver instance
        manage_driver: if True, scraper will quit driver on close()
        """
        self.driver = driver
        self.manage_driver = manage_driver

    # ====================
    # Utility methods
    # ====================

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

    def _extract_post_link(self, post):
        """Try multiple patterns to find a valid post link."""
        link_selectors = [
            "a[href*='/posts/']",
            "a[href*='/permalink/']",
            "a[href*='story_fbid=']",
            "a[href*='/groups/'][href*='/?__cft__']",
            "a[aria-label][role='link']",
        ]
        for selector in link_selectors:
            try:
                link_el = post.find_element(By.CSS_SELECTOR, selector)
                href = link_el.get_attribute("href")
                if href:
                    # Normalize to clean link
                    clean = href.split("?")[0]
                    return clean
            except NoSuchElementException:
                continue
        return ""

    def _extract_post_id(self, post_link: str) -> str:
        """Extract numeric post ID from any known Facebook link pattern."""
        if not post_link:
            return ""
        patterns = [
            r"/posts/(\d+)",          # /posts/123456789
            r"/permalink/(\d+)",      # /permalink/123456789
            r"story_fbid=(\d+)",      # story_fbid=123456789
        ]
        for pat in patterns:
            match = re.search(pat, post_link)
            if match:
                return match.group(1)
        return ""

    # ====================
    # Scraping logic
    # ====================

    def get_recent_posts(self, group_url: str, limit: int = 10, wait_after_load: float = 5.0):
        """Visit a Facebook group page and extract recent posts."""
        self.driver.get(group_url)
        time.sleep(wait_after_load)
        self.scroll_page()

        posts_data = []
        posts = self.driver.find_elements(By.CSS_SELECTOR, "div[role='article']")

        for post in posts[:limit]:
            try:
                # 1️⃣ Link + ID
                post_link = self._extract_post_link(post)
                post_id = self._extract_post_id(post_link)

                # 2️⃣ Caption
                caption = ""
                try:
                    caption_el = post.find_element(By.CSS_SELECTOR, "div[dir='auto']")
                    caption = caption_el.text.strip()
                except NoSuchElementException:
                    pass

                # 3️⃣ Post time
                post_time = "Unknown"
                try:
                    time_el = post.find_element(By.CSS_SELECTOR, "a[aria-label] abbr, abbr")
                    post_time = time_el.get_attribute("aria-label") or time_el.text
                except Exception:
                    pass

                if post_id:  # Only include if valid ID
                    posts_data.append({
                        "post_id": post_id,
                        "group_url": group_url,
                        "post_time": post_time,
                        "post_link": post_link,
                        "caption": caption,
                        "isSentToTelegram": False
                    })

            except Exception as e:
                print("Error parsing a post:", e)
                continue

        return posts_data

    # ====================
    # CSV handling
    # ====================

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

    # ====================
    # Cleanup
    # ====================

    def close(self):
        if self.manage_driver:
            try:
                self.driver.quit()
            except Exception:
                pass
