import os
import re
from typing import Optional, Dict, Any, List

try:
    from ..core.config_loader import ConfigLoader
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    from src.core.config_loader import ConfigLoader


class ProxyManager:
    """
    Resolves per-account proxies. Supports:
    - Direct proxy URLs (e.g., http://user:pass@host:port, socks5://host:port)
    - Named pools via settings: use value "pool:<POOL_NAME>" in account proxy
    - Env interpolation: ${ENV_VAR} within proxy strings will be replaced
    """

    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        self.settings = self.config_loader.get_settings() or {}
        bs = self.settings.get('browser_settings', {})
        self.proxy_pools: Dict[str, List[str]] = bs.get('proxy_pools', {})
        self.strategy: str = (bs.get('proxy_pool_strategy') or 'hash').lower()
        self.state_file: str = bs.get('proxy_pool_state_file') or 'data/proxy_pools_state.json'

    def _interpolate_env(self, s: str) -> str:
        pattern = re.compile(r"\$\{([^}]+)\}")
        def repl(match):
            return os.environ.get(match.group(1), '')
        return pattern.sub(repl, s)

    def _load_state(self) -> Dict[str, Any]:
        from pathlib import Path
        p = Path(__file__).resolve().parent.parent.parent / self.state_file
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            try:
                import json
                return json.loads(p.read_text(encoding='utf-8'))
            except Exception:
                return {}
        return {}

    def _save_state(self, state: Dict[str, Any]) -> None:
        from pathlib import Path
        import json
        p = Path(__file__).resolve().parent.parent.parent / self.state_file
        p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')

    def resolve(self, account_proxy_value: Optional[str], account_id: Optional[str] = None) -> Optional[str]:
        if not account_proxy_value:
            return None
        proxy_str = str(account_proxy_value).strip()
        if proxy_str.startswith('pool:'):
            pool_name = proxy_str.split(':', 1)[1]
            pool = self.proxy_pools.get(pool_name) or []
            if not pool:
                return None
            choice: str
            if self.strategy == 'round_robin':
                state = self._load_state()
                pool_idx = int(state.get(pool_name, 0))
                choice = pool[pool_idx % len(pool)]
                state[pool_name] = (pool_idx + 1) % len(pool)
                self._save_state(state)
            else:
                # Deterministic pick per account for stability; fallback to first
                if account_id:
                    idx = abs(hash(account_id)) % len(pool)
                    choice = pool[idx]
                else:
                    choice = pool[0]
            return self._interpolate_env(choice)
        # Direct URL with optional env vars
        return self._interpolate_env(proxy_str)
