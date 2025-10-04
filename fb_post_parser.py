# fb_post_parser.py
import re
from typing import List
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup  # optional dependency; still recommended


# --------------------
# Post container discovery
# --------------------
def locate_post_containers(driver, max_results: int = 50) -> List:
    """
    Try multiple selectors to collect post container DIVs.
    Returns a list of unique WebElements (best-effort dedup).
    """
    selectors = [
        "div[role='article']",
        'div[data-ad-rendering-role="story_message"]',
        'div[data-ad-preview="message"]',
        # example obfuscated class pattern (from your TODO); Facebook classes change often
        "div.x1yztbdb.x1n2onr6.xh8yej3.x1ja2u2z",
    ]

    found = []
    seen_keys = set()

    for sel in selectors:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
        except WebDriverException:
            els = []
        for el in els:
            # generate a deduplication key: prefer stable attributes, fallback to snippet of outerHTML
            key = el.get_attribute("id") or el.get_attribute("data-ft") or (el.get_attribute("outerHTML") or "")[:300]
            if key and key not in seen_keys:
                seen_keys.add(key)
                found.append(el)
            elif not key:
                # if no key, fallback to adding by object identity (best-effort)
                if el not in found:
                    found.append(el)
        if len(found) >= max_results:
            break

    # As a final fallback, if nothing found using selectors, try searching for article tags
    if not found:
        try:
            els = driver.find_elements(By.TAG_NAME, "article")
            for el in els:
                key = el.get_attribute("id") or (el.get_attribute("outerHTML") or "")[:300]
                if key not in seen_keys:
                    seen_keys.add(key)
                    found.append(el)
        except Exception:
            pass

    return found[:max_results]


def find_post_container_from_child(el):
    """
    Given a WebElement that may be a child inside a post, walk up ancestors to find the logical post container.
    Tries multiple ancestor predicates and class-containing checks.
    """
    xpath_checks = [
        "ancestor::div[@role='article']",
        "ancestor::div[@data-ad-rendering-role='story_message']",
        "ancestor::div[@data-ad-preview='message']",
        "ancestor::div[contains(@class, 'x1yztbdb')]",  # fallback obfuscated-class check
        "ancestor::article",
        "ancestor::div",  # last resort: the nearest div ancestor
    ]

    for xp in xpath_checks:
        try:
            ancestor = el.find_element(By.XPATH, xp)
            if ancestor:
                return ancestor
        except NoSuchElementException:
            continue
        except Exception:
            continue

    # if everything fails, return the original element
    return el


# --------------------
# Extraction helpers
# --------------------
# For extracting the post link we should:
# find the role button span data-ad-rendering-role="share_button" then click
# then file the span with inner text is "Copy link" to get the link into the clipboard
def extract_post_link(post):
    """Try multiple patterns to find a valid post link (from within the post container)."""
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
                return href.split("?")[0]
        except NoSuchElementException:
            continue
    try:
        share_btn = post.find_element(By.CSS_SELECTOR, 'span[data-ad-rendering-role="share_button"]')
        driver = post.parent  # get the driver from context
        share_btn.click()
        time.sleep(1.5)

        # Look for “Copy link” in the menu
        copy_btns = driver.find_elements(By.XPATH, "//span[contains(text(), 'Copy link')]") # or "Sao chép liên kết" in vetnamese
        if copy_btns:
            copy_btns[0].click()
            time.sleep(0.5)
            # Now the link should be in clipboard
            link = pyperclip.paste()
            if link:
                return link.split("?")[0]
    except Exception as e:
        print("Share-button extraction failed:", e)

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


def _sanitize_html(html_content: str) -> str:
    """Remove HTML tags and return plain text (BeautifulSoup)."""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except Exception:
        # conservative fallback: strip tags via regex (not perfect)
        return re.sub(r"<[^>]+>", "", html_content).strip()


def extract_post_caption(post):
    """
    Extracts caption text from different possible Facebook post structures:
    - data-ad-rendering-role="story_message"
    - data-ad-preview="message"
    """
    caption = ""
    selectors = [
        '[data-ad-rendering-role="story_message"]',
        '[data-ad-preview="message"]',
    ]
    for selector in selectors:
        try:
            el = post.find_element(By.CSS_SELECTOR, selector)
            html = el.get_attribute("innerHTML") or el.get_attribute("textContent") or ""
            caption = _sanitize_html(html)
            if caption:
                return caption
        except NoSuchElementException:
            continue
        except Exception:
            continue
    return caption


def extract_post_time(post):
    """Extract post time using multiple possible time label structures."""
    post_time = "Unknown"
    try:
        # first try the more specific pattern
        time_el = post.find_element(By.CSS_SELECTOR, "a[aria-label] abbr, abbr")
        post_time = time_el.get_attribute("aria-label") or time_el.text
    except Exception:
        try:
            # fallback: any abbr inside post
            time_el = post.find_element(By.TAG_NAME, "abbr")
            post_time = time_el.get_attribute("aria-label") or time_el.text
        except Exception:
            pass
    return post_time


def extract_post_data(post, group_url: str):
    """
    Given a post container WebElement, extract structured info.
    Accepts either a container element or a child element (will locate container).
    """
    try:
        # if this element is not clearly a container, try to find the container ancestor
        # by inspecting known attributes
        maybe_container = post
        # Heuristic: if it doesn't have role='article' or data-ad-* attrs, try to find ancestor
        try:
            data_render = maybe_container.get_attribute("data-ad-rendering-role") or ""
            data_preview = maybe_container.get_attribute("data-ad-preview") or ""
        except Exception:
            role = data_render = data_preview = ""

        if not (data_render or data_preview):
            maybe_container = find_post_container_from_child(post)

        post_link = extract_post_link(maybe_container)
        post_id = extract_post_id(post_link)
        caption = extract_post_caption(maybe_container)
        post_time = extract_post_time(maybe_container)

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
        # keep errors visible for debugging but continue scraping other posts
        print("Error parsing a post:", e)
        return None
