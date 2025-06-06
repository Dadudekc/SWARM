"""Main script for running the stealth browser."""
import logging
import time
from .stealth_browser import StealthBrowser
from .debug_helper import BrowserDebugger
from .config import DEFAULT_CONFIG

def keep_browser_open(browser, duration: int = 300):  # Increased to 5 minutes
    """Keep the browser open for the specified duration."""
    print("\nBrowser will stay open for 5 minutes.")
    print("Press 'c' to continue to the next step")
    print("Press 'q' to quit")
    print("Press 'i' to print current page info")
    
    start_time = time.time()
    while time.time() - start_time < duration:
        if keyboard.is_pressed('q'):
            print("\nQuitting...")
            return False
        elif keyboard.is_pressed('c'):
            print("\nContinuing to next step...")
            return True
        elif keyboard.is_pressed('i'):
            print("\nCurrent URL:", browser.driver.current_url)
            print("\nPage source preview:")
            print(browser.driver.page_source[:1000] + "...")  # Print first 1000 chars
            time.sleep(0.5)  # Prevent multiple prints
        time.sleep(0.1)
    return False

def handle_login_flow(browser, debugger):
    """Handle the manual login flow."""
    print("Navigating to Codex...")
    browser.navigate_to()
    
    # Initial wait to see the page
    print("\nWaiting 5 seconds to see the initial page...")
    time.sleep(5)
    
    print("Clicking initial login button...")
    if not browser.login_handler.click_initial_login():
        print("Failed to click initial login button")
        print("Current URL:", browser.driver.current_url)
        return False
    
    print("Initial login button clicked successfully")
    
    # Wait to see the intermediate page
    print("\nWaiting 5 seconds to see the intermediate page...")
    time.sleep(5)
    
    print("Clicking secondary login button...")
    if not browser.login_handler.click_secondary_login():
        print("Failed to click secondary login button")
        print("Current URL:", browser.driver.current_url)
        return False
    
    print("Secondary login button clicked successfully")
    
    # Wait for email input
    print("\nWaiting for email input...")
    if not browser.login_handler.wait_for_email_input():
        print("Failed to find email input")
        print("Current URL:", browser.driver.current_url)
        return False
    
    print("\nEmail input found!")
    print("\nAnalyzing form elements...")
    debugger.print_form_elements()
    
    # Get credentials from config
    email = browser.config['credentials']['email']
    password = browser.config['credentials']['password']
    
    print(f"\nUsing email: {email}")
    
    # Input email
    print("\nAttempting to input email...")
    if not browser.login_handler.input_email(email):
        print("Failed to input email")
        return False
    
    print("Email submitted successfully")
    print("\nWaiting for password field...")
    
    # Wait for password input
    if not browser.login_handler.wait_for_password_input():
        print("Failed to find password input")
        print("Current URL:", browser.driver.current_url)
        return False
    
    print("\nPassword field found!")
    print("\nAnalyzing form elements...")
    debugger.print_form_elements()
    
    # Input password
    print("\nAttempting to input password...")
    if not browser.login_handler.input_password(password):
        print("Failed to input password")
        return False
    
    print("Password submitted successfully")
    
    # Wait for verification code input
    print("\nWaiting for verification code input...")
    if browser.login_handler.wait_for_verification_code():
        print("\nVerification code input found!")
        print("Please enter the verification code in the browser...")
        
        # Handle verification code input
        if not browser.login_handler.handle_verification_code():
            print("Failed to complete verification")
            return False
        
        print("Verification completed")
        
        # Save cookies after successful verification
        print("\nSaving cookies...")
        if browser.cookie_manager.save_cookies():
            print("Cookies saved successfully!")
        else:
            print("Failed to save cookies")
    else:
        print("No verification code input found, checking login status...")
    
    # Check if we're logged in
    if browser.login_handler.check_login_status():
        print("\nSuccessfully logged in!")
        return True
    else:
        print("\nLogin status check failed")
        return False

def try_cookie_login(browser, debugger) -> bool:
    """Attempt to login using saved cookies."""
    print("\nAttempting cookie-based login...")
    
    # First try loading cookies
    if not browser.cookie_manager.load_cookies():
        print("No cookies found or failed to load cookies")
        return False
    
    print("Cookies loaded, verifying login...")
    
    # Navigate to ChatGPT main page
    browser.driver.get("https://chatgpt.com/")
    time.sleep(5)  # Wait for page load
    
    # Check if we're logged in
    if browser.login_handler.verify_login():
        print("Successfully logged in with cookies!")
        return True
    
    print("Cookie login failed, cookies may be expired")
    return False

def send_codex_message(browser, debugger):
    """Send a message to Codex and wait for response."""
    print("\nEnter your message for Codex (or press Enter to skip):")
    message = input().strip()
    
    if not message:
        print("No message entered, skipping...")
        return
    
    print(f"\nSending message: {message}")
    if browser.login_handler.input_codex_message(message):
        print("Message sent successfully!")
        print("Waiting for Codex response...")
        
        if browser.login_handler.wait_for_codex_response():
            print("Response received!")
        else:
            print("No response received within timeout period")
    else:
        print("Failed to send message")

def main():
    """Run the stealth browser with cookie-based login."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Use the full DEFAULT_CONFIG
    browser = StealthBrowser(DEFAULT_CONFIG)
    
    try:
        print("Starting browser...")
        browser.start()
        debugger = BrowserDebugger(browser.driver)
        
        # Try cookie-based login first
        if try_cookie_login(browser, debugger):
            print("\nCookie login successful! You can now:")
            print("1. Press 'c' to continue to Codex")
            print("2. Press 'q' to quit")
            print("3. Press 'i' to inspect the page")
            print("4. Press 'm' to send a message to Codex")
            
            # Wait for user input
            if debugger.wait_for_hotkey(duration=300):  # 5 minutes
                # If user pressed 'c', navigate to Codex
                print("\nNavigating to Codex...")
                browser.driver.get("https://chatgpt.com/codex")
                time.sleep(5)
                
                while True:
                    print("\nCodex is ready! You can:")
                    print("1. Press 'm' to send a message")
                    print("2. Press 'i' to inspect the page")
                    print("3. Press 'q' to quit")
                    
                    if keyboard.is_pressed('q'):
                        print("\nQuitting...")
                        break
                    elif keyboard.is_pressed('m'):
                        send_codex_message(browser, debugger)
                    elif keyboard.is_pressed('i'):
                        debugger.print_page_info()
                    time.sleep(0.1)
            return
        
        print("\nCookie login failed, proceeding with normal login...")
        if handle_login_flow(browser, debugger):
            print("\nLogin process completed successfully!")
            print("You can now close the browser or press 'q' to quit.")
            debugger.wait_for_hotkey(duration=300)  # 5 minutes
        
    except Exception as e:
        print(f"Browser error: {str(e)}")
        if browser.driver:
            print("Current URL:", browser.driver.current_url)
    finally:
        print("Closing browser...")
        browser.stop()

if __name__ == "__main__":
    main() 