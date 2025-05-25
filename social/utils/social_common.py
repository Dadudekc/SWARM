import os
import time
from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)

from dreamos.social.log_writer import logger, LogLevel
from social.constants.platform_constants import (
    MAX_RETRIES,
    RETRY_DELAY,
    DEFAULT_TIMEOUT,
    TWITTER_MAX_IMAGES,
    TWITTER_MAX_VIDEO_SIZE,
    TWITTER_SUPPORTED_IMAGE_FORMATS,
    TWITTER_SUPPORTED_VIDEO_FORMATS,
    REDDIT_MAX_IMAGES,
    REDDIT_MAX_VIDEO_SIZE,
    REDDIT_SUPPORTED_IMAGE_FORMATS,
    REDDIT_SUPPORTED_VIDEO_FORMATS,
    FACEBOOK_MAX_IMAGES,
    FACEBOOK_MAX_VIDEO_SIZE,
    FACEBOOK_SUPPORTED_IMAGE_FORMATS,
    FACEBOOK_SUPPORTED_VIDEO_FORMATS,
    INSTAGRAM_MAX_IMAGES,
    INSTAGRAM_MAX_VIDEO_SIZE,
    INSTAGRAM_SUPPORTED_IMAGE_FORMATS,
    INSTAGRAM_SUPPORTED_VIDEO_FORMATS,
    LINKEDIN_MAX_IMAGES,
    LINKEDIN_MAX_VIDEO_SIZE,
    LINKEDIN_SUPPORTED_IMAGE_FORMATS,
    LINKEDIN_SUPPORTED_VIDEO_FORMATS,
    STOCKTWITS_MAX_IMAGES,
    STOCKTWITS_MAX_VIDEO_SIZE,
    STOCKTWITS_SUPPORTED_IMAGE_FORMATS,
    STOCKTWITS_SUPPORTED_VIDEO_FORMATS,
    MEDIA_BUTTON_XPATHS,
    FILE_INPUT_XPATHS
)

class SocialMediaUtils:
    """Common utilities for social media platform strategies."""
    
    # Platform configuration cache
    _platform_configs = {
        "twitter": {
            "max_images": TWITTER_MAX_IMAGES,
            "max_video_size": TWITTER_MAX_VIDEO_SIZE,
            "supported_image_formats": TWITTER_SUPPORTED_IMAGE_FORMATS,
            "supported_video_formats": TWITTER_SUPPORTED_VIDEO_FORMATS
        },
        "reddit": {
            "max_images": REDDIT_MAX_IMAGES,
            "max_video_size": REDDIT_MAX_VIDEO_SIZE,
            "supported_image_formats": REDDIT_SUPPORTED_IMAGE_FORMATS,
            "supported_video_formats": REDDIT_SUPPORTED_VIDEO_FORMATS
        },
        "facebook": {
            "max_images": FACEBOOK_MAX_IMAGES,
            "max_video_size": FACEBOOK_MAX_VIDEO_SIZE,
            "supported_image_formats": FACEBOOK_SUPPORTED_IMAGE_FORMATS,
            "supported_video_formats": FACEBOOK_SUPPORTED_VIDEO_FORMATS
        },
        "instagram": {
            "max_images": INSTAGRAM_MAX_IMAGES,
            "max_video_size": INSTAGRAM_MAX_VIDEO_SIZE,
            "supported_image_formats": INSTAGRAM_SUPPORTED_IMAGE_FORMATS,
            "supported_video_formats": INSTAGRAM_SUPPORTED_VIDEO_FORMATS
        },
        "linkedin": {
            "max_images": LINKEDIN_MAX_IMAGES,
            "max_video_size": LINKEDIN_MAX_VIDEO_SIZE,
            "supported_image_formats": LINKEDIN_SUPPORTED_IMAGE_FORMATS,
            "supported_video_formats": LINKEDIN_SUPPORTED_VIDEO_FORMATS
        },
        "stocktwits": {
            "max_images": STOCKTWITS_MAX_IMAGES,
            "max_video_size": STOCKTWITS_MAX_VIDEO_SIZE,
            "supported_image_formats": STOCKTWITS_SUPPORTED_IMAGE_FORMATS,
            "supported_video_formats": STOCKTWITS_SUPPORTED_VIDEO_FORMATS
        }
    }
    
    def __init__(self, driver, config: dict, platform: str):
        self.driver = driver
        self.config = config
        self.platform = platform
        self.screenshot_dir = os.path.join(os.getcwd(), "social", "debug", "screenshots")
        self.media_dir = config.get(f"{platform}_media_dir", "media")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.media_dir, exist_ok=True)
        self.logger = logger
        
        # Initialize platform config
        self._platform_config = self._platform_configs.get(platform, {
            "max_images": 1,
            "max_video_size": 100 * 1024 * 1024,  # 100MB default
            "supported_image_formats": {".jpg", ".jpeg", ".png"},
            "supported_video_formats": {".mp4"}
        })
    
    def take_screenshot(self, context: str) -> Optional[str]:
        """Take a screenshot for debugging purposes."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.platform}_{context}_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            self.driver.save_screenshot(filepath)
            logger.info(f"[{self.platform}] Screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"[{self.platform}] Failed to take screenshot: {str(e)}")
            return None
    
    def retry_click(self, element, max_attempts: int = MAX_RETRIES, delay: int = RETRY_DELAY) -> bool:
        """Attempt to click an element with retries."""
        for attempt in range(max_attempts):
            try:
                element.click()
                return True
            except (ElementClickInterceptedException, StaleElementReferenceException) as e:
                if attempt == max_attempts - 1:
                    logger.error(f"[{self.platform}] Failed to click element after {max_attempts} attempts: {str(e)}")
                    return False
                time.sleep(delay)
                continue
        return False
    
    def validate_media_file(self, filepath: str, max_size_mb: int = 20) -> bool:
        """Validate media file for upload."""
        if not os.path.exists(filepath):
            logger.error(f"[{self.platform}] Media file not found: {filepath}")
            return False
            
        file_size = os.path.getsize(filepath)
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            logger.error(f"[{self.platform}] Media file too large: {file_size} bytes (max: {max_size_bytes} bytes)")
            return False
            
        return True
    
    def wait_for_element(self, by: By, value: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[Any]:
        """Wait for an element to be present and return it."""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logger.error(f"[{self.platform}] Timeout waiting for element: {value}")
            return None
    
    def wait_for_clickable(self, by: By, value: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[Any]:
        """Wait for an element to be clickable and return it."""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            logger.error(f"[{self.platform}] Timeout waiting for clickable element: {value}")
            return None
    
    def format_post_content(self, content: str, max_length: Optional[int] = None) -> str:
        """Format post content with optional length limit."""
        if max_length and len(content) > max_length:
            content = content[:max_length-3] + "..."
        return content
    
    def create_media_post_content(self, text: str, media_files: List[str]) -> Dict[str, Any]:
        """Create structured content for media posts."""
        return {
            "text": text,
            "media_files": [os.path.abspath(f) for f in media_files],
            "timestamp": datetime.now().isoformat(),
            "platform": self.platform
        }
    
    def handle_upload_error(self, error: Exception, context: str) -> bool:
        """Handle media upload errors with consistent logging and screenshots."""
        self._log_error(context, str(error))
        return False
    
    def verify_post_success(self, expected_url_pattern: str, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Verify post success by checking URL pattern."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: expected_url_pattern in driver.current_url
            )
            return True
        except TimeoutException:
            logger.error(f"[{self.platform}] Post verification failed - URL pattern not found: {expected_url_pattern}")
            self.take_screenshot("post_verification_failed")
            return False
    
    def extract_comment_data(self, element: Any) -> Optional[Dict[str, Any]]:
        """Extract structured data from a comment element."""
        try:
            return {
                "author": element.find_element(By.XPATH, ".//a[@data-testid='comment_author']").text,
                "content": element.find_element(By.XPATH, ".//div[@data-testid='comment-content']").text,
                "score": element.find_element(By.XPATH, ".//span[@data-testid='vote-score']").text,
                "timestamp": datetime.now().isoformat()
            }
        except NoSuchElementException:
            return None
    
    def validate_media(self, media_paths: List[str], is_video: bool = False) -> bool:
        """Validate media files for upload."""
        if not media_paths:
            return True
            
        if is_video:
            if len(media_paths) > 1:
                self._log_error("media_validation", "Cannot upload multiple videos in one post")
                return False
            filepath = media_paths[0]
            if not os.path.splitext(filepath)[1].lower() in self._get_supported_video_formats():
                self._log_error("media_validation", f"Unsupported video format: {filepath}")
                return False
            if not self.validate_media_file(filepath, max_size_mb=self._get_max_video_size()):
                return False
        else:
            if len(media_paths) > self._get_max_images():
                self._log_error("media_validation", f"Cannot upload more than {self._get_max_images()} images")
                return False
            for filepath in media_paths:
                if not os.path.splitext(filepath)[1].lower() in self._get_supported_image_formats():
                    self._log_error("media_validation", f"Unsupported image format: {filepath}")
                    return False
                if not self.validate_media_file(filepath):
                    return False
                    
        return True
    
    def upload_media(self, media_paths: List[str], is_video: bool = False) -> bool:
        """Upload media files to post with parallel processing and progress tracking."""
        if not media_paths:
            return True

        try:
            # Validate all files first
            if not self.validate_media(media_paths, is_video):
                return False

            # Find and click media upload button
            media_button = self.wait_for_clickable(
                By.XPATH, MEDIA_BUTTON_XPATHS.get(self.platform, "//input[@type='file']")
            )
            if not media_button or not self.retry_click(media_button):
                raise ElementClickInterceptedException("Failed to click media upload button")

            # For videos, upload sequentially to avoid browser issues
            if is_video:
                return self._upload_video(media_paths[0])

            # For images, upload in parallel batches
            return self._upload_images_parallel(media_paths)

        except Exception as e:
            self._log_error("media_upload", str(e))
            return False

    def _upload_video(self, video_path: str) -> bool:
        """Upload a single video file with progress tracking."""
        try:
            file_input = self.wait_for_element(
                By.XPATH, FILE_INPUT_XPATHS.get(self.platform, "//input[@type='file']")
            )
            if not file_input:
                raise TimeoutException("File input not found")

            # Start upload
            self.logger.write_log(
                platform=self.platform,
                status="info",
                tags=["media_upload"],
                message=f"Starting video upload: {os.path.basename(video_path)}",
                level=LogLevel.INFO
            )

            file_input.send_keys(os.path.abspath(video_path))

            # Wait for upload completion
            if not self._wait_for_upload_completion():
                return False

            self.logger.write_log(
                platform=self.platform,
                status="success",
                tags=["media_upload"],
                message=f"Video upload completed: {os.path.basename(video_path)}",
                level=LogLevel.INFO
            )
            return True

        except Exception as e:
            self._log_error("video_upload", str(e))
            return False

    def _upload_images_parallel(self, image_paths: List[str], batch_size: int = 3) -> bool:
        """Upload multiple images in parallel batches."""
        try:
            # Split images into batches
            batches = [image_paths[i:i + batch_size] for i in range(0, len(image_paths), batch_size)]
            
            for batch_idx, batch in enumerate(batches, 1):
                self.logger.write_log(
                    platform=self.platform,
                    status="info",
                    tags=["media_upload"],
                    message=f"Uploading batch {batch_idx}/{len(batches)} ({len(batch)} images)",
                    level=LogLevel.INFO
                )

                # Upload batch in parallel
                with ThreadPoolExecutor(max_workers=batch_size) as executor:
                    futures = []
                    for image_path in batch:
                        future = executor.submit(self._upload_single_image, image_path)
                        futures.append(future)

                    # Wait for all uploads in batch to complete
                    for future in as_completed(futures):
                        if not future.result():
                            return False

                # Wait between batches to avoid overwhelming the browser
                if batch_idx < len(batches):
                    time.sleep(2)

            return True

        except Exception as e:
            self._log_error("parallel_upload", str(e))
            return False

    def _upload_single_image(self, image_path: str) -> bool:
        """Upload a single image file."""
        try:
            file_input = self.wait_for_element(
                By.XPATH, FILE_INPUT_XPATHS.get(self.platform, "//input[@type='file']")
            )
            if not file_input:
                raise TimeoutException("File input not found")

            file_input.send_keys(os.path.abspath(image_path))
            time.sleep(1)  # Brief pause for browser to process
            return True

        except Exception as e:
            self._log_error("single_image_upload", f"Failed to upload {os.path.basename(image_path)}: {str(e)}")
            return False

    def _wait_for_upload_completion(self, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Wait for media upload to complete."""
        try:
            # Look for upload progress indicator
            progress_indicator = self.wait_for_element(
                By.XPATH, "//div[contains(@class, 'upload-progress')]",
                timeout=timeout
            )
            
            if progress_indicator:
                # Wait for progress to complete
                WebDriverWait(self.driver, timeout).until_not(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'upload-progress')]"))
                )
            
            # Wait for any processing indicators
            processing_indicators = [
                "//div[contains(@class, 'processing')]",
                "//div[contains(@class, 'loading')]",
                "//div[contains(@class, 'spinner')]"
            ]
            
            for indicator in processing_indicators:
                try:
                    WebDriverWait(self.driver, 5).until_not(
                        EC.presence_of_element_located((By.XPATH, indicator))
                    )
                except TimeoutException:
                    continue

            return True

        except TimeoutException:
            self._log_error("upload_wait", "Timeout waiting for upload completion")
            return False
        except Exception as e:
            self._log_error("upload_wait", str(e))
            return False

    def _get_upload_progress(self) -> Tuple[bool, Optional[float]]:
        """Get current upload progress if available."""
        try:
            progress_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'upload-progress')]")
            if progress_element:
                progress_text = progress_element.text
                if '%' in progress_text:
                    progress = float(progress_text.strip('%'))
                    return True, progress
            return False, None
        except NoSuchElementException:
            return False, None

    def _get_max_images(self) -> int:
        """Get platform-specific max images."""
        return self._platform_config["max_images"]
    
    def _get_max_video_size(self) -> int:
        """Get platform-specific max video size in MB."""
        return self._platform_config["max_video_size"]
    
    def _get_supported_image_formats(self) -> List[str]:
        """Get platform-specific supported image formats."""
        return self._platform_config["supported_image_formats"]
    
    def _get_supported_video_formats(self) -> List[str]:
        """Get platform-specific supported video formats."""
        return self._platform_config["supported_video_formats"]

    def _log_error(self, context: str, error_msg: str) -> None:
        """Centralized error logging with consistent format."""
        self.logger.write_log(
            platform=self.platform,
            status="error",
            tags=[context],
            error=error_msg,
            level=LogLevel.ERROR
        )
        self.take_screenshot(f"{context}_error") 