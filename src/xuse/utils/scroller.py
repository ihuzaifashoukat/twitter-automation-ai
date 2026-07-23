import logging
from typing import TYPE_CHECKING

from selenium.common.exceptions import JavascriptException

if TYPE_CHECKING:
    # This avoids a runtime import if selenium is not installed when type checking,
    # and helps with potential circular dependencies if WebDriver itself used logging.
    from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__) # Module-level logger

class Scroller:
    """
    A utility class for performing various scrolling operations on a web page
    using a Selenium WebDriver.
    """
    def __init__(self, driver: 'WebDriver'):
        """
        Initializes the Scroller.

        Args:
            driver (WebDriver): The Selenium WebDriver instance.
        """
        self.driver: 'WebDriver' = driver
        self.current_position: int = 0
        self.scroll_count: int = 0
        
        logger.debug("Scroller initialized.")
        self.update_scroll_position() # Get initial position

    def reset(self) -> None:
        """Resets scroll count and re-evaluates current scroll position."""
        logger.debug("Resetting scroller state.")
        self.scroll_count = 0
        self.update_scroll_position() # Refresh current_position to actual browser state

    def scroll_to_top(self) -> bool:
        """
        Scrolls the page to the very top (0, 0).

        Returns:
            bool: True if successful, False otherwise.
        """
        logger.debug("Attempting to scroll to top.")
        try:
            self.driver.execute_script("window.scrollTo(0, 0);")
            self.update_scroll_position()
            logger.info(f"Scrolled to top. New position: {self.current_position}")
            return True
        except JavascriptException as e:
            logger.error(f"Error scrolling to top: {e}")
            return False

    def scroll_to_bottom(self) -> bool:
        """
        Scrolls the page to the very bottom based on current document.body.scrollHeight.

        Returns:
            bool: True if successful, False otherwise.
        """
        logger.debug("Attempting to scroll to bottom.")
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.update_scroll_position()
            logger.info(f"Scrolled to bottom. New position: {self.current_position}")
            return True
        except JavascriptException as e:
            logger.error(f"Error scrolling to bottom: {e}")
            return False

    def scroll_by(self, pixels: int) -> bool:
        """
        Scrolls the page by a specific number of pixels.
        Positive values scroll down, negative values scroll up.

        Args:
            pixels (int): The number of pixels to scroll by.

        Returns:
            bool: True if successful, False otherwise.
        """
        logger.debug(f"Attempting to scroll by {pixels} pixels.")
        try:
            self.driver.execute_script(f"window.scrollBy(0, {pixels});")
            self.update_scroll_position()
            logger.info(f"Scrolled by {pixels}px. New position: {self.current_position}")
            return True
        except JavascriptException as e:
            logger.error(f"Error scrolling by {pixels} pixels: {e}")
            return False

    def update_scroll_position(self) -> None:
        """Updates `self.current_position` with the browser's current window.pageYOffset."""
        try:
            current_offset = self.driver.execute_script("return window.pageYOffset;")
            if current_offset is not None:
                self.current_position = int(current_offset)
            else:
                # This case should be rare, but good to handle.
                logger.warning("window.pageYOffset returned None. Scroll position not updated.")
        except JavascriptException as e:
            logger.warning(f"Could not update scroll position via JavaScript: {e}")
        except TypeError as e: # If current_offset is not convertible to int
            logger.warning(f"Could not convert scroll position to int: {current_offset}. Error: {e}")


    def get_current_scroll_position(self) -> int:
        """
        Fetches and returns the current vertical scroll position (window.pageYOffset).

        Returns:
            int: The current vertical scroll position in pixels.
        """
        self.update_scroll_position()
        return self.current_position

    def get_page_height(self) -> int:
        """
        Returns the total height of the document's body (document.body.scrollHeight).

        Returns:
            int: The total height of the page in pixels. Returns 0 on error.
        """
        try:
            height = self.driver.execute_script("return document.body.scrollHeight;")
            return int(height) if height is not None else 0
        except JavascriptException as e:
            logger.warning(f"Could not get page height: {e}")
            return 0
        except TypeError as e: # If height is not convertible to int
            logger.warning(f"Could not convert page height to int. Error: {e}")
            return 0
            
    def get_window_height(self) -> int:
        """
        Returns the height of the browser window's viewport (window.innerHeight).

        Returns:
            int: The height of the viewport in pixels. Returns 0 on error.
        """
        try:
            height = self.driver.execute_script("return window.innerHeight;")
            return int(height) if height is not None else 0
        except JavascriptException as e:
            logger.warning(f"Could not get window height: {e}")
            return 0
        except TypeError as e: # If height is not convertible to int
            logger.warning(f"Could not convert window height to int. Error: {e}")
            return 0

    def is_at_top(self) -> bool:
        """
        Checks if the page is currently scrolled to the top.

        Returns:
            bool: True if at the top, False otherwise.
        """
        is_top = self.get_current_scroll_position() == 0
        logger.debug(f"Is at top check: {is_top} (Position: {self.current_position})")
        return is_top

    def is_at_bottom(self, threshold_px: int = 10) -> bool:
        """
        Checks if the page is scrolled to the bottom, within a given pixel threshold.
        This is useful for pages with dynamic content loading or slight measurement variations.

        Args:
            threshold_px (int, optional): The tolerance in pixels. Defaults to 10.

        Returns:
            bool: True if at the bottom (within threshold), False otherwise.
        """
        current_pos = self.get_current_scroll_position()
        page_height = self.get_page_height()
        window_height = self.get_window_height()
        
        if page_height == 0: # Avoid issues if page_height couldn't be determined
             logger.warning("Page height is zero, cannot accurately determine if at bottom.")
             # If window_height is also 0, it's likely an uninitialized page.
             # If window_height > 0 but page_height is 0, it's an odd state.
             # Consider it not at bottom if page_height is 0 and window_height > 0.
             return False if window_height > 0 else True # If both 0, effectively at bottom of "nothing"

        # The bottom is reached if current scroll position + window height >= page height
        at_bottom = (current_pos + window_height) >= (page_height - threshold_px)
        logger.debug(
            f"Is at bottom check (threshold {threshold_px}px): {at_bottom} "
            f"(CurrentPos: {current_pos}, WindowH: {window_height}, PageH: {page_height})"
        )
        return at_bottom

    def increment_scroll_count(self) -> None:
        """Increments the internal scroll counter. Useful for tracking scroll attempts."""
        self.scroll_count += 1
        logger.debug(f"Scroll count incremented to: {self.scroll_count}")

    def scroll_page(self, scroll_increment_ratio: float = 0.8) -> bool:
        """
        Scrolls the page down by a fraction of the window height.
        Returns True if scrolling occurred and new content might be loaded,
        False if at the bottom or an error occurred.

        Args:
            scroll_increment_ratio (float): Fraction of window height to scroll by. Default 0.8.
        
        Returns:
            bool: True if scroll position changed, False otherwise (likely at bottom or error).
        """
        logger.debug("Attempting to scroll page down by a portion of window height.")
        last_position = self.get_current_scroll_position()
        
        if self.is_at_bottom(threshold_px=10): # Check if already near bottom
            logger.info("Already at the bottom of the page. No further scroll.")
            return False

        window_height = self.get_window_height()
        if window_height == 0:
            logger.warning("Window height is 0, cannot determine scroll increment. Attempting small scroll.")
            scroll_amount = 500 # Default small scroll
        else:
            scroll_amount = int(window_height * scroll_increment_ratio)
        
        if not self.scroll_by(scroll_amount):
            logger.warning("scroll_by returned False, indicating an error during scrolling.")
            return False # Error during scroll_by

        self.increment_scroll_count()
        new_position = self.get_current_scroll_position()

        if new_position == last_position:
            # If position didn't change, we are likely at the true bottom or stuck.
            # Double check with is_at_bottom as scroll_by might not move if already at max scroll.
            if self.is_at_bottom(threshold_px=10):
                 logger.info(f"Scrolled, but position unchanged ({new_position}px) and confirmed at bottom. End of scroll.")
                 return False
            else:
                 logger.warning(f"Scrolled, but position unchanged ({new_position}px) and NOT at bottom. Possible issue or very short page.")
                 # This could be a stuck page or a page shorter than the scroll increment.
                 # For scraper, this might still mean "no new content via this scroll".
                 return False # Treat as no effective scroll
        
        logger.debug(f"Page scrolled from {last_position}px to {new_position}px.")
        return True


# Example usage (requires a running WebDriver and a webpage loaded):
# if __name__ == '__main__':
#     # This setup is illustrative. You'd need to have Selenium and a WebDriver (e.g., chromedriver) installed.
#     from selenium import webdriver
#     from selenium.webdriver.chrome.service import Service as ChromeService
#     from webdriver_manager.chrome import ChromeDriverManager
    
#     # Basic logger setup for testing this module directly
#     logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     logger.info("Running Scroller direct test...")

#     driver = None
#     try:
#         # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
#         # For a simpler test, assume driver is available or mock it.
#         # This example won't run without a valid driver.
#         # driver.get("https://python.org") # Load a page with scrollbars
#         # time.sleep(2) # Allow page to load

#         # Mock driver for demonstration if actual driver setup is too complex for this snippet
#         class MockDriver:
#             def execute_script(self, script):
#                 logger.debug(f"MockDriver executing: {script}")
#                 if "window.pageYOffset" in script: return getattr(self, "_mock_pos", 0)
#                 if "document.body.scrollHeight" in script: return getattr(self, "_mock_page_h", 2000)
#                 if "window.innerHeight" in script: return getattr(self, "_mock_win_h", 800)
#                 if "window.scrollTo(0, 0)" in script: self._mock_pos = 0
#                 if "window.scrollTo(0, document.body.scrollHeight)" in script: self._mock_pos = getattr(self, "_mock_page_h", 2000) - getattr(self, "_mock_win_h", 800)
#                 if "window.scrollBy" in script:
#                     pixels = int(script.split(',')[1].replace(');','').strip())
#                     self._mock_pos = getattr(self, "_mock_pos", 0) + pixels
#                 return None
#             _mock_pos = 0
#             _mock_page_h = 2000
#             _mock_win_h = 800

#         driver = MockDriver() # Use mock driver
#         scroller = Scroller(driver)

#         logger.info(f"Initial scroll position: {scroller.get_current_scroll_position()}")
#         logger.info(f"Page height: {scroller.get_page_height()}")
#         logger.info(f"Window height: {scroller.get_window_height()}")
#         logger.info(f"Is at top? {scroller.is_at_top()}")
#         logger.info(f"Is at bottom? {scroller.is_at_bottom()}")

#         scroller.scroll_by(200)
#         logger.info(f"Scroll position after scrolling by 200: {scroller.get_current_scroll_position()}")

#         scroller.scroll_to_bottom()
#         logger.info(f"Scroll position after scrolling to bottom: {scroller.get_current_scroll_position()}")
#         logger.info(f"Is at bottom? {scroller.is_at_bottom()}")
        
#         scroller.scroll_to_top()
#         logger.info(f"Scroll position after scrolling to top: {scroller.get_current_scroll_position()}")
#         logger.info(f"Is at top? {scroller.is_at_top()}")

#         scroller.increment_scroll_count()
#         logger.info(f"Scroll count: {scroller.scroll_count}")
#         scroller.reset()
#         logger.info(f"Scroll count after reset: {scroller.scroll_count}")

#     except Exception as e:
#         logger.error(f"An error occurred during Scroller test: {e}", exc_info=True)
#     finally:
#         # if driver and not isinstance(driver, MockDriver):
#         #     driver.quit()
#         logger.info("Scroller direct test finished.")
