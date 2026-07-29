# Gate 5 — Design Complete

> Số gate đánh theo **thứ tự tạo ra**, không theo thứ tự trong DAG. Gate này chạy sớm (sau `designer`), trước Gate 3 của `mobile-screen`.

**Chạy khi:** `designer` emit `type: handoff` cho 1 story.

**Vì sao cần:** `agents/designer/skills/generate_wireframe/SKILL.md` đã ghi rõ tiêu chí verify, nhưng **trước đây không gate nào cưỡng chế** — `dag.json` để `designer.gate: null`. Nghĩa là designer tự nhận xong là xong. Wireframe thiếu error state thì `mobile-screen` code theo và **chỉ lộ ra ở Gate 4** (QA test edge case) — lúc đó phải sửa cả design lẫn code đã build lên trên nó. Bắt tại đây rẻ hơn nhiều.

---

## Điều kiện PASS

1. **Đủ UI state:** số state trong `shared/design/<story_id>.json` ≥ số (acceptance criteria + error state) liệt kê cho story đó trong `shared/PRD.md` + `shared/system-spec.md`. Thiếu = chỉ vẽ happy path.
2. **`data_bindings` hợp lệ:** mọi field được bind phải tồn tại thật trong `shared/contracts/api-contracts.json` (slice của story đó). Field lạ = designer bịa tên, `mobile-screen` sẽ code sai rồi mới phát hiện.
3. **Layout JSON parse được** — nó là input máy đọc cho `mobile-screen`, không phải mô tả cho người.
4. **Handoff body có đủ field cô đặc** theo `kernel/rules/handoff-contracts.md` cạnh `designer → mobile-screen`: `ui_states_count`, `data_bindings_summary`, có slot quảng cáo hay không.

Điều 4 quan trọng với tầng network: nếu thiếu `data_bindings_summary`, `mobile-screen` buộc phải mở lại `api-contracts.json` — mất đúng lợi ích "cô đặc message" mà hợp đồng cạnh thiết kế ra.

---

## Khi FAIL

Trả về `designer` kèm danh sách state/field còn thiếu (cụ thể, không phải "chưa đủ"). Tăng `gate.consecutive_fail` như mọi gate khác; hết lượt thì → `waiting_human` + escalate kênh `design`.

**Nếu FAIL vì PRD mơ hồ** (không rõ story cần bao nhiêu error state) thì đó **không phải lỗi designer** — designer mở Sync Session với `ba`, và gate này chờ, không đếm là fail của designer.

## Khi PASS

Node `<STORY>-designer` → `done`; `RECOMPUTE_READY()` mở khoá `<STORY>-mobile-screen` nếu `PROJ-mobile-shell` cũng đã `done`.
