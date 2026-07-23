# Best Practices

Operational guidance for running x-use (formerly `twitter-automation-ai`) safely and effectively. This document covers the current v2.0 codebase — Python 3.10+, Selenium + LLM pipelines, run via the `x-use` CLI (`x-use run`; the legacy `python src/main.py` shim still works), configured through JSON files in `config/`. Features from the roadmap that are not yet shipped are explicitly marked as planned.

## 1. Account Safety & Rate Limiting

X aggressively profiles automation. The single most effective protection is patience: low action volume, human-scale delays, and content filters that skip marginal engagements.

**Keep the conservative defaults.** The shipped `config/settings.json` uses:

- `min_delay_between_actions_seconds: 60` / `max_delay_between_actions_seconds: 180` — randomized waits between actions.
- `response_interval_seconds: 300` — base pacing between processing cycles.
- Per-run caps: `max_posts_per_competitor_run: 1`, `max_replies_per_keyword_run: 2`, `max_likes_per_run: 5`, `max_curated_posts_per_run: 1`.
- `max_tweets_per_keyword_scrape: 15` — bounded scraping per keyword.

The presets in `presets/accounts/` show sensible profiles. `engagement_light.json` and `brand_safe.json` widen delays to 120–300 seconds and cap replies at 1–2 and likes at 2–3 per run. Even the most aggressive preset, `growth.json`, stays at 90–240 second delays with 2 reposts per run. If you edit these numbers, move them up, not down.

**Use recency filters.** `reply_only_to_recent_tweets_hours: 24` (in `action_config` or a per-account `action_config_override`) prevents replying to stale tweets — necro-replies are a classic bot signal and get reported. The community pipeline has the analogous `community_reply_only_recent_tweets_hours`.

**Why aggressive settings get accounts flagged.** X correlates action frequency, action-to-browse ratio, IP reputation, and fingerprint consistency. A fresh account liking 50 tweets in 10 minutes from a datacenter IP is trivially detectable. Detection usually escalates: captcha challenges, then temporary action blocks, then shadow restrictions, then suspension. By the time you notice, the account is already scored.

**Warm up new accounts.** For the first 1–2 weeks on a new or newly-automated account:

- Start from `presets/accounts/engagement_light.json` (likes and one reply per run, no reposts).
- Run once or twice per day, not continuously.
- Keep `avoid_replying_to_own_tweets: true` and relevance filters enabled so the account only touches genuinely on-topic content.
- Gradually raise caps over weeks, watching `data/metrics/<account_id>.json` for error spikes.

## 2. Cookies & Credentials

**How cookies are stored.** Each account entry in `config/accounts.json` points at a JSON cookie file via `cookie_file_path` (or embeds a `cookies` array directly). The file is a Selenium-compatible array of cookie objects for `x.com`; a safe dummy lives at `data/cookies/dummy_cookies_example.json`. For a working login the file must contain valid `auth_token` and `ct0` cookies matching `browser_settings.cookie_domain_url` (default `https://x.com`). If cookies are expired, set `browser_settings.login_wait_seconds` (e.g. 60–120) and complete a manual login once; the run continues after a signed-in state is detected.

**Never commit real cookies.** An `auth_token` cookie is a full session credential — anyone holding it can act as your account. Only the dummy examples under `data/cookies/` belong in git. Keep real cookie files in local, untracked paths and reference them from `cookie_file_path`.

**Keep `config/accounts.json` local.** The tracked copy in this repo contains only placeholder data. As part of the v2.0 relaunch (Phase 1), the repo moves to an `accounts.example.json` pattern: the example file is committed, your real `config/accounts.json` is gitignored. Until then, treat your populated `accounts.json` as a secret — never push it to a fork or paste it into an issue.

**API keys go in `config/settings.json` — not `.env` (yet).** The engine reads LLM keys exclusively from the `api_keys` block in `config/settings.json`; placeholder values (`YOUR_GEMINI_API_KEY`, etc.) are detected and rejected, so a provider left on a placeholder is simply never initialized. Environment variables are **not** read for LLM keys today — the only env-var mechanism in the engine is `${VAR}` interpolation inside proxy strings (see Section 3). Keep your populated `settings.json` local and never commit real keys. Loading keys from `.env`/environment variables is planned as part of the v2.0 packaging work.

**If a key or cookie leaks, rotate it immediately.** Revoke the API key at the provider, generate a new one, and update `config/settings.json`. For a leaked cookie, log the account out of all sessions on X (which invalidates `auth_token`), log in again, and re-export fresh cookies. Assume anything that touched a public commit is compromised — deleting the commit does not un-leak it.

## 3. Proxies

**One account, one stable IP.** X checks IP consistency per session. The most reliable heuristic is one dedicated IP (or sticky residential session) per account, kept stable across runs. Never route many accounts through one exit IP, and avoid switching an established account's IP without need.

**Per-account proxies.** Set `proxy` on the account object in `config/accounts.json` (`http://user:pass@host:port` or `socks5://host:port`). It overrides the global `browser_settings.proxy`. Chrome applies it via `--proxy-server`; Firefox via profile preferences (proxy auth prompts are not auto-handled, so embed credentials in the URL).

**Pools and rotation.** Define named pools under `browser_settings.proxy_pools` and reference them with `"proxy": "pool:<name>"` (e.g. `pool:residential_eu`). Two strategies via `proxy_pool_strategy`:

- `hash` — stable mapping from `account_id` to a pool entry. **Preferred**: each account keeps the same IP run after run, matching the one-account-per-IP heuristic. The presets `beginner-proxies-hash.json` and `beginner-proxies-roundrobin.json` show both setups.
- `round_robin` — rotates through the pool across runs, persisting counters in `proxy_pool_state_file` (default `data/proxy_pools_state.json`). Use only for scraping-heavy work where session identity matters less.

**Residential vs datacenter.** Residential IPs with sticky sessions are strongly recommended for any account that posts, replies, or likes — datacenter ranges are widely fingerprinted and score poorly with X. Datacenter proxies are acceptable for cost-sensitive, read-only scraping. See `data/proxies/dummy_proxies.json` for URL formats.

**Keep proxy credentials out of config.** Proxy strings support environment interpolation — `http://user:${RESI_PASS}@eu1.proxy.local:8080` expands `${RESI_PASS}` at runtime. Export the variable before running rather than hardcoding passwords in `settings.json`.

## 4. Stealth

**Prefer Chrome with undetected-chromedriver.** Set `browser_settings.type: "chrome"` and `use_undetected_chromedriver: true`; optionally `enable_stealth: true` to layer selenium-stealth's anti-fingerprinting tweaks on top (it is a soft dependency — install it or the flag is ignored). `presets/settings/beginner-chrome-undetected.json` is a ready-made starting point. Plain Firefox works but exposes more automation fingerprints.

**Keep the user agent consistent per account.** `user_agent_generation: "random"` (the default, via fake-headers) generates a new UA each session. A login whose UA changes every run looks synthetic. For long-lived accounts, set `user_agent_generation: "custom"` with a realistic `custom_user_agent` and keep it stable — an account that always looks like the same browser on the same OS is far less suspicious. Pair it with a fixed `window_size` (default `1920,1080`).

**Never run parallel logins to the same account.** Two simultaneous Selenium sessions with the same cookie file mean the same account acting from two browsers, possibly two IPs, at once — a near-certain flag and a recipe for corrupted session state. The orchestrator in `src/main.py` runs accounts concurrently (`asyncio.gather`, one task per account), but each account gets exactly one browser session per run and its actions execute sequentially within that session. Keep that invariant: never launch overlapping runs against one `accounts.json`, and never point two account entries at the same cookie file.

**Headless notes.** Chrome headless uses `--headless=new` for better parity with headed browsing. For warming up accounts or debugging login issues, run headed (`"headless": false`) — it is both less detectable and easier to observe.

## 5. LLM Usage

**Structured JSON prompting.** All generation and analysis goes through `src/core/llm_service/` (`service.py`, `clients.py`, `generator.py`, `parsing.py`, `prompts.py`). `LLMService.generate_structured` takes a schema, optional `system_prompt`, `few_shots` examples, and a `hard_character_limit`, and performs robust JSON extraction (OpenAI JSON mode is attempted when available). When extending prompts, follow this pattern — schema-first instructions plus one or two few-shot examples yield far fewer malformed outputs than free-form prompting.

**Tune relevance and sentiment thresholds, don't disable them.** The analyzer (`src/features/analyzer/`) scores tweets 0–1 for relevance and sentiment; filters live in `analysis_config` globally and as per-account `action_config_override` keys:

- `enable_relevance_filter_likes` / `relevance_threshold_likes` (global default `likes_min: 0.3`)
- `enable_relevance_filter_competitor_reposts` / `relevance_threshold_competitor_reposts` (default `competitor_reposts_min: 0.35`)
- `enable_relevance_filter_keyword_replies` / `relevance_threshold_keyword_replies`
- Decision cutoffs when `engagement_decision` is enabled: `decision_quote_min`, `decision_retweet_min`, `decision_repost_min` (defaults 0.75 / 0.5 / 0.35).

Raise thresholds when the account engages with off-topic content; lower them slightly if nearly everything is filtered out. The presets encode the trade-off: `brand_safe.json` runs likes at 0.5 and reposts at 0.65, while `growth.json` accepts more volume at 0.4 / 0.55. Quoting should always carry the highest bar — it puts words on your timeline.

**Per-account model selection.** Each account can set `llm_settings_override`, and each action type has its own block (`llm_settings_for_post`, `llm_settings_for_reply`, `llm_settings_for_thread_analysis`) with `service_preference` (gemini | openai | azure), `model_name_override`, `max_tokens`, and `temperature`. This lets a flagship account use a premium model while others run cheap ones.

**Cost control: flash-tier for filters, larger models for generation.** Relevance and sentiment checks run on every scraped tweet; generation runs only on the few that pass. The defaults reflect this: thread analysis uses `gemini-2.5-flash` at `max_tokens: 50`, `temperature: 0.1`, while `growth.json` demonstrates upgrading only post generation to `gpt-4o`. Keep analysis on flash-tier models with low token caps and low temperature; spend on the model that writes text people actually read.

## 6. Responsible Use & X Terms of Service

Be clear-eyed about what this software is: **browser automation of X can violate X's Terms of Service and automation rules, and accounts running it risk temporary locks, action blocks, or permanent suspension.** Conservative settings reduce the risk; nothing eliminates it. Do not automate an account you cannot afford to lose.

This project exists for people automating **their own accounts** — scheduling their own content, engaging on topics they genuinely care about, and managing accounts they legitimately operate. It is not a spam tool, and the design choices enforce that stance:

- **Anti-spam defaults.** Low per-run caps, long randomized delays, relevance filters, and recency limits ship enabled or conservative out of the box (see Section 1).
- **No mass-DM, follow-churn, or vote-manipulation features.** These are deliberately absent and contributions adding them will not be accepted.
- **Draft/approval mode (planned, Phase 1).** The upcoming MCP server will support a human-in-the-loop draft mode, on by default for MCP usage: write actions return a draft for review, and nothing posts until explicitly approved. Until it ships, review your prompts and thresholds carefully — everything the current pipeline generates is posted automatically.

You are responsible for how you use this software: compliance with X's Terms of Service and automation policies, with the laws of your jurisdiction (including platform-manipulation and disclosure rules), and with basic decency toward other users. The maintainers provide the tool; the operator owns the consequences.

## 7. Operations

**Read your metrics.** Every run writes two observability streams per account:

- `data/metrics/<account_id>.json` — counters for posts, replies, retweets, quote_tweets, likes, and errors, plus last-run timestamps. A quick health check: are action counts what you configured, and is the error counter flat?
- `logs/accounts/<account_id>.jsonl` — one JSON line per action attempt with metadata. Tail this during a run; grep it afterward for failures.

**Watch error categories.** Recurring patterns map to specific fixes: click-interception/"not clickable" errors usually mean UI changes (the app already retries with scroll-into-view and JS-click fallbacks; persistent failures mean selectors in `src/features/scraper/selectors.py` or `src/features/publisher/` need updating). Login/cookie errors mean expired cookies — re-export them. LLM 429/500 errors mean throttling — switch `service_preference` or reduce volume. A sudden wall of failures on a previously healthy account can indicate an X-side restriction: stop the automation and check the account manually before resuming.

**Preflight checks (planned, Phase 1).** The roadmap includes an `x-use doctor` command that will verify Chrome/driver availability, cookie validity, LLM key configuration, and proxy reachability before a run. Today, do this manually: confirm the driver launches, cookies log in, and a cheap LLM call succeeds before enabling actions on a new setup.

**Back up config and state.** Your operational state lives in `config/` (settings, accounts, cookie files you placed there), `data/` (metrics, proxy pool state), and `logs/`. Back up `config/` and `data/metrics/` regularly to encrypted or access-controlled storage — cookie files are credentials, so treat backups with the same care as the originals. Restoring is just copying the files back; `data/proxy_pools_state.json` can be safely reset if lost (round-robin counters restart).

## 8. Contributing

- **Conventional commits.** Use `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:` prefixes with a concise, imperative subject line.
- **No AI attribution lines.** Do not add AI co-author trailers, "generated by" notes, or tool attributions to commits, PRs, or code comments.
- **Test pure logic with pytest.** Config merging, dedup/action-key handling, and LLM JSON parsing (`src/core/llm_service/parsing.py`) are deterministic and should be covered by unit tests that need no browser and no network. Selenium-dependent code is exercised via optional headless smoke tests, not required unit tests.
- **Keep selectors centralized.** X's DOM changes regularly. Scraper selectors live in `src/features/scraper/selectors.py`; publisher interactions are grouped in `src/features/publisher/` (`composer.py`, `audience_selector.py`, `reply_handler.py`, `retweet_handler.py`). Never scatter inline XPaths through feature logic — a UI change should be fixable in one place.
- **PR etiquette.** Keep PRs focused on one change; describe what you tested and on which browser; include a DOM snippet when fixing selectors so reviewers can verify against the current UI; update `docs/CONFIG_REFERENCE.md` when adding or changing config keys; and never include real cookies, API keys, or populated account configs in diffs, fixtures, or screenshots. See `CONTRIBUTING.md` and the Code of Conduct for the full guidelines.
