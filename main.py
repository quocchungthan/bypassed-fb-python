from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os
from fb_tool import FacebookGroupScraper
from dotenv import load_dotenv
from html_tool import HtmlSanitizer
from telegram_processor import TelegramNotifier
from fb_group_collector import FacebookGroupCollector
import random



# Load environment variables from .env file
load_dotenv()

# Load credentials from environment variables for safety
FB_USERNAME = os.getenv("FB_USERNAME", "your_email_or_phone")
FB_PASSWORD = os.getenv("FB_PASSWORD", "your_password")
FB_KEYWORDS = [k.strip() for k in os.getenv("FB_KEYWORDS", "keyword1 ,keyword2").split(",") if k.strip()]
LIMIT_GROUP_COUNT = int(os.getenv("LIMIT_GROUP_COUNT", "0"))  # 0 = no limit
profile_path = os.getenv("CHROME_PROFILE_PATH", "invalid")
LOOP_PER = int(os.getenv("LOOP_PER", "0"))  # 0 = run once; otherwise every X minutes

print("Using Chrome profile:", profile_path)
print("Loop interval (minutes):", LOOP_PER)


def run_scraper_cycle():
    """Perform one full scraping + sanitizing + telegram notify cycle."""
    # Launch Chrome
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_experimental_option(
        "prefs",
        {
            "intl.accept_languages": "vi-VN,vi",
            "translate_whitelists": {},
            "translate.enabled": False,
        },
    )

    driver = webdriver.Chrome(options=options)
    scraper = FacebookGroupScraper(driver=driver, manage_driver=False)

    try:
        driver.get("https://www.facebook.com/")
        time.sleep(5)

        collector = FacebookGroupCollector(driver)
        urls = collector.get_all_group_urls(max_scrolls=55)
        if LIMIT_GROUP_COUNT > 0:
            random.shuffle(urls)  # Shuffle the list in place
            urls = urls[:LIMIT_GROUP_COUNT]  # Take the first N items after shuffle

        for url in urls:
            print(f"[INFO] Capturing posts from: {url}")
            scraper.capture_group_posts_html(
                group_url=url,
                css_selector="div.x1yztbdb.x1n2onr6.xh8yej3.x1ja2u2z",
                max_scrolls=10,
            )
            time.sleep(3)

        # Step 2: sanitize HTML → plain text
        sanitizer = HtmlSanitizer(logs_root="logs")
        sanitizer.run()

        # Step 3: send to Telegram
        notifier = TelegramNotifier(logs_root="logs", driver=driver)
        notifier.run()

    finally:
        driver.quit()
        print("[INFO] Browser closed.\n")


if LOOP_PER <= 0:
    print("[RUN] Single cycle mode (no looping).")
    run_scraper_cycle()
else:
    print(f"[RUN] Continuous mode — will repeat every {LOOP_PER} minutes.")
    while True:
        start_time = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n=== New Cycle at {start_time} ===")
        run_scraper_cycle()
        print(f"[SLEEP] Waiting {LOOP_PER} minutes before next cycle...")
        time.sleep(LOOP_PER * 60)
