import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import InvalidArgumentException

logger = logging.getLogger(__name__)


def load_cookies_from_file(candidate_path: str, config_dir: Path, project_root: Path) -> Optional[List[Dict[str, Any]]]:
    """Load cookies JSON from config dir, project root, or absolute path."""
    config_dir_cookie_path = config_dir / candidate_path
    project_root_cookie_path = project_root / candidate_path

    resolved: Optional[Path] = None
    if config_dir_cookie_path.is_file():
        resolved = config_dir_cookie_path
        logger.debug(f"Found cookie file relative to config directory: {resolved}")
    elif project_root_cookie_path.is_file():
        resolved = project_root_cookie_path
        logger.debug(f"Found cookie file relative to project root: {resolved}")
    else:
        abs_path = Path(candidate_path)
        if abs_path.is_absolute() and abs_path.is_file():
            resolved = abs_path
            logger.debug(f"Found cookie file at absolute path: {resolved}")

    if not resolved:
        logger.error(f"Cookie file not found at '{candidate_path}' (checked config dir, project root, and absolute path).")
        return None

    try:
        with resolved.open('r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from cookie file {resolved}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading cookies from file {resolved}: {e}")
        return None


def apply_cookies(driver: WebDriver, cookies: List[Dict[str, Any]], cookie_domain_url: Optional[str]) -> None:
    if cookie_domain_url:
        try:
            driver.get(cookie_domain_url)
        except Exception as e:
            logger.warning(f"Failed navigating to cookie domain {cookie_domain_url} before adding cookies: {e}")

    for cookie_dict in cookies:
        selenium_cookie: Dict[str, Any] = {}
        for key, value in cookie_dict.items():
            if key == 'expires':
                selenium_cookie['expiry'] = value
            elif key == 'httpOnly':
                selenium_cookie['httpOnly'] = value
            elif key in ['name', 'value', 'path', 'domain', 'secure', 'sameSite']:
                selenium_cookie[key] = value

        if 'name' in selenium_cookie and 'value' in selenium_cookie:
            try:
                driver.add_cookie(selenium_cookie)
            except InvalidArgumentException as iae:
                logger.warning(
                    f"Could not add cookie {selenium_cookie.get('name')} (often domain mismatch or expiry format): {iae}"
                )
            except Exception as e:
                logger.warning(
                    f"Could not add cookie {selenium_cookie.get('name')}: {e}"
                )

    if cookie_domain_url:
        try:
            driver.refresh()
        except Exception:
            pass

