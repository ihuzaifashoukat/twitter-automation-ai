import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from ..core.config_loader import ConfigLoader
except ImportError:
    import sys
    from pathlib import Path as _P
    sys.path.append(str(_P(__file__).resolve().parent.parent.parent))
    from src.core.config_loader import ConfigLoader


class MetricsRecorder:
    """
    Records per-account metrics and structured events.
    - JSON summary at data/metrics/<account_id>.json
    - JSONL events at logs/accounts/<account_id>.jsonl
    Paths are relative to project root.
    """

    def __init__(self, account_id: str, config_loader: ConfigLoader):
        self.account_id = account_id
        self.config_loader = config_loader
        # Paths
        from pathlib import Path as P
        project_root = P(__file__).resolve().parent.parent.parent
        self.metrics_dir = project_root / 'data' / 'metrics'
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir = project_root / 'logs' / 'accounts'
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.summary_path = self.metrics_dir / f'{self.account_id}.json'
        self.events_path = self.logs_dir / f'{self.account_id}.jsonl'
        # Cached summary
        self.summary: Dict[str, Any] = self._load_summary()

    def _load_summary(self) -> Dict[str, Any]:
        if self.summary_path.exists():
            try:
                return json.loads(self.summary_path.read_text(encoding='utf-8'))
            except Exception:
                pass
        return {
            'account_id': self.account_id,
            'counters': {
                'posts': 0,
                'replies': 0,
                'retweets': 0,
                'quote_tweets': 0,
                'likes': 0,
                'errors': 0,
            },
            'last_run_started_at': None,
            'last_run_finished_at': None,
        }

    def mark_run_start(self):
        self.summary['last_run_started_at'] = datetime.utcnow().isoformat()
        self._flush_summary()

    def mark_run_finish(self):
        self.summary['last_run_finished_at'] = datetime.utcnow().isoformat()
        self._flush_summary()

    def increment(self, key: str, by: int = 1):
        self.summary['counters'][key] = int(self.summary['counters'].get(key, 0)) + by
        self._flush_summary()

    def log_event(self, action: str, result: str, metadata: Optional[Dict[str, Any]] = None):
        payload = {
            'ts': datetime.utcnow().isoformat(),
            'account_id': self.account_id,
            'action': action,
            'result': result,
            'meta': metadata or {},
        }
        with self.events_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(payload, ensure_ascii=False) + '\n')

    def _flush_summary(self):
        self.summary_path.write_text(json.dumps(self.summary, ensure_ascii=False, indent=2), encoding='utf-8')

