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
3. `api-contracts.json` parse được và đã **freeze** (từ đây `dev-be` + `client-screen` code song song dựa vào nó).
4. **Checklist UX-state đủ cho mọi story** (`loading`/`empty`/`error`/`permission_denied`/`partial_success`/`offline`/`session_expired` — xem `agents/ba/AGENT.md` mục A). `cto` xác nhận đã đọc đủ checklist này khi ký, không chỉ đọc acceptance criteria. Đây là điều kiện **nội dung** như điều 1-2 — không có tool nào chấm được "checklist có thật sự đủ chất lượng", chỉ có 2 điều kiện cơ học bên dưới (5, 6) bắt được phần **thiếu hoàn toàn**.

**Cơ chế** (validator kiểm được):
5. `gate.signoffs` phủ đủ `gate.required_signoffs` = `["ba", "cto"]`.
6. **Mỗi entry `signoffs` phải trỏ tới `message_id` thật** có `from` khớp `role` của entry đó — chặn việc 1 bên ký thay bên kia. Đây là lý do entry lưu `message_id` chứ không chỉ lưu tên role.
7. **`shared/PRD.md` có khối anchor `story:PROJ` với role `designer`** (`validate.py` mã `E9`). Thiếu = phase `design-system` sẽ nhận Tier 2 rỗng và tự bịa design intent (đối tượng người dùng/tông màu/app tham chiếu) — bắt ở đây rẻ hơn nhiều so với bắt lúc `context_compile.py` chặn dispatch, vì lúc đó đã tốn 1 vòng chờ.
8. **Mọi story thật trong Epic đã có entry trong `shared/contracts/domain-map.json`** (`validate.py` mã `E10`/`E11`) — thiếu = `designer-screen` của story đó không biết nạp domain skill nào.
9. **`shared/contracts/tech-stack.json` tồn tại, parse được, mỗi entry có `platform`/`language` khác rỗng, và entry của client có `ui_framework`** (`validate.py` mã `E12`) — thiếu = `design-system` không biết khoanh vùng tìm thư viện UI theo platform nào khi chạy `component_discovery`, và `client` không biết nạp platform pack nào.
10. **`delivery_targets` hợp lệ và có bằng chứng** (`validate.py` mã `E23`/`E24`): mảng không rỗng, mọi phần tử ⊂ `{mobile_native, web_app, backend_service}`; **đúng 1 `entries`** cho mỗi target đã chọn và **không** có entry lạc; `decision.evidence` không rỗng; `decision.alternatives_rejected` không rỗng; có client thì `platform_pack` trỏ **thư mục thật** trong `agents/client/skills/platform/`; `locked: true` + `locked_at`.

    > **Điều 10 là điều kiện nặng nhất về mặt hệ thống, vì nó quyết định HÌNH DẠNG của WBS.** `generate_wbs` đọc `delivery_targets` để bật/tắt unit (`dag.json` → `only_if`): `has_client` sai thì project web sinh ra node native shell (hoặc project backend thuần sinh ra cả nhánh design), `has_backend` sai thì `qa` chờ một node `dev-be` không bao giờ tồn tại → treo im lặng. Trước đây kernel **mặc định** mọi project là mobile nên bước này không tồn tại; giờ nó là kết luận có bằng chứng của `cto` (`agents/cto/skills/decide_tech_stack/SKILL.md`), và Gate 1 là chỗ **cuối cùng** còn rẻ để bắt sai.

11. **`product_signals` đủ 5 tín hiệu bắt buộc** trong `kernel/memory/project-profile.json` (`how_users_arrive`, `primary_device`, `data_shared_between_users`, `needs_offline`, `needs_search_engine_discovery`) khác `null`, và mọi `decision.evidence[].signal` **trỏ tín hiệu thật** — không phải tín hiệu `cto` tự nghĩ ra. Đây là điều kiện **đối xứng** với điều 8 (`domain-map`) và với quy tắc token/`data_bindings` của nhánh Design: bịa nguồn thì lỗi chỉ lộ ra ở tầng dưới.

Điều 7-9 thêm cùng đợt với nhánh Design/domain; điều 10-11 thêm cùng đợt bỏ mặc định mobile khỏi kernel (xem `shared/lessons_learned.md`) — trước đây Gate 1 không kiểm gì về input của nhánh Design lẫn về loại sản phẩm, nên `ba`/`cto` có thể bỏ qua hoàn toàn checklist/khối `PROJ`/`classify_domain`/tech stack mà Gate 1 vẫn pass. Chạy `python kernel/tools/validate.py` (không chỉ đọc file này) mới coi là đã kiểm — đúng nguyên tắc "Gate nào có công cụ thì PHẢI chạy công cụ" (`ORCHESTRATOR.md` bất biến #5).

---

## Khi FAIL

| Tình huống | Hành động |
|---|---|
| Còn bất đồng, `turn <= max_turns` | Tiếp tục vòng hỏi-đáp. Node `cto` → `status: waiting_sync` (nhả slot, và `C28` không coi nó là agent hang), **chưa** ghi signoff của bên chưa đồng ý. |
| `turn > max_turns` | Dừng Sync Session, **không tự chọn bên thắng**. Node `cto` → `waiting_human` + `escalated_at`, thông báo theo `kernel/config/escalation.json[<key>]` (`key` từ `escalation.notify` của bên đang treo). Quay lại bằng `kernel/tools/resume.py`. |
| Có signoff nhưng nội dung thiếu (vd edge case chưa có phương án) | Đây là lỗi nội dung, không phải cơ chế — bên phát hiện mở `request` mới, `signoffs` của bên kia **bị xoá** để buộc ký lại sau khi sửa. |
| `validate.py` báo `E9`/`E10`/`E11` | Lỗi của `ba` (khối `PROJ` hoặc `domain-map.json` thiếu) — **không** ký thay, trả về `ba` bổ sung rồi chạy lại `validate.py` trước khi ký lại. |
| `validate.py` báo `E12`/`E23`/`E24` | Lỗi của `cto` (`tech-stack.json` thiếu, `delivery_targets` sai/không bằng chứng, entry lệch target, `platform_pack` không tồn tại) — **không** ký thay, `cto` chạy lại `skills/decide_tech_stack/` rồi chạy lại `validate.py` trước khi ký lại. |
| `product_signals` thiếu tín hiệu bắt buộc | Lỗi của `po` (lúc intake). `cto` mở Sync Session với `ba` (`max_turns: 3`) để `ba`/`po` bổ sung — **không** tự điền hộ, và gate này **chờ** (`waiting_sync`), không tính là fail của `cto`. |

---

## Khi PASS

1. Node `<TRACK_ID>-cto` → `status: done`, `gate.result: "pass"`.
2. Orchestrator gọi kernel skill `generate_wbs` → **append** track `build` (xem `skills/generate_wbs/SKILL.md`). Tập unit sinh ra **phụ thuộc `delivery_targets`** vừa khoá ở điều 10 — không phải hằng số.
3. Gate 2 validate track vừa append.
4. Track `intake` kết thúc tại đây — `generate_wbs` **không** tạo lại node `po`/`ba`/`cto`.
