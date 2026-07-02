# Ngày 26 — Hạ Tầng MCP/A2A & Agentic Routing

Lab sinh viên cho **AICB-P2T2 Tuần 6**, xây trên **Google ADK**.

## Bắt đầu nhanh

Lab dùng **uv** để khóa dependency và tạo môi trường tái lập.

```bash
uv sync --frozen
cp .env.example .env   # thêm GOOGLE_API_KEY
uv run jupyter notebook day26_mcp_a2a_lab.ipynb
```

> **Lưu ý `cryptography`:** Lab ghim `cryptography>=46.0.7,<47.0.0`; `uv.lock` giữ toàn bộ dependency nhất quán.

## Cấu trúc dự án

```
├── day26_mcp_a2a_lab.ipynb
├── mcp_server/
│   └── research_tools_server.py   # MCP + governance guard
├── agents/
│   ├── search_agent/              # A2A :8001 + before_tool_callback
│   ├── database_agent/            # A2A :8002 + SQL governance
│   ├── synthesis_agent/           # A2A :8003 + report synthesis
│   └── orchestrator/              # MCP + A2A policy enforcement
├── lab_utils/
│   ├── governance/
│   │   ├── policy.json            # Ma trận capability
│   │   ├── guard.py               # GovernanceGuard
│   │   ├── audit.py               # Audit log JSONL
│   │   └── adk_callbacks.py       # ADK before_tool_callback + auto trace_id
│   ├── routing_tool.py            # suggest_routing (semantic router)
│   ├── semantic_router.py
│   └── agent_registry.py
└── scripts/
    ├── start_a2a_servers.sh       # 3 A2A specialists (8001–8003)
    ├── start_capstone.sh          # A2A + ADK Web một lệnh
    └── start_adk_web.sh           # ADK Web only
└── logs/
    └── governance_audit.jsonl     # Audit tự động ghi
```

## Data Governance

| Lớp | MCP | A2A |
|-----|-----|-----|
| **Capability matrix** | Chỉ `orchestrator` được gọi MCP tools | Orchestrator chỉ dispatch tới agent trong allowlist |
| **SQL guard** | Chỉ SELECT, bảng `agent_metrics` | Tương tự trên `database_agent` |
| **Rate limit** | 30 calls/phút/actor | 30 calls/phút/actor |
| **Runaway prevention** | Tối đa 50 tool calls/task | Tối đa 50 dispatch/task |
| **HITL** | PII trong SQL → cần phê duyệt | Thiếu `trace_id` → cần phê duyệt |
| **Audit** | Mọi lần gọi → `logs/governance_audit.jsonl` | Mọi dispatch → audit log |

Chỉnh policy tại `lab_utils/governance/policy.json`.

## Chạy A2A Specialist

**Bắt buộc trước Module 2 / Capstone.** Xem notebook Module 0.5 hoặc:

```bash
# Capstone — một lệnh (A2A :8001–8003 + ADK Web :8000)
uv run bash scripts/start_capstone.sh

# Hoặc từng bước
bash scripts/start_a2a_servers.sh      # :8001, :8002, :8003
bash scripts/start_adk_web.sh          # :8000 orchestrator

# Hoặc từng terminal
bash scripts/start_search_agent.sh      # :8001
bash scripts/start_database_agent.sh    # :8002
bash scripts/start_synthesis_agent.sh   # :8003

# Dừng
bash scripts/stop_a2a_servers.sh
```

```bash
# ✅ ĐÚNG
adk web agents/orchestrator
# hoặc: bash scripts/start_adk_web.sh

# ❌ SAI — không có root_agent trong thư mục agents/
# adk web agents
```

## Sản phẩm lab

Hệ 4 agent qua A2A + MCP, semantic routing (`suggest_routing`), **data governance** và audit trace.
