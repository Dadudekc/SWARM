"""Login handling functionality for the stealth browser."""
import logging
import time
from typing import Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException

class LoginHandler:
    """Handles login-related operations."""
    
    def __init__(self, driver, config):
        self.logger = logging.getLogger("LoginHandler")
        self.driver = driver
        self.config = config

    def click_initial_login(self) -> bool:
        """Click the initial 'Log in to try it' button."""
        try:
            # Try the specific selector first
            login_button = self.find_element(self.config['codex_selectors']['initial_login_button'])
            if login_button:
                self.logger.info("Found initial login button by selector, clicking...")
                # Try to click the parent button element
                parent_button = login_button.find_element(By.XPATH, "./..")
                parent_button.click()
                return True
            else:
                # Fallback to text-based search
                login_button = self.find_element_by_text("Log in to try it")
                if login_button:
                    self.logger.info("Found initial login button by text, clicking...")
                    login_button.click()
                    return True
                else:
                    raise Exception("Could not find initial login button")
        except Exception as e:
            self.logger.error(f"Error during initial login click: {str(e)}")
            return False

    def click_secondary_login(self) -> bool:
        """Click the secondary login button after the first one."""
        try:
            # Wait a moment for the page to update
            time.sleep(2)
            
            # Print current URL for debugging
            self.logger.info(f"Current URL before clicking secondary login: {self.driver.current_url}")
            
            # Try multiple selectors for the secondary login button
            selectors = [
                'button[type="submit"]',
                'button:contains("Continue")',
                'button:contains("Log in")',
                'button[data-testid="login-button"]',
                'button[data-testid="submit-button"]',
                'button._root_625o4_51._primary_625o4_86',
                'button[class*="primary"]',
                'button[class*="submit"]'
            ]
            
            # First try to find by selector
            for selector in selectors:
                try:
                    login_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if login_button:
                        self.logger.info(f"Found secondary login button with selector: {selector}")
                        login_button.click()
                        time.sleep(2)  # Wait for click to take effect
                        self.logger.info(f"Current URL after clicking: {self.driver.current_url}")
                        return True
                except:
                    continue
            
            # If no button found by selector, try to find by text
            button_texts = ["Continue", "Log in", "Sign in", "Submit"]
            for text in button_texts:
                try:
                    button = self.find_element_by_text(text, "button")
                    if button:
                        self.logger.info(f"Found secondary login button with text: {text}")
                        button.click()
                        time.sleep(2)
                        self.logger.info(f"Current URL after clicking: {self.driver.current_url}")
                        return True
                except:
                    continue
            
            # If still no button found, try to find any clickable button
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        self.logger.info("Found a clickable button, attempting to click...")
                        button.click()
                        time.sleep(2)
                        self.logger.info(f"Current URL after clicking: {self.driver.current_url}")
                        return True
            except:
                pass
            
            raise Exception("Could not find secondary login button")
            
        except Exception as e:
            self.logger.error(f"Error during secondary login click: {str(e)}")
            return False

    def wait_for_email_input(self) -> Optional[WebElement]:
        """Wait for and return the email input field."""
        try:
            # Try the exact selector first
            try:
                email_input = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '#\\:r1\\:-email'))
                )
                if email_input:
                    self.logger.info("Found email input with exact selector")
                    return email_input
            except:
                pass
            
            # Fallback to other selectors
            email_selectors = [
                'input[type="email"][name="email"][placeholder="Email address"]',
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder="Email address"]'
            ]
            
            for selector in email_selectors:
                try:
                    email_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if email_input:
                        self.logger.info(f"Found email input with selector: {selector}")
                        return email_input
                except:
                    continue
            
            return None
        except Exception as e:
            self.logger.error(f"Error waiting for email input: {str(e)}")
            return None

    def wait_for_continue_button(self) -> Optional[WebElement]:
        """Wait for and return the continue button."""
        try:
            # Try multiple selectors for the continue button
            button_selectors = [
                'button._root_625o4_51._primary_625o4_86[type="submit"][name="intent"][value="email"]',
                'button[type="submit"][name="intent"][value="email"]',
                'button._root_625o4_51._primary_625o4_86',
                'button:contains("Continue")'
            ]
            
            for selector in button_selectors:
                try:
                    button = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if button:
                        self.logger.info(f"Found continue button with selector: {selector}")
                        return button
                except:
                    continue
            
            return None
        except Exception as e:
            self.logger.error(f"Error waiting for continue button: {str(e)}")
            return None

    def wait_for_password_input(self) -> Optional[WebElement]:
        """Wait for and return the password input field."""
        try:
            # Try multiple selectors for password
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder="Password"]',
                'input[aria-label="Password"]',
                'input[data-testid="password-input"]',
                'input[data-testid="login-password"]',
                'input[data-testid="password"]'
            ]
            
            for selector in password_selectors:
                try:
                    password_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if password_input:
                        self.logger.info(f"Found password input with selector: {selector}")
                        return password_input
                except:
                    continue
            
            return None
        except Exception as e:
            self.logger.error(f"Error waiting for password input: {str(e)}")
            return None

    def input_email(self, email: str) -> bool:
        """Input email and submit."""
        try:
            email_input = self.wait_for_email_input()
            if not email_input:
                raise Exception("Could not find email input field")
            
            # Clear and input email
            email_input.clear()
            email_input.send_keys(email)
            self.logger.info("Email input successful")
            
            # Try to find and click the continue button
            continue_button = self.wait_for_continue_button()
            if continue_button:
                self.logger.info("Found continue button, clicking...")
                continue_button.click()
            else:
                # Fallback to Enter key
                self.logger.info("Continue button not found, using Enter key")
                email_input.send_keys(Keys.RETURN)
            
            # Wait a moment for the page to update
            time.sleep(2)
            
            return True
        except Exception as e:
            self.logger.error(f"Error inputting email: {str(e)}")
            return False

    def input_password(self, password: str) -> bool:
        """Input password and submit."""
        try:
            password_input = self.wait_for_password_input()
            if not password_input:
                raise Exception("Could not find password input field")
            
            # Clear and input password
            password_input.clear()
            password_input.send_keys(password)
            self.logger.info("Password input successful")
            
            # Submit password
            password_input.send_keys(Keys.RETURN)
            self.logger.info("Password submitted")
            
            return True
        except Exception as e:
            self.logger.error(f"Error inputting password: {str(e)}")
            return False

    def find_element(self, selector: str, by: str = By.CSS_SELECTOR) -> Optional[WebElement]:
        """Return a visible element matching selector."""
        try:
            return WebDriverWait(self.driver, self.config['element_wait']).until(
                EC.presence_of_element_located((by, selector))
            )
        except:
            return None

    def find_element_by_text(self, text: str, tag: str = "*") -> Optional[WebElement]:
        """Find element containing exact text."""
        try:
            elements = self.driver.find_elements(By.TAG_NAME, tag)
            for element in elements:
                if element.text.strip() == text:
                    return element
            return None
        except Exception as e:
            self.logger.error(f"Error finding element by text: {str(e)}")
            return None

    def wait_for_verification_code(self) -> bool:
        """Wait for the verification code input field."""
        try:
            # Try multiple selectors for verification code input
            code_selectors = [
                'input[type="text"][name="code"]',
                'input[placeholder*="code"]',
                'input[placeholder*="Code"]',
                'input[aria-label*="code"]',
                'input[aria-label*="Code"]',
                'input[data-testid="verification-code"]'
            ]
            
            for selector in code_selectors:
                try:
                    code_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if code_input:
                        self.logger.info(f"Found verification code input with selector: {selector}")
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            self.logger.error(f"Error waiting for verification code input: {str(e)}")
            return False

    def check_login_status(self) -> bool:
        """Check if we're successfully logged in."""
        try:
            # Wait for any of these elements that indicate successful login
            success_indicators = [
                'div[role="textbox"]',  # Codex editor
                'div[data-testid="codex-editor"]',
                'div[class*="editor"]',
                'div[class*="CodexEditor"]',
                'div[class*="chat"]',
                'div[class*="Chat"]'
            ]
            
            for selector in success_indicators:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if element:
                        self.logger.info(f"Found login success indicator: {selector}")
                        return True
                except:
                    continue
            
            # Also check URL for success
            current_url = self.driver.current_url
            if '/codex' in current_url and 'auth' not in current_url:
                self.logger.info("URL indicates successful login")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error checking login status: {str(e)}")
            return False

    def handle_verification_code(self) -> bool:
        """Handle the verification code input process."""
        try:
            if not self.wait_for_verification_code():
                self.logger.error("Could not find verification code input")
                return False
            
            self.logger.info("Waiting for manual verification code input...")
            # Get code from terminal input
            code = input("\nPlease enter the verification code: ")
            
            # Find and input the code
            code_selectors = [
                'input[type="text"][name="code"]',
                'input[placeholder*="code"]',
                'input[placeholder*="Code"]',
                'input[aria-label*="code"]',
                'input[aria-label*="Code"]',
                'input[data-testid="verification-code"]'
            ]
            
            for selector in code_selectors:
                try:
                    code_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if code_input:
                        code_input.clear()
                        code_input.send_keys(code)
                        code_input.send_keys(Keys.RETURN)
                        self.logger.info("Verification code submitted")
                        break
                except:
                    continue
            
            # Wait for code processing
            time.sleep(5)
            
            # Verify login by checking both URLs
            return self.verify_login()
            
        except Exception as e:
            self.logger.error(f"Error handling verification code: {str(e)}")
            return False

    def verify_login(self) -> bool:
        """Verify login by checking both ChatGPT and Codex URLs."""
        try:
            # First check ChatGPT main page
            self.logger.info("Verifying login on ChatGPT main page...")
            self.driver.get("https://chatgpt.com/")
            time.sleep(5)  # Wait for page load
            
            # Check for ChatGPT logo
            logo_selectors = [
                'a[href="/"] svg[viewBox="0 0 45 12"]',  # Logo SVG
                'a[href="/"] svg',  # Any SVG in the logo link
                'div.draggable.no-draggable-children svg',  # Logo in header
                'div.sticky.top-0 svg'  # Logo in sticky header
            ]
            
            logo_found = False
            for selector in logo_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if element:
                        self.logger.info("Found ChatGPT logo - main page verified")
                        logo_found = True
                        break
                except:
                    continue
            
            if not logo_found:
                self.logger.error("Could not find ChatGPT logo on main page")
                return False
            
            # Then check Codex page
            self.logger.info("Verifying login on Codex page...")
            self.driver.get("https://chatgpt.com/codex")
            time.sleep(5)  # Wait for page load
            
            # Check for Codex-specific indicators
            codex_indicators = [
                'div[role="textbox"]',  # Codex editor
                'div[data-testid="codex-editor"]',
                'div[class*="editor"]',
                'div[class*="CodexEditor"]'
            ]
            
            for selector in codex_indicators:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if element:
                        self.logger.info("Successfully verified login on Codex page")
                        return True
                except:
                    continue
            
            # Also check URL for success
            current_url = self.driver.current_url
            if '/codex' in current_url and 'auth' not in current_url:
                self.logger.info("URL indicates successful login")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error verifying login: {str(e)}")
            return False

    def input_codex_message(self, message: str) -> bool:
        """Input a message into the Codex input area."""
        try:
            # Try multiple selectors for the input area
            input_selectors = [
                'div[contenteditable="true"].ProseMirror',
                'div[data-placeholder="Describe a task"]',
                'div[class*="ProseMirror"]',
                'div[class*="prosemirror-parent"]',
                'div[class*="text-token-text-primary"]',
                'div[role="textbox"]'
            ]
            
            for selector in input_selectors:
                try:
                    input_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if input_element:
                        self.logger.info(f"Found input area with selector: {selector}")
                        
                        # Clear existing content
                        input_element.clear()
                        
                        # Input the message
                        input_element.send_keys(message)
                        self.logger.info("Message input successful")
                        
                        # Submit the message (press Enter)
                        input_element.send_keys(Keys.RETURN)
                        self.logger.info("Message submitted")
                        
                        return True
                except:
                    continue
            
            # If no input element found by selector, try finding by XPath
            try:
                input_element = self.driver.find_element(By.XPATH, 
                    "//div[contains(@class, 'ProseMirror') and @contenteditable='true']")
                if input_element:
                    self.logger.info("Found input area by XPath")
                    input_element.clear()
                    input_element.send_keys(message)
                    input_element.send_keys(Keys.RETURN)
                    return True
            except:
                pass
            
            self.logger.error("Could not find Codex input area")
            return False
            
        except Exception as e:
            self.logger.error(f"Error inputting message: {str(e)}")
            return False

    def wait_for_codex_response(self, timeout: int = 30) -> bool:
        """Wait for Codex to generate a response."""
        try:
            # Try multiple selectors for the response area
            response_selectors = [
                'div[class*="markdown"]',
                'div[class*="response"]',
                'div[class*="code-block"]',
                'div[class*="CodexResponse"]'
            ]
            
            for selector in response_selectors:
                try:
                    response = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if response:
                        self.logger.info(f"Found response with selector: {selector}")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error waiting for response: {str(e)}")
            return False 