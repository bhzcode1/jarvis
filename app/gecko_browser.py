"""
Gecko Browser Module - Firefox Automation via Selenium

Provides voice-controlled browser automation through the Gecko engine.
Handles navigation, interaction, data extraction, and autonomous tasks.
"""

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
import time
import json


class GeckoBrowser:
    """Firefox browser automation for voice-controlled web interactions."""
    
    def __init__(self, headless=False):
        """
        Initialize the Gecko browser with Selenium WebDriver.
        
        Args:
            headless (bool): Run browser invisibly if True
        """
        options = Options()
        
        if headless:
            options.add_argument("--headless")
        
        # Make it look like a real human browser
        options.set_preference(
            "general.useragent.override",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0)"
        )
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        
        self.driver = webdriver.Firefox(
            service=Service(GeckoDriverManager().install()),
            options=options
        )
        self.wait = WebDriverWait(self.driver, 10)
        print("🦊 Gecko browser ready.")
    
    # ─────────────────────────────────────────────────────────
    # NAVIGATION
    # ─────────────────────────────────────────────────────────
    
    def open(self, url):
        """Open a URL in the browser."""
        if not url.startswith("http"):
            url = "https://" + url
        self.driver.get(url)
        return f"Opened {url}"
    
    def search(self, query):
        """Search Google for a query."""
        self.driver.get(f"https://www.google.com/search?q={query}")
        return f"Searching for {query}"
    
    def go_back(self):
        """Navigate to the previous page."""
        self.driver.back()
        return "Going back."
    
    def go_forward(self):
        """Navigate to the next page."""
        self.driver.forward()
        return "Going forward."
    
    def refresh(self):
        """Refresh the current page."""
        self.driver.refresh()
        return "Page refreshed."
    
    def close_tab(self):
        """Close the current tab."""
        self.driver.close()
        return "Tab closed."
    
    def new_tab(self, url=""):
        """Open a new tab."""
        self.driver.execute_script(f"window.open('{url}', '_blank');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        return "New tab opened."
    
    # ─────────────────────────────────────────────────────────
    # PAGE INTERACTION
    # ─────────────────────────────────────────────────────────
    
    def click(self, selector):
        """Click an element by CSS selector."""
        try:
            element = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            return f"Clicked {selector}"
        except Exception as e:
            return f"Could not click element: {str(e)}"
    
    def type_text(self, selector, text):
        """Type text into an input field."""
        try:
            element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            element.clear()
            element.send_keys(text)
            return f"Typed: {text}"
        except Exception as e:
            return f"Could not type: {str(e)}"
    
    def press_enter(self, selector):
        """Press Enter in an input field."""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            element.send_keys(Keys.RETURN)
            time.sleep(1)  # Wait for page load
            return "Enter pressed."
        except Exception as e:
            return f"Could not press enter: {str(e)}"
    
    def scroll_down(self, amount=500):
        """Scroll down the page."""
        self.driver.execute_script(f"window.scrollBy(0, {amount});")
        return f"Scrolled down {amount}px."
    
    def scroll_up(self, amount=500):
        """Scroll up the page."""
        self.driver.execute_script(f"window.scrollBy(0, -{amount});")
        return f"Scrolled up {amount}px."
    
    def scroll_to_bottom(self):
        """Scroll to the bottom of the page."""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        return "Scrolled to bottom."
    
    def scroll_to_top(self):
        """Scroll to the top of the page."""
        self.driver.execute_script("window.scrollTo(0, 0);")
        return "Scrolled to top."
    
    # ─────────────────────────────────────────────────────────
    # DATA EXTRACTION
    # ─────────────────────────────────────────────────────────
    
    def get_page_text(self):
        """Extract all text from the current page."""
        try:
            return self.driver.find_element(By.TAG_NAME, "body").text
        except:
            return ""
    
    def get_title(self):
        """Get the page title."""
        return self.driver.title
    
    def get_url(self):
        """Get the current URL."""
        return self.driver.current_url
    
    def find_text(self, selector):
        """Find text by CSS selector."""
        try:
            return self.driver.find_element(By.CSS_SELECTOR, selector).text
        except:
            return None
    
    def find_all_text(self, selector):
        """Find all matching elements and extract their text."""
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            return [e.text for e in elements if e.text.strip()]
        except:
            return []
    
    def take_screenshot(self, path="browser_screenshot.png"):
        """Take a screenshot of the current page."""
        self.driver.save_screenshot(path)
        return f"Screenshot saved to {path}"
    
    def get_all_links(self):
        """Get all links on the current page."""
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            return [
                {
                    "text": link.text,
                    "href": link.get_attribute("href")
                } for link in links if link.text.strip()
            ]
        except:
            return []
    
    # ─────────────────────────────────────────────────────────
    # SMART EXTRACTION (for LLM processing)
    # ─────────────────────────────────────────────────────────
    
    def extract_data(self, selector, limit=10):
        """Extract data from multiple elements."""
        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
        return [e.text for e in elements[:limit] if e.text.strip()]
    
    def get_page_info(self):
        """Get comprehensive page information."""
        return {
            "title": self.get_title(),
            "url": self.get_url(),
            "text": self.get_page_text()[:2000],  # First 2000 chars
            "links": self.get_all_links()[:10]   # First 10 links
        }
    
    def close(self):
        """Close the browser."""
        try:
            self.driver.quit()
            print("🦊 Gecko browser closed.")
        except:
            pass


# ───────────────────────────────────────────────────────────────
# AUTONOMOUS BROWSER AGENT
# ───────────────────────────────────────────────────────────────

def browser_autonomy(goal: str, ask_llm_func, gecko: GeckoBrowser = None) -> str:
    """
    Execute multi-step browser tasks autonomously.
    
    Args:
        goal: High-level goal (e.g., "Search Amazon for wireless earbuds and get the top 3 prices")
        ask_llm_func: LLM function to break goal into steps
        gecko: GeckoBrowser instance (creates new if None)
    
    Returns:
        str: Result summary
    """
    close_at_end = gecko is None
    gecko = gecko or GeckoBrowser(headless=False)
    
    try:
        # Ask LLM to break down the goal into steps
        steps_prompt = f"""
        You are controlling a Firefox browser via Selenium.
        Goal: {goal}
        
        Return a JSON list of steps. Each step must have:
        - action: one of: open, search, click, type, scroll, extract, wait, read
        - selector: CSS selector (for click, type, extract - use empty string if N/A)
        - value: the value to use for that action
        
        Example:
        [
          {{"action": "open", "selector": "", "value": "amazon.com"}},
          {{"action": "type", "selector": "input#twotabsearchtextbox", "value": "wireless earbuds"}},
          {{"action": "click", "selector": "input[type='submit']", "value": ""}},
          {{"action": "scroll", "selector": "", "value": "500"}},
          {{"action": "extract", "selector": "span.a-price-whole", "value": ""}}
        ]
        
        Return ONLY the JSON array, no explanation.
        """
        
        steps_json = ask_llm_func(steps_prompt)
        
        # Parse the JSON response
        try:
            steps = json.loads(steps_json)
        except:
            # If JSON parsing fails, return error
            return f"Could not parse browser steps: {steps_json}"
        
        results = []
        
        for i, step in enumerate(steps):
            action = step.get("action", "").lower()
            selector = step.get("selector", "")
            value = step.get("value", "")
            
            try:
                if action == "open":
                    gecko.open(value)
                elif action == "search":
                    gecko.search(value)
                elif action == "click":
                    gecko.click(selector)
                elif action == "type":
                    gecko.type_text(selector, value)
                elif action == "scroll":
                    gecko.scroll_down(int(value) if value else 500)
                elif action == "extract":
                    data = gecko.extract_data(selector, limit=5)
                    results.extend(data)
                elif action == "read":
                    text = gecko.get_page_text()
                    results.append(text[:1000])
                elif action == "wait":
                    time.sleep(min(float(value) if value else 1, 5))
                
                time.sleep(0.8)  # Human-like delay
            except Exception as e:
                print(f"Step {i} error: {str(e)}")
        
        # Format results for voice output
        result_text = " ".join(str(r) for r in results[:5])  # First 5 results
        return result_text if result_text else "Task completed."
    
    except Exception as e:
        return f"Browser agent error: {str(e)}"
    
    finally:
        if close_at_end:
            gecko.close()
