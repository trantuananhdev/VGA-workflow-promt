# Gate 3 — Dev → QA (và mọi agent code-producing khác trước khi handoff xuôi dòng)

**Chạy khi:** bất kỳ agent tạo code emit `type: handoff` báo hoàn thành phần việc của nó — `dev-be` (→ `qa`), `client` (phase `client-shell` → tự mở khoá `client-screen`; phase `client-screen` → `qa`/`ads-placement`), `ads` (`ads-setup` → chờ; `ads-placement` → `qa`). Cả 3 đều dùng `git_workflow` và có skill build/verify riêng nên áp dụng cùng bộ điều kiện.

**Điều kiện PASS (tất cả phải đúng):**
1. Skill lint/build riêng của agent đó (`skill_run_lint` với `dev-be` và `client-screen`, build native với `client-shell`, build+init SDK với `ads`) — exit code 0. **Bằng chứng qua `artifact_refs`** (file log thật), body chỉ giữ dòng tổng kết — xem `kernel/rules/handoff-contracts.md`.
2. Skill test riêng tương ứng pass — `artifact_refs` trỏ file log thật, KHÔNG phải lời tóm tắt "tests pass". Gate 0 đã kiểm path tồn tại (`D15`); `artifact_refs` treo = coi như chưa có bằng chứng.
3. Verify của `git_workflow` đạt đủ: có commit `Refs: <task_id>`, PR mở, CI xanh.
4. **Điều kiện bổ sung theo phase:**
   - `client-shell`: `check_platform_compliance` trả `violations: []` (xem `agents/client/skills/platform/mobile-native/check_platform_compliance/SKILL.md`) — chặn ở đây rẻ hơn nhiều so với phát hiện sau khi đã build hàng loạt story lên trên shell sai chuẩn.
   - `client-screen`: **hợp đồng layout đã được thực hiện đủ**, báo bằng **số** trong handoff body (`contract_compliance`): số UI state trong code / số `states[]`, số component đã dựng / số `components[]`, số `binds[]` đã xử lý `on_null` / tổng `binds[]`, số control đã bind `disabled_when` / tổng control, số input có validation client-side / tổng input. **Lệch ở bất kỳ tỉ số nào = FAIL**, kèm danh sách cụ thể field bị bỏ. Xem `agents/client/skills/implement_screen_contract/SKILL.md`.

   > **Vì sao điều này cần 1 điều kiện riêng:** điều 1-2 (lint + test) **về bản chất không bắt được** lớp lỗi này. Code bỏ qua `on_null` vẫn lint sạch và vẫn pass mọi unit test có dữ liệu đầy đủ — nó chỉ hỏng khi field thật bị rỗng ngoài production. Tương tự `text_overflow` (chỉ vỡ khi tên dài), `disabled_when` (chỉ sai khi user bấm đúng lúc không nên bấm). `designer-screen` đã khai đủ và Gate 5 đã kiểm từng component; nếu Gate 3 không kiểm phía thực hiện thì toàn bộ chuỗi đó **dừng lại ở giấy tờ**.
   - `ads-setup`: `setup_consent_management` đã test đủ 3 case (đồng ý / từ chối / ngoài vùng GDPR) — chưa xong consent thì KHÔNG được phép request quảng cáo ở phase sau.
   - `ads-placement`: `check_ad_policy` trả `violations: []` (đây cũng là điều kiện 5 của Gate 4).

**Khi FAIL:** Orchestrator ghi lý do cụ thể vào `wbs.json` → `nodes[node_id].gate.last_error`, tăng `gate.consecutive_fail`, đưa node về `status: ready` để retry — **trả về đúng log lỗi đó, không gửi lại toàn bộ context từ đầu**. Khi `consecutive_fail >= manifest[role].escalation.after_fail` thì node chuyển **`waiting_human`** (không phải `failed` — nó đang chờ người, chưa chết) + set `gate.escalated_at` + escalate. Quay lại vòng lặp bằng `python kernel/tools/resume.py <node_id> --note "..."`. Xem `kernel/rules/scheduling-policy.md`.

Bộ đếm nằm ở **node**, không ở role — fail 3 lần ở story A không được chặn story B.

**Khi PASS:** Orchestrator set node `status: done` rồi chạy `RECOMPUTE_READY()` — node downstream chỉ thành `ready` khi **mọi** `depends_on` của nó đã `done`. Ví dụ `US014-qa` có `depends_on: [US014-dev-be, US014-client-screen]` (+ `US014-ads-placement` nếu story monetization) → chỉ chạy khi đủ cả. Không cần logic "chờ" riêng: nó là hệ quả tự nhiên của `depends_on` trong `wbs.json`.
