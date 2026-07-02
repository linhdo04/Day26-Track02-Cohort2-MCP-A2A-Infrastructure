# Đáp án và biên bản hoàn thành Lab 26

## Bài 1.1 — MCP Server

Ba tool ban đầu là `search_documents`, `sql_query`, `summarize_text`; bài 1.2 bổ sung
`count_words`. SQL governance chỉ cho caller `orchestrator`, chỉ chấp nhận `SELECT`,
chặn DDL/DML, giới hạn bảng `agent_metrics`, kiểm tra PII, rate limit và số tool call.
`stdio` phù hợp cho local development vì không cần mở cổng mạng, lifecycle của server
đi cùng client và giảm bề mặt tấn công.

## Bài 2.1 — A2A và Sub-Agent Local

| Tiêu chí | A2A (Remote) | Sub-Agent Local |
|---|---|---|
| Triển khai | Service/process độc lập qua HTTP | Cùng process với orchestrator |
| Hiệu năng | Có network overhead | Nhanh hơn, gọi nội bộ |
| Cô lập state | Cô lập tốt, scale độc lập | Chia sẻ runtime, cô lập thấp hơn |
| Phù hợp khi | Nhiều team, công nghệ hoặc miền trust; cần scale riêng | Workflow nhỏ, coupling cao, ưu tiên độ trễ |

Chọn A2A khi cần hợp đồng dịch vụ, discovery, isolation, deployment và scaling độc lập.

## Bài 3.1 — Fallback chain

`SemanticRouter.route_with_chain()` ưu tiên semantic match đủ threshold. Khi không có
match, hàm đi theo thứ tự chain và bỏ qua tên agent không đăng ký.

## Bài 5.1 — Capability matrix

| Agent | Capability được phép | Cần HITL | Giới hạn |
|---|---|---|---|
| orchestrator | 4 MCP tools; dispatch 3 specialist | SQL có PII, thiếu trace ID, vượt cost | 30 call/phút; 50 call/task; 300 giây |
| search_agent | `search_web` | Hành động ngoài allowlist | Giới hạn global |
| database_agent | `run_sql_query` SELECT trên `agent_metrics` | Dữ liệu nhạy cảm | Giới hạn global |
| synthesis_agent | `synthesize_report` | Hành động ghi/gửi dữ liệu | Giới hạn global |

## Bài 5.2 — Governance

Policy cho phép orchestrator dispatch `synthesis_agent`, chặn từ khóa `password` ở
`search_documents`, audit mọi quyết định, và test xác nhận caller không hợp lệ không
thể mở MCP connection.

## Capstone W1–W5

Mã và policy đã sẵn sàng cho năm kịch bản. Kiểm thử tích hợp W1 đã xác nhận luồng
`orchestrator → search_agent` với trace ID và câu trả lời từ specialist. Các kiểm thử
xác định tại `tests/test_lab.py` xác nhận MCP registration, SQL DDL deny, keyword deny,
A2A trace/HITL, synthesis dispatch, fallback routing và audit log.

Ngày 2026-07-02, lần chạy live cuối cho W1–W5 bị Gemini API trả về
`429 RESOURCE_EXHAUSTED` do API key đạt quota free-tier 20 request/ngày. Đây là trạng
thái quota bên ngoài, không phải lỗi triển khai. Khi quota reset hoặc có API key mới,
chạy:

```bash
uv run bash scripts/start_a2a_servers.sh
uv run python scripts/verify_capstone.py
bash scripts/stop_a2a_servers.sh
```

W5 luôn được kiểm tra trực tiếp qua `GovernanceGuard` và phải có verdict `deny`.
