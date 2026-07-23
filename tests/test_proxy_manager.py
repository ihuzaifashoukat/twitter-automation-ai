"""Tests for xuse.utils.proxy_manager.ProxyManager pool selection (pure logic).

Pool state files are redirected into tmp_path by configuring
``proxy_pool_state_file`` with an absolute path (pathlib: joining an absolute
path onto PROJECT_ROOT yields the absolute path), so the real repo data/ dir
is never written.

Note on the hash strategy: it pins accounts via ``abs(hash(account_id))``.
Python randomizes str hashing per process (PYTHONHASHSEED), so the pinning is
stable within a process but not across restarts — the tests assert the
in-process contract only.
"""

import json

import pytest

from xuse.utils.proxy_manager import ProxyManager

POOL = [
    "http://proxy1.example.com:8001",
    "http://proxy2.example.com:8002",
    "http://proxy3.example.com:8003",
]


@pytest.fixture
def make_proxy_manager(make_config_loader, tmp_path):
    def _factory(strategy="hash", pools=None, state_file=None):
        settings = {
            "browser_settings": {
                "proxy_pools": pools if pools is not None else {"resi": list(POOL)},
                "proxy_pool_strategy": strategy,
                "proxy_pool_state_file": state_file or str(tmp_path / "proxy_state.json"),
            }
        }
        return ProxyManager(make_config_loader(settings=settings))

    return _factory


class TestDirectProxies:
    def test_direct_url_passes_through(self, make_proxy_manager):
        manager = make_proxy_manager()
        assert manager.resolve("http://user:pass@host:1234") == "http://user:pass@host:1234"

    def test_empty_and_none_resolve_to_none(self, make_proxy_manager):
        manager = make_proxy_manager()
        assert manager.resolve(None) is None
        assert manager.resolve("") is None

    def test_env_interpolation_in_direct_url(self, make_proxy_manager, monkeypatch):
        monkeypatch.setenv("XUSE_TEST_PROXY_HOST", "host.internal")
        manager = make_proxy_manager()
        assert (
            manager.resolve("socks5://${XUSE_TEST_PROXY_HOST}:1080")
            == "socks5://host.internal:1080"
        )

    def test_unset_env_var_interpolates_to_empty_string(self, make_proxy_manager, monkeypatch):
        monkeypatch.delenv("XUSE_TEST_UNSET_VAR", raising=False)
        manager = make_proxy_manager()
        assert manager.resolve("http://${XUSE_TEST_UNSET_VAR}:1") == "http://:1"


class TestHashStrategy:
    def test_unknown_pool_resolves_to_none(self, make_proxy_manager):
        manager = make_proxy_manager()
        assert manager.resolve("pool:does_not_exist", account_id="acct") is None

    def test_same_account_gets_same_proxy_within_process(self, make_proxy_manager):
        manager = make_proxy_manager()
        first = manager.resolve("pool:resi", account_id="account-xyz")
        second = manager.resolve("pool:resi", account_id="account-xyz")
        assert first == second
        assert first in POOL

    def test_choice_matches_deterministic_hash_formula(self, make_proxy_manager):
        manager = make_proxy_manager()
        for account_id in ("alpha", "beta", "gamma"):
            expected = POOL[abs(hash(account_id)) % len(POOL)]
            assert manager.resolve("pool:resi", account_id=account_id) == expected

    def test_no_account_id_falls_back_to_first_pool_member(self, make_proxy_manager):
        manager = make_proxy_manager()
        assert manager.resolve("pool:resi") == POOL[0]

    def test_hash_strategy_does_not_write_state_file(self, make_proxy_manager, tmp_path):
        manager = make_proxy_manager()
        manager.resolve("pool:resi", account_id="account-xyz")
        assert not (tmp_path / "proxy_state.json").exists()

    def test_pool_member_env_interpolation(self, make_proxy_manager, monkeypatch):
        monkeypatch.setenv("XUSE_TEST_POOL_USER", "pooluser")
        manager = make_proxy_manager(
            pools={"resi": ["http://${XUSE_TEST_POOL_USER}:pw@host:9000"]}
        )
        assert (
            manager.resolve("pool:resi", account_id="acct")
            == "http://pooluser:pw@host:9000"
        )


class TestRoundRobinStrategy:
    def test_rotates_through_pool_and_wraps(self, make_proxy_manager):
        manager = make_proxy_manager(strategy="round_robin")
        chosen = [manager.resolve("pool:resi") for _ in range(4)]
        assert chosen == [POOL[0], POOL[1], POOL[2], POOL[0]]

    def test_state_file_tracks_next_index(self, make_proxy_manager, tmp_path):
        manager = make_proxy_manager(strategy="round_robin")
        for _ in range(4):
            manager.resolve("pool:resi")
        state = json.loads((tmp_path / "proxy_state.json").read_text(encoding="utf-8"))
        assert state == {"resi": 1}  # 4 picks into a pool of 3 -> next index 1

    def test_rotation_resumes_from_saved_state_across_instances(self, make_proxy_manager):
        first_manager = make_proxy_manager(strategy="round_robin")
        assert first_manager.resolve("pool:resi") == POOL[0]
        assert first_manager.resolve("pool:resi") == POOL[1]

        # A new manager over the same state file continues where the last one stopped.
        second_manager = make_proxy_manager(strategy="round_robin")
        assert second_manager.resolve("pool:resi") == POOL[2]

    def test_pools_rotate_independently(self, make_proxy_manager):
        manager = make_proxy_manager(
            strategy="round_robin",
            pools={"resi": list(POOL), "dc": ["http://dc1.example.com:1", "http://dc2.example.com:2"]},
        )
        assert manager.resolve("pool:resi") == POOL[0]
        assert manager.resolve("pool:dc") == "http://dc1.example.com:1"
        assert manager.resolve("pool:resi") == POOL[1]
        assert manager.resolve("pool:dc") == "http://dc2.example.com:2"

    def test_round_robin_ignores_account_id(self, make_proxy_manager):
        manager = make_proxy_manager(strategy="round_robin")
        assert manager.resolve("pool:resi", account_id="same-account") == POOL[0]
        assert manager.resolve("pool:resi", account_id="same-account") == POOL[1]

    def test_corrupt_state_file_restarts_rotation(self, make_proxy_manager, tmp_path):
        state_path = tmp_path / "proxy_state.json"
        state_path.write_text("{ not json", encoding="utf-8")
        manager = make_proxy_manager(strategy="round_robin", state_file=str(state_path))
        assert manager.resolve("pool:resi") == POOL[0]
