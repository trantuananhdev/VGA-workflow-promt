# message-examples.md — Ví dụ thật, copy dùng ngay khi 1 agent cần gửi message

> Đây KHÔNG phải hàng đợi thật (đó là `kernel/mailbox/`) — đây là bản mẫu tham khảo.
> `from`/`to` PHẢI là `agent_id` thật trong `agents/`. `node_id` PHẢI tồn tại trong `kernel/memory/wbs.json`.

## 3 quy ước then chốt của tầng điều phối

**1. `node_id` = node của NGƯỜI GỬI** (mọi `type`). Đây là địa chỉ để Orchestrator biết message đóng/chặn node nào. `task_id` KHÔNG đủ để routing vì 1 story sinh nhiều node (`dev-be`, `mobile-screen`, `qa`...).

**2. `processed_at` = cờ consume.** Agent luôn ghi `null`. **Chỉ Orchestrator** điền timestamp, sau khi đã cập nhật `wbs.json` + `event-log.jsonl`. Vòng lặp lọc theo field này, KHÔNG theo `status`.

**3. `message_id` = `msg-<node_id>-<n>`**, với `n` = 1 + số message đã có trong `kernel/mailbox/` cùng `node_id`. **Tên file = `<message_id>.md`.**

> Vì sao không đánh số toàn cục (`msg-0031`): 1 node chỉ có ĐÚNG 1 agent instance ghi, nên đánh số trong phạm vi node là **không thể trùng**. Còn đánh số toàn cục thì 2 agent chạy song song (`concurrency > 1`) sẽ cùng chọn 1 số rồi ghi đè file của nhau — mất message mà không ai biết. Validator cưỡng chế: `D16` (trùng), `D17` (sai quy ước).

---

## 1. Handoff (mặc định, 1 chiều) — `designer` báo xong cho `mobile`

`kernel/mailbox/msg-US014-designer-1.md`:

```markdown
---
message_id: msg-US014-designer-1
type: handoff
node_id: US014-designer
task_id: US-014
from: designer
to: mobile
status: pending
processed_at: null
schema_version: 1
---

## Tóm tắt
Wireframe cho US-014 (đăng nhập OTP) đã xong — 4 UI state (input số điện thoại, chờ OTP,
lỗi OTP sai, lỗi OTP hết hạn). Không có gì mơ hồ cần hỏi lại.

## Bàn giao
- ui_states_count: 4
- data_bindings_summary: [phone_number, otp_code, expires_in]
- có slot quảng cáo: không

## Con trỏ (mở nếu cần)
- `shared/design/US-014.json` (layout JSON đầy đủ)
```

**Orchestrator xử lý theo đúng thứ tự — không bỏ bước nào:**
```
1. Gate 0: frontmatter hợp lệ + `to` có trong dag.json.units["designer"].feeds?
2. wbs.json: node US014-designer -> status: done, finished_at: <now>
3. Thêm message_id vào node.message_refs           (dấu vết: message nào đã chạm node này)
4. RECOMPUTE_READY(): US014-mobile-screen có depends_on
   [US014-designer, PROJ-mobile-shell] — nếu CẢ 2 done -> chuyển ready
5. Append 1 dòng vào event-log.jsonl
6. Set processed_at: <now>                          <-- thiếu bước này = loop vô hạn
```

`mobile` chỉ cần đọc "Tóm tắt" + "Bàn giao" là đủ làm việc — chỉ mở con trỏ khi thực sự cần layout chi tiết.

---

## 2. Request (Sync Session) — `mobile` hỏi `cto`

`kernel/mailbox/msg-US014-mobile-screen-1.md`:

```markdown
---
message_id: msg-US014-mobile-screen-1
type: request
node_id: US014-mobile-screen
task_id: US-014
request_id: sync-US014-01
from: mobile
to: cto
status: pending
processed_at: null
turn: 1
max_turns: 3
schema_version: 1
---

## Câu hỏi
`api-contracts.json#otp-verify` chưa nói rõ: OTP hết hạn (60s) nhưng user vẫn bấm submit
thì server trả `410 Gone` hay `400 Bad Request`? Cần biết để hiển thị đúng message lỗi.
```

Khác handoff ở điểm quan trọng: node `US014-mobile-screen` **vẫn giữ `status: running`** — nó đang bị block chờ trả lời, KHÔNG chuyển `done`. Orchestrator chỉ set `processed_at` (đã route sang `cto`), không đổi trạng thái node.

## 3. Response — `cto` trả lời

`kernel/mailbox/msg-INTAKE001-cto-2.md`:

```markdown
---
message_id: msg-INTAKE001-cto-2
type: response
node_id: INTAKE001-cto
task_id: US-014
request_id: sync-US014-01
from: cto
to: mobile
status: answered
processed_at: null
turn: 2
schema_version: 1
---

## Trả lời
Dùng `410 Gone`. Đã cập nhật `api-contracts.json#otp-verify`.
```

### ⚠ Node của người trả lời có thể đã `done` — điều đó HỢP LỆ

Để ý `node_id: INTAKE001-cto` là node thuộc track `intake` và **đã `done`** từ lúc Gate 1 pass. Vẫn đúng, vì:

- Sau Gate 1, `cto` **vẫn là người có thẩm quyền** về kiến trúc suốt vòng đời project — nó không cần node đang chạy mới được trả lời.
- Trả lời **không làm đổi trạng thái node của người trả lời**. Node `INTAKE001-cto` giữ nguyên `done`.
- Node **đang bị chặn** là của người hỏi, và Orchestrator tìm ra nó bằng cách match `request_id` với request gốc — không cần suy ra từ `node_id` của response.

Nói cách khác: với `handoff` thì `node_id` là *node vừa hoàn thành*; với `request`/`response` thì `node_id` chỉ để **xác thực danh tính người gửi** (Gate 0 kiểm `from` khớp `role` của node đó, chặn mạo danh) — còn việc scheduling đi qua `request_id`.

**Khi `turn` vượt `max_turns` mà `status` chưa `answered`:** Orchestrator dừng Sync Session, KHÔNG tự chọn bên thắng — node bên treo → `waiting_human` + `escalated_at`, thông báo theo `kernel/config/escalation.json`, quay lại bằng `kernel/tools/resume.py`. Ngưỡng mặc định: `kernel/config/limits.json` → `message.sync_max_turns_default`.

---

## 4. Handoff có bằng chứng dài — `artifact_refs`, KHÔNG dán log vào body

`kernel/mailbox/msg-US014-mobile-screen-2.md`:

```markdown
---
message_id: msg-US014-mobile-screen-2
type: handoff
node_id: US014-mobile-screen
task_id: US-014
from: mobile
to: qa
status: pending
processed_at: null
gate_ref: gate3
artifact_refs: [logs/US014-mobile-screen/flutter-analyze.txt, logs/US014-mobile-screen/flutter-test.txt]
schema_version: 1
---

## Tóm tắt
US-014 (đăng nhập OTP) đã xong 4 screen. Test với mock server dựng từ `api-contracts.json`
— `dev-be` chưa deploy nên CHƯA phải integration thật.

## Bàn giao
- PR: #142, CI xanh
- Commit: `Refs: US-014`
- Permission đã dùng: `camera` (đã khai trong `shared/capabilities/native.json`)

## Bằng chứng (đoạn quyết định — file đầy đủ ở artifact_refs)
flutter analyze: No issues found. (2.1s)
flutter test:    00:04 +12: All tests passed!
```

### Giới hạn body

Ngưỡng ở `kernel/config/limits.json` → `message.body_max_lines` / `body_max_chars` (**không lặp lại con số ở đây** — sửa 1 nơi duy nhất).

Body được nạp vào context của agent nhận. Log 5000 dòng dán vào body sẽ **nổ `max_context_tokens`** của `qa`, mà **Gate 0 phần B không chặn được** — nó chỉ kiểm bundle Tier 0+1+2, không kiểm kích thước message.

Nên: **log dài để ở file, `artifact_refs` trỏ tới; body chỉ giữ dòng quyết định.** Validator: `D14` (giới hạn body), `D15` (mọi path trong `artifact_refs` phải tồn tại thật).

Nguyên tắc "No LGTM without proof" **không đổi** — bằng chứng vẫn phải thật và kiểm được, chỉ là nằm ở file thay vì nhét hết vào message.
