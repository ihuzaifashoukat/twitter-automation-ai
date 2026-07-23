import logging
import time
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)


def is_signed_in(driver: WebDriver, timeout_seconds: int = 5) -> bool:
    """Heuristically determine if an X.com session is signed in.

    Checks for elements only visible to logged-in users (compose button), and
    falls back to checking for login link visibility.
    """
    try:
        # Fast path: presence of the SideNav compose button indicates logged in
        WebDriverWait(driver, timeout_seconds).until(
            EC.presence_of_element_located((By.XPATH, "//a[@data-testid='SideNav_NewTweet_Button']"))
        )
        return True
    except Exception:
        pass

    # Negative check: presence of a login link means likely logged out
    try:
        login_links = driver.find_elements(By.XPATH, "//a[@href='/login'] | //a[contains(@href,'login')]")
        if login_links:
            return False
    except Exception:
        pass

    # As a fallback, check for the top app bar which often exists when logged in
    try:
        driver.find_element(By.XPATH, "//*[@data-testid='AppTabBar_More_Menu'] | //*[@data-testid='AppTabBar_Home_Link']")
        return True
    except Exception:
        return False


def wait_for_signed_in(driver: WebDriver, max_wait_seconds: int = 0) -> bool:
    """Optionally wait up to max_wait_seconds for a signed-in state.

    Returns True when signed in is detected, False if timeout or still logged out.
    """
    if max_wait_seconds <= 0:
        return is_signed_in(driver, timeout_seconds=3)

    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        if is_signed_in(driver, timeout_seconds=2):
            return True
        time.sleep(1.0)
    return False

