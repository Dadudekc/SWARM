"""Stealth OpenAI / ChatGPT automation client built on **undetected_chromedriver**.

The implementation is adapted from standalone snippet contributed by the ops
team and integrated into Dream.OS code-style:

* Uses project-wide logging rather than external ``setup_logging`` util.
* All filesystem paths are resolved relative to repository root.
* Designed to be instantiated by :pyclass:`DriverManager` when the
  ``CHATGPT_STEALTH=1`` environment variable is set.
"""
from __future__ import annotations

import logging
import os
import pickle
import shutil
import time
from pathlib import Path
from typing import Optional

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger("openai_client")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _safe_mkdir(path: str | Path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Main client
# ---------------------------------------------------------------------------


class OpenAIClient:  # noqa: D101 – external API wrapper
    CHATGPT_URL: str = "https://chat.openai.com/"
    _TEST_URL: str = "https://chatgpt.com/g/g-67a4c53f01648191bdf31ab8591e84e7-tbow-tactic-generator"

    def __init__(self, profile_dir: str | os.PathLike, *, headless: bool = False, driver_path: str | None = None):
        self.profile_dir = str(profile_dir)
        self.headless = headless
        self.driver_path = driver_path

        # Paths ---------------------------------------------------------
        self.cookie_dir = Path("cookies")
        self.cookie_file = self.cookie_dir / "openai.pkl"
        self.cached_driver = Path("drivers/chromedriver.exe")

        # Build driver instance ----------------------------------------
        self.driver = self._create_driver()

    # ------------------------------------------------------------------
    # Internal: driver initialisation
    # ------------------------------------------------------------------

    def _create_driver(self):
        """Return a configured *undetected_chromedriver* instance."""
        try:
            from webdriver_manager.chrome import ChromeDriverManager  # type: ignore
        except ImportError as exc:  # pragma: no cover
            logger.error("webdriver_manager not installed – pip install webdriver_manager")
            raise

        driver_path: Optional[str]
        if self.driver_path and Path(self.driver_path).is_file():
            driver_path = self.driver_path
            logger.info("🔎 Using provided ChromeDriver → %s", driver_path)
        elif self.cached_driver.is_file():
            driver_path = str(self.cached_driver)
            logger.info("🔎 Using cached ChromeDriver → %s", driver_path)
        else:
            logger.warning("No driver found – downloading via webdriver_manager …")
            dl_path = ChromeDriverManager().install()
            driver_path = dl_path
            # copy executable for next run
            self.cached_driver.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(dl_path, self.cached_driver)
            logger.info("✅ ChromeDriver cached → %s", self.cached_driver)

        # Chrome options ----------------------------------------------
        opts = uc.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument(f"--user-data-dir={self.profile_dir}")
        if self.headless:
            opts.add_argument("--headless=new")
        # monkey-patch for Selenium≥4.20 compatibility
        opts.headless = self.headless  # type: ignore[attr-defined]

        driver = uc.Chrome(options=opts, driver_executable_path=driver_path)
        logger.info("🕵️ undetected_chromedriver started (headless=%s)", self.headless)
        return driver

    # ------------------------------------------------------------------
    # Cookie helpers
    # ------------------------------------------------------------------

    def _save_cookies(self) -> None:
        self.cookie_dir.mkdir(exist_ok=True)
        with self.cookie_file.open("wb") as fh:
            pickle.dump(self.driver.get_cookies(), fh)
        logger.info("💾 Cookies saved → %s", self.cookie_file)

    def _load_cookies(self) -> bool:
        if not self.cookie_file.is_file():
            return False
        try:
            self.driver.get(self.CHATGPT_URL)
            time.sleep(2)
            with self.cookie_file.open("rb") as fh:
                for ck in pickle.load(fh):
                    ck.pop("sameSite", None)
                    self.driver.add_cookie(ck)
            self.driver.refresh(); time.sleep(5)
            return True
        except Exception as exc:
            logger.warning("Failed to inject cookies: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def _is_logged_in(self) -> bool:
        self.driver.get(self._TEST_URL)
        time.sleep(3)
        ok = self.driver.current_url.startswith("https://chatgpt.com/g/")
        if ok:
            self.driver.get(self.CHATGPT_URL); time.sleep(2)
        return ok

    def login_openai(self) -> bool:
        """Ensure we're authenticated – cookies → manual login fallback."""
        if self._is_logged_in():
            logger.debug("Already logged in.")
            return True
        if self._load_cookies() and self._is_logged_in():
            logger.info("✅ Logged in via cookie restore.")
            return True

        # Manual flow --------------------------------------------------
        logger.warning("🔐 Manual login required… opening login page.")
        self.driver.get("https://chat.openai.com/auth/login")
        time.sleep(5)
        input("👉 Complete login (CAPTCHA, 2FA, …) then press ENTER …")
        if self._is_logged_in():
            self._save_cookies()
            return True
        logger.error("Login still not detected – aborting.")
        return False

    # ------------------------------------------------------------------
    # Prompt / response helpers
    # ------------------------------------------------------------------

    def send_prompt(self, prompt: str, *, timeout: int = 120) -> str:
        logger.info("Sending prompt to ChatGPT…")
        self.driver.get(self.CHATGPT_URL)

        wait = WebDriverWait(self.driver, 15)
        input_div = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ProseMirror[contenteditable='true']"))
        )
        input_div.click()
        for ch in prompt:
            input_div.send_keys(ch)
            time.sleep(0.04)
        input_div.send_keys(Keys.RETURN)
        logger.debug("Prompt submitted – waiting for full response…")
        return self._collect_response(timeout)

    def _collect_response(self, timeout: int = 120) -> str:
        start = time.time()
        captured = ""
        while time.time() - start < timeout:
            time.sleep(3)
            try:
                msgs = self.driver.find_elements(By.CSS_SELECTOR, ".markdown.prose.w-full.break-words")
                if msgs:
                    latest = msgs[-1].text
                    if latest != captured:
                        captured = latest
                    else:
                        break
                cont = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue generating')]")
                if cont:
                    cont[0].click()
            except Exception as exc:
                logger.debug("Polling error: %s", exc)
        return captured

    # ------------------------------------------------------------------
    # Public convenience
    # ------------------------------------------------------------------

    def prompt(self, prompt: str, *, timeout: int = 120) -> str:  # noqa: D401
        if not self.login_openai():
            logger.error("Cannot send prompt – not authenticated.")
            return ""
        return self.send_prompt(prompt, timeout=timeout)

    def shutdown(self) -> None:  # noqa: D401
        try:
            self.driver.quit()
        except Exception as exc:  # pragma: no cover
            logger.debug("Driver shutdown error: %s", exc) 