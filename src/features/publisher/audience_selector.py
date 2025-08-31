import logging
import time
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys

from data_models import AccountConfig
from utils.selenium_waits import wait_for_any_clickable

logger = logging.getLogger(__name__)


def _find_audience_container(driver):
    """Return the audience container element and a best-effort scrollable node."""
    try:
        # Try HoverCard first (more common in this context)
        hovercard = WebDriverWait(driver, 6).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-testid='HoverCard']"))
        )
        logger.debug("Found HoverCard container")
        return hovercard, hovercard
    except TimeoutException:
        pass

    try:
        dialog = WebDriverWait(driver, 6).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='dialog' and @aria-modal='true']"))
        )
        logger.debug("Found dialog container")
        return dialog, dialog
    except TimeoutException:
        logger.error("No audience container found")
        return None, None


def _scroll_virtualized_list(driver, container):
    """Scroll the virtualized list to load more communities."""
    try:
        scroll_parent = container.find_element(By.XPATH, ".//div[@style[contains(., 'position: absolute')]]/..")
        driver.execute_script("arguments[0].scrollTop += 300;", scroll_parent)
        time.sleep(1)
        return True
    except Exception as e:
        logger.warning(f"Virtualized scroll failed: {e}")
        return False


def _click_element_safely(driver, element) -> bool:
    """Safely click an element with multiple fallback strategies."""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)

        # Use locator from element for clickable wait
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "."))  # fallback to checking element itself
        )

        element.click()
        logger.debug("Successfully clicked with normal click")
        return True
    except ElementClickInterceptedException:
        logger.debug("Normal click intercepted, trying JavaScript click")
        try:
            driver.execute_script("arguments[0].click();", element)
            logger.debug("Successfully clicked with JavaScript")
            return True
        except Exception as e:
            logger.debug(f"JavaScript click failed: {e}")
    except Exception as e:
        logger.debug(f"Normal click failed: {e}")

    # Fallback to ActionChains
    try:
        from selenium.webdriver.common.action_chains import ActionChains
        ActionChains(driver).move_to_element(element).pause(0.2).click().perform()
        logger.debug("Successfully clicked with ActionChains")
        return True
    except Exception as e:
        logger.error(f"All click methods failed: {e}")
        return False



def _find_community_by_name(container, name: str):
    """Find community by name inside audience container."""
    if not name or not name.strip():
        return None

    name_lower = name.strip().lower()
    logger.debug(f"Searching for community: {name_lower}")

    try:
        # Select all virtualized community items
        items = container.find_elements(By.XPATH, ".//div[@role='menuitem']")
        logger.debug(f"Found {len(items)} candidate menu items")

        for item in items:
            try:
                # Look inside for visible text spans
                text_spans = item.find_elements(By.XPATH, ".//span[normalize-space(text())]")
                for span in text_spans:
                    span_text = span.text.strip().lower()
                    if span_text and span_text not in ["members", "everyone", "my communities"]:
                        logger.debug(f"Checking: {span_text}")
                        if name_lower == span_text or name_lower in span_text:
                            logger.info(f"Matched community: {span_text}")
                            return item  # return whole menuitem, not span
            except Exception as e:
                logger.debug(f"Error checking item: {e}")
                continue
    except Exception as e:
        logger.error(f"Error finding community items: {e}")

    return None



def select_community_if_configured(driver, account_config: AccountConfig) -> bool:
    """Enhanced community selection focusing on name-based matching."""
    if not getattr(account_config, "post_to_community", False):
        logger.debug("Community posting not configured.")
        return True
    
    community_name = getattr(account_config, "community_name", None)
    
    if not community_name:
        logger.warning("Community posting enabled but no community name provided.")
        return True

    logger.info(f"Attempting to switch audience to community: '{community_name}'")
    
    # Wait for any overlays to disappear
    try:
        WebDriverWait(driver, 3).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='twc-cc-mask']"))
        )
    except TimeoutException:
        pass

    # Find the search context (layers or global)
    search_context = driver
    try:
        layers = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-testid='layers']"))
        )
        search_context = layers
        logger.debug("Using layers container as search context")
    except TimeoutException:
        logger.debug("Using driver as global search context")

    # Find and click the audience button
    audience_button = wait_for_any_clickable(
        search_context,
        [
            (By.XPATH, ".//button[@aria-label='Choose audience']"),
            (By.XPATH, "//button[@aria-label='Choose audience']"),
            (By.XPATH, ".//button[contains(@aria-label, 'audience')]"),
            (By.XPATH, "//button[contains(@aria-label, 'audience')]"),
            (By.XPATH, ".//button[contains(text(), 'Everyone')]"),  # Additional fallback
        ],
        timeout=10,
    )
    
    if not audience_button:
        logger.error("Audience button not found with any strategy")
        return False

    # Click the audience button
    if not _click_element_safely(driver, audience_button):
        logger.error("Failed to click audience button")
        return False
    
    logger.debug("Successfully clicked audience button")
    time.sleep(2)  # Wait for menu to appear

    # Find the audience container
    audience_container, scrollable = _find_audience_container(driver)
    if not audience_container:
        logger.error("Audience container not found after clicking button")
        return False

    logger.debug("Found audience container, starting community search")

    # Search for the community with scrolling
    selected = False
    max_attempts = 15  # Increased attempts for better coverage
    previous_items_count = 0
    no_change_count = 0
    
    for attempt in range(max_attempts):
        logger.debug(f"Search attempt {attempt + 1}/{max_attempts}")
        
        # Look for the community in currently visible items
        community_element = _find_community_by_name(audience_container, community_name)
        
        if community_element:
            logger.info(f"Found community '{community_name}' on attempt {attempt + 1}")
            
            if _click_element_safely(driver, community_element):
                selected = True
                logger.info(f"Successfully selected community: '{community_name}'")
                break
            else:
                logger.warning(f"Found community '{community_name}' but failed to click")
        
        # Count current items to detect if scrolling is working
        try:
            current_items = len(audience_container.find_elements(
                By.XPATH, ".//div[@role='menuitem']"
            ))
            
            if current_items == previous_items_count:
                no_change_count += 1
                if no_change_count >= 3:
                    logger.warning("No new items loaded after scrolling, may have reached end")
                    break
            else:
                no_change_count = 0
                previous_items_count = current_items
                
        except Exception:
            pass
        
        # Scroll to load more communities
        if attempt < max_attempts - 1:  # Don't scroll on last attempt
            logger.debug("Scrolling to load more communities...")
            if not _scroll_virtualized_list(driver, audience_container):
                logger.warning("Scrolling failed, trying a few more attempts without scroll")

    if not selected:
        logger.error(f"Failed to find and select community: '{community_name}'")
        
        # Log all visible communities for debugging
        try:
            visible_communities = []
            menu_items = audience_container.find_elements(By.XPATH, ".//div[@role='menuitem']")
            for item in menu_items:
                try:
                    spans = item.find_elements(By.XPATH, ".//span[normalize-space(text()) != '']")
                    for span in spans:
                        text = span.text.strip()
                        if text and text.lower() not in ['members', 'everyone', 'my communities']:
                            visible_communities.append(text)
                            break
                except Exception:
                    continue
            
            logger.debug(f"Visible communities found: {visible_communities}")
        except Exception:
            pass
        
        # Close the menu
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        return False

    # Wait for the audience container to close (indicating successful selection)
    try:
        logger.debug("Waiting for audience container to close...")
        WebDriverWait(driver, 8).until(EC.staleness_of(audience_container))
        logger.debug("Audience container closed successfully")
    except TimeoutException:
        logger.warning("Container didn't close as expected, but selection may have succeeded")
        time.sleep(2)

    # Optional verification: check if audience button text updated
    try:
        time.sleep(1)  # Allow UI to update
        updated_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'audience')]")
        button_text = updated_button.text or ""
        
        if community_name.lower() in button_text.lower():
            logger.info("Verified: audience button shows selected community")
        else:
            logger.debug(f"Button text after selection: '{button_text}'")
            
    except Exception:
        logger.debug("Could not verify button text update")

    logger.info(f"Community selection completed successfully: '{community_name}'")
    return selected