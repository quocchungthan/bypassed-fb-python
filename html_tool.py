import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class HtmlSanitizer:
    def __init__(self, logs_root="logs"):
        self.logs_root = logs_root

    def _extract_text_and_urls(self, html_content: str):
        """Extract plain text, URLs, and URL paths from HTML."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract readable text
        text = soup.get_text(separator="\n", strip=True)

        # Extract href URLs
        hrefs = sorted(set(tag["href"] for tag in soup.find_all(href=True)))

        # Extract URL paths
        url_paths = []
        for h in hrefs:
            try:
                parsed = urlparse(h)
                if parsed.path:
                    url_paths.append(parsed.path)
            except Exception:
                continue

        return text, hrefs, sorted(set(url_paths))

    def _extract_text_and_urls(self, html_content: str):
        """Extract plain text, URLs, URL paths, and caption text from HTML."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract readable text
        text = soup.get_text(separator="\n", strip=True)

        # Extract href URLs
        hrefs = sorted(set(tag["href"] for tag in soup.find_all(href=True)))

        # Extract URL paths
        url_paths = []
        for h in hrefs:
            try:
                parsed = urlparse(h)
                if parsed.path:
                    url_paths.append(parsed.path)
            except Exception:
                continue

        # Extract caption-like text from story_message role
        caption_elements = soup.find_all(attrs={"data-ad-rendering-role": "story_message"})
        captions = [el.get_text(strip=True) for el in caption_elements if el.get_text(strip=True)]

        return text, hrefs, sorted(set(url_paths)), captions

    def _cleanup_text(self, text: str) -> str:
        """Clean text: merge 1-char lines, remove duplicates."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        # merge single-character lines with the previous one
        merged_lines = []
        for line in lines:
            if len(line) == 1 and merged_lines:
                merged_lines[-1] += line  # append without space
            else:
                merged_lines.append(line)

        # remove duplicate lines (case-insensitive)
        seen = set()
        unique_lines = []
        for line in merged_lines:
            normalized = line.lower()
            if normalized not in seen:
                seen.add(normalized)
                unique_lines.append(line)

        return "\n".join(unique_lines)

    def sanitize_file(self, html_path: str):
        """Convert one .html file into .txt with cleaned text, captions, and URLs."""
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            text, hrefs, paths, captions = self._extract_text_and_urls(html_content)
            cleaned_text = self._cleanup_text(text)

            txt_path = html_path.replace(".html", ".txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("==== Extracted Text ====\n")
                f.write(cleaned_text + "\n\n")

                if captions:
                    f.write("==== Captions ====\n")
                    for cap in captions:
                        f.write(cap + "\n")
                    f.write("\n")

                f.write("==== URLs ====\n")
                for h in hrefs:
                    f.write(h + "\n")

                f.write("\n==== URL Paths ====\n")
                for p in paths:
                    f.write(p + "\n")

            print(f"[✅] Sanitized: {os.path.basename(html_path)} -> {os.path.basename(txt_path)}")

        except Exception as e:
            print(f"[ERROR] Failed to sanitize {html_path}: {e}")

    def run(self):
        """Run through all .html files inside logs/ recursively."""
        print(f"[INFO] Scanning logs folder: {self.logs_root}")
        for root, _, files in os.walk(self.logs_root):
            for filename in files:
                if filename.endswith(".html"):
                    full_path = os.path.join(root, filename)
                    self.sanitize_file(full_path)
        print("[DONE] HTML sanitization completed.")
