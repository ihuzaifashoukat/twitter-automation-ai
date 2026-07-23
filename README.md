# x-use

**Browser-native AI agents for X (Twitter) — multi-account, MCP-ready, no API keys required.**

x-use drives a real, stealth-hardened browser instead of the paid X API: it posts, replies, searches, and engages across multiple accounts, generates content with your own LLM, and exposes everything as MCP tools so Claude Desktop, Claude Code, Cursor, and other MCP clients can operate your X presence directly.

> x-use is the v2 relaunch of **twitter-automation-ai**. The repository was renamed to `x-use`; old URLs keep redirecting.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ihuzaifashoukat/x-use/actions/workflows/ci.yml/badge.svg)](https://github.com/ihuzaifashoukat/x-use/actions/workflows/ci.yml)
[![Issues](https://img.shields.io/github/issues/ihuzaifashoukat/x-use)](https://github.com/ihuzaifashoukat/x-use/issues)
[![Forks](https://img.shields.io/github/forks/ihuzaifashoukat/x-use)](https://github.com/ihuzaifashoukat/x-use/network/members)
[![Stars](https://img.shields.io/github/stars/ihuzaifashoukat/x-use)](https://github.com/ihuzaifashoukat/x-use/stargazers)

<!-- DEMO GIF PLACEHOLDER: record `x-use init` → paste MCP snippet → draft → approve_draft, then embed the GIF here. -->

---

## Recommended Proxy Providers

X's per-IP detection kills automation at scale. A quality proxy provider keeps a multi-account setup running reliably. The providers below are tested and recommended.

### ⭐ ScrapingAnt — Featured Provider

Private residential network with premium grade IPs — not resold traffic. Supports sticky sessions required for X's IP consistency checks.

<table>
<tr>
<td align="center">
<a href="https://scrapingant.com/residential-proxies?ref=mdkzote">
<img src="https://i.ibb.co/mrK3tv4g/Screenshot-2026-05-08-at-14-17-29.png" alt="ScrapingAnt Residential Proxies" width="350" />
</a>  <br/><a href="https://scrapingant.com/residential-proxies?ref=mdkzote">Top-notch, fast residential ScrapingAnt’s proxies for best performance</a>

</td>
<td align="center">
<a href="https://scrapingant.com/datacenter-proxies?ref=mdkzote">
<img src="https://i.ibb.co/ch0cFtPm/Screenshot-2026-05-08-at-14-17-46.png" alt="ScrapingAnt Datacenter Proxies" width="350" />
</a>
  <br/><a href="https://scrapingant.com/datacenter-proxies?ref=mdkzote">Affordable datacenter proxies for cost-effective operations</a>

</td>
</tr>
</table>
> 5% discount for x-use users — apply code `TWI_AUTO` at checkout.

### RapidProxy

[RapidProxy](https://www.rapidproxy.io/?ref=aut)

<img src="https://i.ibb.co/TqYSs4yr/image-10.png" alt="RapidProxy Banner" width="300" />

Dynamic and static residential proxies with free testing and unlimited, non-expiring traffic.

---

## Quick start

### 1. Install

PyPI publishing (`pip install x-use`) is coming with the v2.0 release — for now, install from the repo:

```bash
git clone https://github.com/ihuzaifashoukat/x-use.git
cd x-use
pip install -e .
```

Requires Python 3.10+ and Chrome. This gives you the `x-use` command. (An editable install also anchors config resolution to the cloned repo, so `config/` is found from anywhere.)

### 2. Configure

```bash
x-use init     # interactive wizard: presets, account + cookie import, LLM keys
x-use doctor   # verify browser/driver, cookies, LLM keys, proxies
```

### 3. Connect your AI client (MCP)

Paste this into `claude_desktop_config.json` (Claude Desktop → Settings → Developer → Edit Config) — the same `command`/`args` pair works for any MCP client that runs stdio servers:

```json
{
  "mcpServers": {
    "x-use": {
      "command": "x-use",
      "args": ["mcp"]
    }
  }
}
```

Restart the client, then ask it to `list_accounts`. **Draft mode is on by default**: write tools return a reviewable draft and change nothing until you call `approve_draft` with the returned `draft_id`.

## x-use vs. API-based X MCP servers

| | **x-use** | API-based X/Twitter MCP servers |
|---|---|---|
| X API cost | **$0** — cookie auth, no X API key needed | Paid X API tier required |
| Multi-account | Built-in: per-account config, cookies, proxies | Typically one account |
| Proxies | Per-account proxies, named pools, hash/round-robin rotation | N/A |
| Stealth | undetected-chromedriver + selenium-stealth, randomized user agents | N/A (official API) |
| Write safety | Draft mode **on by default**, explicit `approve_draft` gate | Usually posts directly |
| Metrics | Per-account counters + JSONL event logs, readable via MCP | Varies |

You still bring your own LLM key (OpenAI, Azure OpenAI, or Gemini) for content generation and analysis — that's the only key involved.

## Features

- **MCP server over stdio** — 9 tools on the official MCP Python SDK (`FastMCP`, pinned `mcp>=1,<2`), with a lazy warm per-account browser session pool so calls stay fast.
- **Draft mode default-on** — write tools build the full payload (including LLM-generated text), store a draft, and touch nothing until approved.
- **Multi-account engine** — post (including communities and media), reply, repost/quote, like, keyword search, and engagement with relevance gating; per-account overrides for keywords, LLM settings, and action behavior.
- **LLM generation & analysis** — OpenAI, Azure OpenAI, Gemini; structured JSON prompting with strict extraction. Keys resolve from env/`.env` first, then `config/settings.json`.
- **Stealth browsers** — undetected-chromedriver, selenium-stealth, randomized user agents, headless support.
- **Proxies** — per-account proxy, named pools, hash or round-robin rotation, `${VAR}` env interpolation in proxy strings.
- **Metrics & logs** — per-account counters in `data/metrics/<account_id>.json` plus JSONL event logs in `logs/accounts/<account_id>.jsonl`.

## MCP tools

| Tool | What it does |
|---|---|
| `list_accounts()` | List configured accounts with secrets stripped. Read-only — never starts a browser. |
| `get_metrics(account)` | Counters and recent events for an account. Read-only — never starts a browser. |
| `search_tweets(keywords, limit=10, account?)` | Search recent posts for a query; returns tweet objects. Read-only. |
| `post_tweet(account, text, media?, community?)` | Post text/media, optionally into a community. |
| `generate_and_post(account, topic)` | Generate a post about a topic with the configured LLM, then post it. |
| `reply_to_tweet(account, tweet_url, text="auto")` | Reply with explicit text, or `"auto"` to generate from the tweet's actual content. |
| `engage(account, keywords, actions=["like"], max_actions=5)` | Relevance-gated likes/retweets on keyword results; hard-capped by per-run config caps. |
| `run_cycle(account?, pipelines?)` | Run a full orchestrator cycle in the background; returns a run handle immediately. |
| `approve_draft(draft_id)` | Execute a pending draft — exactly once, through the same pacing/dedup/metrics path as batch runs. |

With draft mode on (the default), the write tools — `post_tweet`, `generate_and_post`, `reply_to_tweet`, `engage` — return drafts instead of acting. Drafts persist across restarts in `data/drafts.jsonl`. Opt out with `"mcp": { "draft_mode": false }` in `config/settings.json`.

## CLI reference

```bash
x-use init                            # interactive setup wizard
x-use run                             # all active accounts, concurrent
x-use run --account my_account        # one account only
x-use run --pipeline keyword_replies  # one pipeline only (in-memory; config files untouched)
x-use doctor                          # environment checks; exits non-zero on failure
x-use mcp                             # start the MCP stdio server
```

Pipelines for `--pipeline`: `community_engagement`, `competitor_reposts`, `content_curation`, `keyword_replies`, `keyword_retweets`, `likes`.

The legacy `python src/main.py` entry point still works via a deprecation shim (removal no earlier than v2.1).

## Configuration

- `config/accounts.json` — your accounts (gitignored). Start from [`config/accounts.example.json`](config/accounts.example.json) or let `x-use init` write it.
- `config/settings.json` — global defaults: browser, pacing, action caps, LLM, proxies, `mcp` section.
- `.env` — LLM API keys; overrides `settings.json` (env wins). See [`.env.example`](.env.example).
- Full schema: [docs/CONFIG_REFERENCE.md](docs/CONFIG_REFERENCE.md). Starter templates: [`presets/`](presets/) (`x-use init` offers them as wizard choices).

## Responsible use

Browser automation of X carries real account risk — read [BEST_PRACTICES.md](BEST_PRACTICES.md) before running anything. It covers conservative rate limits (the shipped defaults), account warm-up, relevance filters, cookie/credential hygiene, and X ToS considerations. Keep delays high, caps low, and draft mode on.

## Development

```bash
pip install -e '.[dev]'
pytest
```

100 tests cover config loading/merging, dedup keys, LLM JSON extraction, tweet parsing, and proxy pool selection — no network or browser required. CI (GitHub Actions, [`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs the suite plus an import smoke check on Python 3.10/3.11/3.12.

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community expectations. Selector fixes, presets, docs, and MCP tool ideas (via issues) are the most valuable contributions right now; see [ROADMAP.md](ROADMAP.md) for where the project is heading.

## License

MIT — see [LICENSE](LICENSE).
