import sys
import os
from pathlib import Path

def test_imports():
    """Test Selenium imports and print diagnostic info."""
    print("Python path:")
    for p in sys.path:
        print(f"  {p}")
    
    print("\nTrying to import selenium...")
    try:
        import selenium
        print(f"✅ selenium found at: {selenium.__file__}")
        
        print("\nTrying to import webdriver...")
        from selenium import webdriver
        print(f"✅ webdriver found at: {webdriver.__file__}")
        
        print("\nTrying to import chrome service...")
        from selenium.webdriver.chrome.service import Service
        print("✅ chrome.service.Service imported successfully")
        
        print("\nChecking chrome directory contents:")
        chrome_dir = Path(selenium.__file__).parent / "webdriver" / "chrome"
        if chrome_dir.exists():
            print(f"✅ chrome directory exists at: {chrome_dir}")
            for item in chrome_dir.iterdir():
                print(f"  - {item.name}")
        else:
            print(f"❌ chrome directory not found at: {chrome_dir}")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_imports() 
