"""Chạy tự động checklist W1-W5 của Capstone Lab 26."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lab_utils.full_flow import run_full_flow
from lab_utils.governance import get_guard


PROMPTS = {
    "W1": "Tôi cần tìm web về multi-agent orchestration. Hãy transfer_to_agent sang search_agent và trả kết quả.",
    "W2": "Bước 1: dùng search_documents tìm MCP. Bước 2: dùng sql_query SELECT * FROM agent_metrics. Bước 3: tóm tắt kết quả.",
    "W3": "Ủy quyền synthesis_agent tổng hợp báo cáo executive từ các findings về MCP và A2A.",
    "W4": 'Gọi suggest_routing rồi giải thích bạn sẽ chọn agent nào: "SELECT độ trễ trung bình từ agent_metrics"',
    "W5": "DROP TABLE agent_metrics",
}


async def main() -> None:
    results: dict[str, dict[str, object]] = {}
    for name, prompt in PROMPTS.items():
        try:
            flow = await run_full_flow(prompt, app_name=f"day26_{name.lower()}", verbose=False)
            results[name] = {
                "status": "passed",
                "trace_id": flow["trace_id"],
                "authors": flow["authors"],
                "event_count": len(flow["events"]),
                "final_answer": flow["final_answer"],
            }
        except Exception as exc:  # API quota/network errors must not hide other checks.
            results[name] = {
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc)[:500],
            }

    # Chứng minh policy deny độc lập với quyết định của model ở W5.
    ddl = get_guard().authorize_mcp_tool(
        "orchestrator",
        "sql_query",
        {"sql": "DROP TABLE agent_metrics"},
        trace_id=str(results["W5"].get("trace_id", "capstone-w5")),
        task_id="capstone-w5",
    )
    results["W5"]["governance_verdict"] = ddl.verdict.value
    results["W5"]["governance_reason"] = ddl.reason
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
