Preset Library

Overview

- This folder contains beginner-friendly presets for `config/settings.json` and `config/accounts.json`.
- Copy a preset into the `config/` directory and rename as needed:
  - Settings: copy one file from `presets/settings/` to `config/settings.json`.
  - Accounts: copy one file from `presets/accounts/` to `config/accounts.json`.
- Replace placeholders like `YOUR_*_KEY_HERE`, `REPLACE_WITH_COMMUNITY_ID`, and cookie file paths.

How to use

- Pick a settings preset:
  - `beginner-defaults.json`: simple defaults (Firefox headless, no proxies).
  - `beginner-chrome-undetected.json`: Chrome with undetected-chromedriver + stealth.
  - `beginner-proxies-hash.json`: Adds proxy pools with stable hash selection.
  - `beginner-proxies-roundrobin.json`: Adds proxy pools with round-robin rotation and state file.
- Pick an accounts preset:
  - `growth.json`: Proactive growth using reposts/decisioning.
  - `brand_safe.json`: Conservative, on-topic engagement.
  - `replies_first.json`: Focused on support/FAQ style replies.
  - `engagement_light.json`: Minimal, safe engagement.
  - `community_posting.json`: Example of posting to a specific community.

Important

- Competitor profiles are required for rewrite-based posting. Ensure each account has `competitor_profiles_override` populated (or `competitor_profiles` in the model) so the scraper has sources to pull content from for rewriting and posting to either communities or personal profiles.

Apply the preset

- Settings:
  - cp presets/settings/beginner-defaults.json config/settings.json
- Accounts:
  - cp presets/accounts/growth.json config/accounts.json

Notes

- All presets are self-contained but you can merge settings across files.
- Make sure cookie files exist at the given paths or adjust `cookie_file_path`.
- For proxies, ensure environment variables referenced in proxy URLs (e.g., `${RESI_PASS}`) are set.
- See `data/README.md` for dummy cookies (`data/cookies/dummy_cookies_example.json`) and proxy examples/state (`data/proxies/dummy_proxies.json`, `data/proxy_pools_state.json`).
