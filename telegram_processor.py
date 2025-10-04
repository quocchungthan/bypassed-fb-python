import os
import re
import csv
import requests
import shutil
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
SENT_LOG_PATH = "output/sent_posts.csv"


class TelegramNotifier:
    def __init__(self, logs_root="logs"):
        self.logs_root = logs_root
        os.makedirs(os.path.dirname(SENT_LOG_PATH), exist_ok=True)
        self.sent_links = self._load_sent_links()

    def _load_sent_links(self):
        links = set()
        if os.path.exists(SENT_LOG_PATH):
            with open(SENT_LOG_PATH, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        links.add(row[0])
        return links

    def _save_sent_link(self, link):
        with open(SENT_LOG_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([link])
        self.sent_links.add(link)

    def _extract_caption_and_url(self, text_path):
        """Extract caption and the first valid URL from the .txt file."""
        caption = ""
        url = ""

        with open(text_path, encoding="utf-8") as f:
            content = f.read()

        # --- Extract caption ---
        match_caption = re.search(r"==== Captions ====\n(.*?)\n====", content, re.S)
        if match_caption:
            caption = match_caption.group(1).strip()
            # Check if caption is duplicated (two equal halves)
            half = len(caption) // 2
            if len(caption) % 2 == 0 and caption[:half] == caption[half:]:
                caption = caption[:half].strip()

        # --- Extract URLs ---
        if '==== URL Paths ====' in content:
            url_section = content.split('==== URL Paths ====')[1]
        else:
            url_section = ""
        match_urls = re.findall(r"https?://[^\s]+|(?:/groups/.*/posts/[^\s]+|/share/p/[^\s]+)", url_section)
        if match_urls:
            raw_url = match_urls[0].strip()
            if raw_url.startswith("/"):
                url = f"https://www.facebook.com{raw_url}"
            else:
                url = raw_url

        return caption, url

    def _send_telegram_message(self, caption, url):
        """Send message to Telegram in HTML format."""
        if not BOT_TOKEN or not CHAT_ID:
            print("[ERROR] Missing Telegram credentials.")
            return

        html_message = f"<b>{caption}</b>\n\n<a href='{url}'>🔗 View Post</a>"
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": html_message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
        )

        if response.status_code == 200:
            print(f"[✅] Sent successfully: {url}")
        else:
            print(f"[❌] Failed to send: {url} → {response.text}")

    def run(self):
        """Scan logs folder for .txt files and send messages."""
        for root, _, files in os.walk(self.logs_root):
            for f in files:
                if f.endswith(".txt"):
                    text_path = os.path.join(root, f)
                    caption, url = self._extract_caption_and_url(text_path)

                    if not url:
                        print(f"[SKIP] No valid post URL found in {text_path}")
                        continue

                    if url in self.sent_links:
                        print(f"[SKIP] Already sent: {url}")
                        continue
                    # TODO: call the cmt tool here. that tool accept the url, browser go to the url, then comment the picture cmt.png I prepared.
                    print(f"[INFO] Sending post → {url}")
                    self._send_telegram_message(caption or "(No caption)", url)
                    self._save_sent_link(url)

        # After finishing all, clean up logs to save disk space
        print("[🧹] Cleaning logs folder...")
        shutil.rmtree(self.logs_root, ignore_errors=True)
        os.makedirs(self.logs_root, exist_ok=True)
        print("[✅] Logs cleaned up.")
