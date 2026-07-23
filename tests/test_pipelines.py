"""The CLI (`x-use run --pipeline`) and the MCP `run_cycle` tool must resolve
pipeline names through one shared mapping (xuse.pipelines.PIPELINE_FLAGS) so
the two surfaces can never drift apart again.
"""

from xuse.pipelines import ALL_PIPELINE_ENABLE_FLAGS, PIPELINE_FLAGS

EXPECTED_PIPELINES = {
    "competitor_reposts",
    "keyword_replies",
    "keyword_retweets",
    "likes",
    "content_curation",
    "community_engagement",
}


def test_cli_uses_shared_mapping():
    from xuse.cli import PIPELINE_FLAGS as cli_flags

    assert cli_flags is PIPELINE_FLAGS


def test_mcp_run_cycle_uses_shared_mapping():
    from xuse.mcp import write_tools

    assert write_tools._PIPELINE_FLAGS is PIPELINE_FLAGS


def test_mapping_covers_all_six_pipelines():
    assert set(PIPELINE_FLAGS) == EXPECTED_PIPELINES


def test_flags_are_unique_enable_flags():
    assert len(ALL_PIPELINE_ENABLE_FLAGS) == len(set(ALL_PIPELINE_ENABLE_FLAGS))
    assert all(flag.startswith("enable_") for flag in ALL_PIPELINE_ENABLE_FLAGS)


def test_every_flag_exists_on_action_config():
    from xuse.models import ActionConfig

    fields = set(ActionConfig.model_fields)
    for flag in ALL_PIPELINE_ENABLE_FLAGS:
        assert flag in fields, f"ActionConfig is missing {flag}"
