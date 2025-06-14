"""Debug helper module for browser automation."""
import time
import keyboard
from typing import Optional, Dict, Any
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

class BrowserDebugger:
    """Helper class for debugging browser automation."""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.last_inspect_time = 0
        self.inspect_cooldown = 1.0  # seconds between inspections
        
    def print_page_info(self, max_source_length: int = 5000):
        """Print current page information."""
        current_time = time.time()
        if current_time - self.last_inspect_time < self.inspect_cooldown:
            return
            
        self.last_inspect_time = current_time
        
        print("\n=== Page Information ===")
        print(f"URL: {self.driver.current_url}")
        print("\n=== Page Source Preview ===")
        print(self.driver.page_source[:max_source_length] + "...")
        print("\n=== Form Elements ===")
        self.print_form_elements()
        
    def print_form_elements(self):
        """Print information about form elements."""
        try:
            # Find all input elements
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            if inputs:
                print("\nInput Elements:")
                for input_elem in inputs:
                    self.print_element_info(input_elem)
            
            # Find all form elements
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            if forms:
                print("\nForm Elements:")
                for form in forms:
                    self.print_element_info(form)
                    
        except Exception as e:
            print(f"Error printing form elements: {str(e)}")
            
    def print_element_info(self, element: WebElement):
        """Print detailed information about an element."""
        try:
            print("\nElement Details:")
            print(f"Tag: {element.tag_name}")
            print(f"ID: {element.get_attribute('id')}")
            print(f"Name: {element.get_attribute('name')}")
            print(f"Type: {element.get_attribute('type')}")
            print(f"Class: {element.get_attribute('class')}")
            print(f"Placeholder: {element.get_attribute('placeholder')}")
            print(f"Value: {element.get_attribute('value')}")
            print(f"Aria Label: {element.get_attribute('aria-label')}")
            print(f"Data Test ID: {element.get_attribute('data-testid')}")
            print("---")
        except Exception as e:
            print(f"Error printing element info: {str(e)}")
            
    def wait_for_hotkey(self, duration: Optional[int] = None) -> bool:
        """Wait for hotkey input with optional duration.
        
        Returns:
            bool: True if 'c' was pressed, False if 'q' was pressed or duration expired
        """
        print("\n=== Debug Controls ===")
        print("Press 'i' to inspect page")
        print("Press 'c' to continue")
        print("Press 'q' to quit")
        if duration:
            print(f"Will timeout after {duration} seconds")
        
        start_time = time.time()
        while True:
            if duration and time.time() - start_time > duration:
                print("\nDuration expired")
                return False
                
            if keyboard.is_pressed('i'):
                self.print_page_info()
                time.sleep(0.5)  # Prevent multiple prints
            elif keyboard.is_pressed('c'):
                print("\nContinuing...")
                return True
            elif keyboard.is_pressed('q'):
                print("\nQuitting...")
                return False
                
            time.sleep(0.1)
            
    def find_element_by_attributes(self, 
                                 element_type: str = "input",
                                 attributes: Optional[Dict[str, str]] = None) -> Optional[WebElement]:
        """Find an element by its attributes.
        
        Args:
            element_type: Type of element to find (e.g., "input", "form")
            attributes: Dictionary of attribute names and values to match
            
        Returns:
            Optional[WebElement]: Found element or None
        """
        try:
            elements = self.driver.find_elements(By.TAG_NAME, element_type)
            if not attributes:
                return elements[0] if elements else None
                
            for element in elements:
                matches = True
                for attr_name, attr_value in attributes.items():
                    if element.get_attribute(attr_name) != attr_value:
                        matches = False
                        break
                if matches:
                    return element
                    
            return None
        except Exception as e:
            print(f"Error finding element: {str(e)}")
            return None 
