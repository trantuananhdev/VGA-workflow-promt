# Gate 3 — Dev → QA (và mọi agent code-producing khác trước khi handoff xuôi dòng)

**Chạy khi:** bất kỳ agent tạo code emit `type: handoff` báo hoàn thành phần việc của nó — `dev-be` (→ `qa`), `mobile` (phase `mobile-shell` → tự mở khoá `mobile-screen`; phase `mobile-screen` → `qa`/`ads-placement`), `ads` (`ads-setup` → chờ; `ads-placement` → `qa`). Cả 3 đều dùng `git_workflow` và có skill build/verify riêng nên áp dụng cùng bộ điều kiện.

**Điều kiện PASS (tất cả phải đúng):**
1. Skill lint/build riêng của agent đó (`skill_run_lint` với `dev-be` và `mobile-screen`, build native với `mobile-shell`, build+init SDK với `ads`) — exit code 0. **Bằng chứng qua `artifact_refs`** (file log thật), body chỉ giữ dòng tổng kết — xem `kernel/rules/handoff-contracts.md`.
2. Skill test riêng tương ứng pass — `artifact_refs` trỏ file log thật, KHÔNG phải lời tóm tắt "tests pass". Gate 0 đã kiểm path tồn tại (`D15`); `artifact_refs` treo = coi như chưa có bằng chứng.
3. Verify của `git_workflow` đạt đủ: có commit `Refs: <task_id>`, PR mở, CI xanh.
4. **Điều kiện bổ sung theo phase:**
   - `mobile-shell`: `check_platform_compliance` trả `violations: []` (xem `agents/mobile/skills/check_platform_compliance/SKILL.md`) — chặn ở đây rẻ hơn nhiều so với phát hiện sau khi đã build hàng loạt story lên trên shell sai chuẩn.
   - `ads-setup`: `setup_consent_management` đã test đủ 3 case (đồng ý / từ chối / ngoài vùng GDPR) — chưa xong consent thì KHÔNG được phép request quảng cáo ở phase sau.
   - `ads-placement`: `check_ad_policy` trả `violations: []` (đây cũng là điều kiện 5 của Gate 4).

**Khi FAIL:** Orchestrator ghi lý do cụ thể vào `wbs.json` → `nodes[node_id].gate.last_error`, tăng `gate.consecutive_fail`, đưa node về `status: ready` để retry — **trả về đúng log lỗi đó, không gửi lại toàn bộ context từ đầu**. Khi `consecutive_fail >= manifest[role].escalation.after_fail` thì node chuyển **`waiting_human`** (không phải `failed` — nó đang chờ người, chưa chết) + set `gate.escalated_at` + escalate. Quay lại vòng lặp bằng `python kernel/tools/resume.py <node_id> --note "..."`. Xem `kernel/rules/scheduling-policy.md`.

Bộ đếm nằm ở **node**, không ở role — fail 3 lần ở story A không được chặn story B.

**Khi PASS:** Orchestrator set node `status: done` rồi chạy `RECOMPUTE_READY()` — node downstream chỉ thành `ready` khi **mọi** `depends_on` của nó đã `done`. Ví dụ `US014-qa` có `depends_on: [US014-dev-be, US014-mobile-screen]` (+ `US014-ads-placement` nếu story monetization) → chỉ chạy khi đủ cả. Không cần logic "chờ" riêng: nó là hệ quả tự nhiên của `depends_on` trong `wbs.json`.
