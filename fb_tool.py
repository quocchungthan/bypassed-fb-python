import csv
import os
import time
from selenium.webdriver.common.by import By
import re
import datetime
import json

from fb_post_parser import extract_post_data, locate_post_containers

class FacebookGroupScraper:
    def __init__(self, driver, manage_driver=False, log_dir="logs"):
        self.driver = driver
        self.manage_driver = manage_driver
        self.log_dir = log_dir
    

    def scroll_page(self, scroll_pause: float = 2.5, max_scroll: int = 20):
        """Scroll gradually to load more posts."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        for _ in range(max_scroll):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height


    def _safe_group_name(self, group_url: str) -> str:
        """Sanitize group URL into a folder-safe name."""
        name = re.sub(r"[^a-zA-Z0-9_-]+", "_", group_url.strip("/").split("/")[-1])
        return name or "unknown_group"

    def _init_log_folder(self, group_url: str) -> str:
        """Create a timestamped log folder for the given group."""
        group_name = self._safe_group_name(group_url)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder = os.path.join(self.log_dir, group_name, timestamp)
        os.makedirs(folder, exist_ok=True)
        return folder

    def _write_log(self, folder: str, filename: str, content: str):
        """Safely write text to a log file."""
        try:
            with open(os.path.join(folder, filename), "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"⚠️ Failed to write log {filename}: {e}")

    def get_recent_posts(self, group_url: str, limit: int = 10, wait_after_load: float = 5.0):
        """Visit a Facebook group page and extract recent posts with debug logs."""
        log_folder = self._init_log_folder(group_url)
        query_info = f"URL: {group_url}\nTime: {datetime.datetime.now()}\nLimit: {limit}\n\n"
        self._write_log(log_folder, "query.txt", query_info)

        self.driver.get(group_url)
        time.sleep(wait_after_load)
        self.scroll_page()

        html_snapshot = self.driver.page_source
        self._write_log(log_folder, "page.html", html_snapshot)

        posts = locate_post_containers(self.driver)
        posts_data = []

        for idx, post in enumerate(posts[:limit], start=1):
            print(f"Processing post {idx}/{limit}...")
            html_snippet = post.get_attribute("outerHTML") or ""
            self._write_log(log_folder, f"post_{idx:02d}_raw.html", html_snippet)

            post_info = extract_post_data(post, group_url)
            if post_info:
                posts_data.append(post_info)
                self._write_log(log_folder, f"post_{idx:02d}_parsed.txt", json.dumps(post_info, ensure_ascii=False, indent=2))

        # Save a summary of all parsed posts
        self._write_log(log_folder, "parsed_summary.json", json.dumps(posts_data, ensure_ascii=False, indent=2))
        print(f"🗂️ Logs saved in: {log_folder}")

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
        """Append new post data to CSV; update caption if same post_id has a longer caption."""
        if not data:
            return

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fieldnames = ["post_id", "group_url", "post_time", "post_link", "caption", "isSentToTelegram"]

        # Load existing rows
        existing_rows = self._load_existing_rows(output_path)
        existing_by_id = {r["post_id"]: r for r in existing_rows}

        updated_count = 0
        new_rows = []

        for d in data:
            pid = d["post_id"]
            if pid in existing_by_id:
                # Update caption if the new one is longer
                old_caption = existing_by_id[pid].get("caption", "")
                new_caption = d.get("caption", "")
                if len(new_caption) > len(old_caption):
                    existing_by_id[pid]["caption"] = new_caption
                    updated_count += 1
            else:
                new_rows.append(d)

        # Merge all rows (existing + new)
        all_rows = list(existing_by_id.values()) + new_rows

        # Write back all data
        write_header = not os.path.exists(output_path) or os.path.getsize(output_path) == 0
        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

        print(f"✅ Saved {len(new_rows)} new posts, updated {updated_count} captions.")

    def _load_existing_rows(self, output_path: str):
        """Load all existing rows from the CSV (if exists)."""
        if not os.path.exists(output_path):
            return []
        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def close(self):
        if self.manage_driver:
            try:
                self.driver.quit()
            except Exception:
                pass
