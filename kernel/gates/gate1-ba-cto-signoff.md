# Gate 1 — BA + CTO Dual Signoff

**Chạy khi:** Orchestrator tiêu thụ mỗi `type: response` thuộc Sync Session giữa `ba` và `cto`.

**Node giữ gate này:** `<TRACK_ID>-cto` (theo `dag.json`: `cto.gate = "gate1"`). Node `ba` có `gate: null` — nó không giữ gate riêng.

---

## Chữ ký lưu ở đâu — `gate.signoffs`

Đây là gate **duy nhất** cần nhiều bên ký, nên node của nó có 2 field thêm:

```json
"gate": {
  "name": "gate1",
  "required_signoffs": ["ba", "cto"],
  "signoffs": [
    { "role": "ba",  "at": "...", "message_id": "msg-0043" },
    { "role": "cto", "at": "...", "message_id": "msg-0051" }
  ],
  "result": null
}
```

Orchestrator **append** 1 entry vào `signoffs` mỗi lần tiêu thụ 1 `response` có `status: answered` từ `ba` hoặc `cto`. Gate 1 chỉ `pass` khi `signoffs` phủ đủ `required_signoffs`.

> **Vì sao phải có field này:** node chỉ có 1 field `result`, không lưu được 2 chữ ký. Không có `signoffs`, Orchestrator buộc phải quét `kernel/mailbox/` để tìm xem `ba` đã ký chưa — vi phạm trực tiếp nguyên tắc *`wbs.json` là file trạng thái duy nhất*, và mất luôn khả năng khôi phục sau crash mà không replay log.

---

## Điều kiện PASS

**Nội dung** (không tự động hoá được, `ba`/`cto` tự chịu trách nhiệm):
1. Toàn bộ User Story trong Epic có đủ: mô tả, edge case, acceptance criteria, `Monetization: true|false` (`ba`).
2. Toàn bộ edge case có phương án kỹ thuật tương ứng trong `architecture.md` / `db-schema.md` / `api-contracts.json` / `system-spec.md` (`cto`).
3. `api-contracts.json` parse được và đã **freeze** (từ đây `dev-be` + `mobile-screen` code song song dựa vào nó).

**Cơ chế** (validator kiểm được):
4. `gate.signoffs` phủ đủ `gate.required_signoffs` = `["ba", "cto"]`.
5. **Mỗi entry `signoffs` phải trỏ tới `message_id` thật** có `from` khớp `role` của entry đó — chặn việc 1 bên ký thay bên kia. Đây là lý do entry lưu `message_id` chứ không chỉ lưu tên role.

---

## Khi FAIL

| Tình huống | Hành động |
|---|---|
| Còn bất đồng, `turn <= max_turns` | Tiếp tục vòng hỏi-đáp. Node `cto` giữ `status: running`, **chưa** ghi signoff của bên chưa đồng ý. |
| `turn > max_turns` | Dừng Sync Session, **không tự chọn bên thắng**. Node `cto` → `waiting_human` + `escalated_at`, thông báo theo `kernel/config/escalation.json[<key>]` (`key` từ `escalation.notify` của bên đang treo). Quay lại bằng `kernel/tools/resume.py`. |
| Có signoff nhưng nội dung thiếu (vd edge case chưa có phương án) | Đây là lỗi nội dung, không phải cơ chế — bên phát hiện mở `request` mới, `signoffs` của bên kia **bị xoá** để buộc ký lại sau khi sửa. |

---

## Khi PASS

1. Node `<TRACK_ID>-cto` → `status: done`, `gate.result: "pass"`.
2. Orchestrator gọi kernel skill `generate_wbs` → **append** track `build` (xem `skills/generate_wbs/SKILL.md`).
3. Gate 2 validate track vừa append.
4. Track `intake` kết thúc tại đây — `generate_wbs` **không** tạo lại node `po`/`ba`/`cto`.
