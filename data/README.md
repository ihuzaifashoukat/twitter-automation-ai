Data Guide

Overview

- This folder includes dummy data to help you configure proxies and account cookies.
- Files here are safe examples; replace values with your real data before use.

Cookies

- Example: `data/cookies/dummy_cookies_example.json`
  - Format: an array of cookie objects compatible with Selenium `add_cookie`.
  - Common fields: `name`, `value`, `domain` (e.g., `.x.com`), `path`, `expires` (unix timestamp), `httpOnly`, `secure`, `sameSite`.
  - Usage: Point an account’s `cookie_file_path` in `config/accounts.json` to your cookie file.
    - Example: `"cookie_file_path": "config/tech_innovator_001_cookies.json"`
    - You can copy the dummy file into `config/` and rename, or update the path directly to `data/cookies/...`.

Proxies

- Pools are defined in `config/settings.json` under `browser_settings.proxy_pools`.
  - Supports environment variable interpolation, e.g. `http://user:${RESI_PASS}@eu1.proxy.local:8080`.
  - Set env vars before running: `export RESI_PASS="your_password"`.
- Pool strategy is controlled by `browser_settings.proxy_pool_strategy`: `hash` (stable per-account) or `round_robin` (rotates with state).
- Round-robin state is stored in `data/proxy_pools_state.json`.
  - This file maps pool names to the next index to pick.

Files included

- `data/cookies/dummy_cookies_example.json`: Two sample cookies for `x.com` (`.x.com`).
- `data/proxy_pools_state.json`: Sample state with counters for pools.
- `data/proxies/dummy_proxies.json`: Example proxy URLs you can adapt into your settings’ proxy pools.

Notes

- Do not commit real cookies or passwords. Keep secrets in environment variables or local untracked files.
- If you change `proxy_pool_state_file` path in settings, update or copy `data/proxy_pools_state.json` accordingly.

