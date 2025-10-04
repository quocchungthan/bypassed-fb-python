import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


def extract_post_link(post):
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
                return href.split("?")[0]
        except NoSuchElementException:
            continue
    return ""


def extract_post_id(post_link: str) -> str:
    """Extract numeric post ID from any known Facebook link pattern."""
    if not post_link:
        return ""
    patterns = [
        r"/posts/(\d+)",
        r"/permalink/(\d+)",
        r"story_fbid=(\d+)",
    ]
    for pat in patterns:
        match = re.search(pat, post_link)
        if match:
            return match.group(1)
    return ""


def extract_post_data(post, group_url: str):
    """Extract structured post data from a single Facebook post element."""
    try:
        # 1️⃣ Link + ID
        post_link = extract_post_link(post)
        post_id = extract_post_id(post_link)

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

        if not post_id:
            return None

        return {
            "post_id": post_id,
            "group_url": group_url,
            "post_time": post_time,
            "post_link": post_link,
            "caption": caption,
            "isSentToTelegram": False,
        }
    except Exception as e:
        print("Error parsing a post:", e)
        return None
