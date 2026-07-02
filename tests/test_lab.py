import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from lab_utils.governance.audit import AuditLogger
from lab_utils.governance.guard import GovernanceGuard
from lab_utils.semantic_router import AgentCapability, SemanticRouter
from mcp_server.research_tools_server import _count_words, list_tools


class McpToolTests(unittest.TestCase):
    def test_count_words_and_tool_registration(self):
        self.assertEqual(_count_words("MCP kết nối nhiều agent"), 5)
        names = {tool.name for tool in asyncio.run(list_tools())}
        self.assertIn("count_words", names)


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.router = SemanticRouter(
            [
                AgentCapability("search_agent", "search web documents", ["search"]),
                AgentCapability("database_agent", "SQL database metrics", ["sql"]),
            ],
            threshold=0.15,
        )

    def test_semantic_match_wins_over_chain(self):
        self.assertEqual(
            self.router.route_with_chain("SQL metrics", ["search_agent", "orchestrator"]),
            "database_agent",
        )

    def test_first_valid_fallback_is_used(self):
        self.assertEqual(
            self.router.route_with_chain("không có token phù hợp", ["unknown", "search_agent", "orchestrator"]),
            "search_agent",
        )


class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.guard = GovernanceGuard(
            audit=AuditLogger(Path(self.temp_dir.name) / "audit.jsonl")
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_password_search_is_denied_and_audited(self):
        decision = self.guard.authorize_mcp_tool(
            "orchestrator", "search_documents", {"query": "find admin password"}
        )
        self.assertTrue(decision.blocked)
        entry = self.guard.audit.read_recent(1)[0]
        self.assertEqual(entry["verdict"], "deny")

    def test_invalid_caller_cannot_open_mcp(self):
        decision = self.guard.authorize_mcp_connection("search_agent")
        self.assertTrue(decision.blocked)

    def test_sql_ddl_is_denied(self):
        decision = self.guard.authorize_mcp_tool(
            "orchestrator", "sql_query", {"sql": "DROP TABLE agent_metrics"}
        )
        self.assertTrue(decision.blocked)

    def test_synthesis_dispatch_requires_trace_then_allows(self):
        needs_trace = self.guard.authorize_a2a_dispatch(
            "orchestrator", "synthesis_agent", "report"
        )
        allowed = self.guard.authorize_a2a_dispatch(
            "orchestrator", "synthesis_agent", "report", trace_id="trace-1"
        )
        self.assertTrue(needs_trace.needs_approval)
        self.assertTrue(allowed.allowed)


if __name__ == "__main__":
    unittest.main()
