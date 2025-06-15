"""Services for scraping chats via Selenium."""

import logging
import time
from selenium.webdriver.common.by import By

logger = logging.getLogger('chatgpt_bridge')


class ChatScraperService:
    """Retrieve chat titles and links from the ChatGPT sidebar."""

    def __init__(self, driver_manager, exclusions=None, reverse_order=False):
        self.driver_manager = driver_manager
        self.driver = driver_manager.driver
        self.exclusions = exclusions if exclusions else []
        self.reverse_order = reverse_order

    def get_all_chats(self) -> list:
        """Return all chat titles and links available in the sidebar."""
        logger.info("🔎 Scraping all chats from sidebar...")
        try:
            time.sleep(2)
            chat_elements = self.driver.find_elements(
                "xpath", "//a[contains(@class, 'group') and contains(@href, '/c/')]")
            if not chat_elements:
                logger.warning("⚠️ No chats found in the sidebar.")
                return []
            chats = []
            for el in chat_elements:
                title = el.text.strip() or "Untitled"
                link = el.get_attribute("href")
                if not link:
                    logger.warning("⚠️ Chat '%s' has no link, skipping.", title)
                    continue
                chats.append({"title": title, "link": link})
            logger.info("✅ Retrieved %s chats from sidebar.", len(chats))
            return chats
        except Exception as exc:
            logger.error("❌ Error while scraping chats: %s", exc)
            return []

    def get_filtered_chats(self) -> list:
        """Filter chats using exclusions and optional reverse order."""
        all_chats = self.get_all_chats()
        logger.info("🔍 Filtering %s chats...", len(all_chats))
        filtered = [c for c in all_chats if c["title"] not in self.exclusions]
        logger.info("✅ %s chats after exclusion filter.", len(filtered))
        if self.reverse_order:
            filtered.reverse()
            logger.info("🔄 Reversed chat order as requested.")
        return filtered

    def validate_login(self) -> bool:
        """Return True if user is logged in based on sidebar presence."""
        logger.info("🔐 Validating OpenAI chat login status...")
        try:
            sidebar = self.driver.find_element(
                "xpath", "//nav[contains(@class,'flex h-full')]"
            )
            if sidebar:
                logger.info("✅ User is logged in.")
                return True
        except Exception:
            logger.warning("⚠️ User is NOT logged in or sidebar is missing.")
        return False

    def manual_login_flow(self):
        """Prompt user to log in manually via the browser."""
        logger.info("🛂 Manual login flow initiated. Waiting for user login...")
        self.driver.get("https://chat.openai.com/auth/login")
        while not self.validate_login():
            time.sleep(5)
            logger.info("🔄 Waiting for login...")
        logger.info("✅ Login detected! Proceeding with chat scraping.")

    def load_chat(self, chat_link: str):
        """Navigate to a specific chat by link."""
        try:
            self.driver.get(chat_link)
            time.sleep(2)
            logger.info("✅ Loaded chat: %s", chat_link)
        except Exception as exc:
            logger.error("❌ Failed to load chat %s: %s", chat_link, exc)
            raise

    def archive_chat(self, chat: dict):
        """Archive a chat after processing."""
        try:
            archive_btn = self.driver.find_element("xpath", "//button[contains(@class, 'archive')]")
            if archive_btn:
                archive_btn.click()
                time.sleep(1)
                logger.info("✅ Archived chat: %s", chat.get('title', 'Untitled'))
        except Exception as exc:
            logger.warning("⚠️ Failed to archive chat: %s", exc)

    def shutdown(self):
        """Clean shutdown of the scraper."""
        logger.info("🛑 Shutting down ChatScraperService...")
        if self.driver_manager:
            self.driver_manager.quit()

__all__ = ["ChatScraperService"]
