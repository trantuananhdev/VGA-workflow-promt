# Gate 5 — Design Complete (per story)

> Số gate đánh theo **thứ tự tạo ra**, không theo thứ tự trong DAG. Gate này chạy sau `designer-screen`, **sau** Gate 7 (`design-system` đã khoá token), **trước** Gate 3 của `mobile-screen`.

**Chạy khi:** `designer` (phase `designer-screen`) emit `type: handoff` cho 1 story.

**Vì sao cần:** `agents/designer/skills/generate_wireframe/SKILL.md` đã ghi rõ tiêu chí verify, nhưng **trước đây không gate nào cưỡng chế** — `dag.json` để `designer.gate: null`. Nghĩa là designer tự nhận xong là xong. Wireframe thiếu error state thì `mobile-screen` code theo và **chỉ lộ ra ở Gate 4** (QA test edge case) — lúc đó phải sửa cả design lẫn code đã build lên trên nó. Bắt tại đây rẻ hơn nhiều.

---

## Điều kiện PASS

1. **Đủ UI state:** số state trong `shared/design/screens/<story_id>.json` ≥ số (acceptance criteria + error state) liệt kê cho story đó trong `shared/PRD.md` + `shared/system-spec.md`. Thiếu = chỉ vẽ happy path.
2. **`data_bindings` hợp lệ:** mọi field được bind phải tồn tại thật trong `shared/contracts/api-contracts.json` (slice của story đó). Field lạ = designer bịa tên, `mobile-screen` sẽ code sai rồi mới phát hiện.
3. **Layout JSON parse được** — nó là input máy đọc cho `mobile-screen`, không phải mô tả cho người.
4. **Handoff body có đủ field cô đặc** theo `kernel/rules/handoff-contracts.md` cạnh `designer-screen → mobile-screen`: `ui_states_count`, `data_bindings_summary`, `domains_applied`, có slot quảng cáo hay không.
5. **Mọi token đều tồn tại thật:** mọi giá trị màu/typography/spacing/radius/elevation trong layout phải là **tham chiếu** tới key phẳng trong `shared/design/tokens.json` (dạng `token:color.primary`, `token:spacing.md`), **không** được hard-code giá trị (`#1A56DB`, `16`). Token lạ hoặc giá trị hard-code = **fail**. Đây là điều kiện **đối xứng với điều 2**: `data_bindings` phải trỏ field thật thì token cũng phải trỏ key thật — cùng một lý do (bịa tên thì lỗi chỉ lộ ra ở tầng dưới).
6. **Domain tag hợp lệ:** mọi tag trong `domains_applied` của handoff phải (a) khớp domain của story đó trong `shared/contracts/domain-map.json`, và (b) là 1 tag trong `known_domains` **có** thư mục skill tương ứng ở `agents/designer/skills/domain/`. Tag lạ = designer nạp bộ pattern không tồn tại rồi tự bịa ra pattern. Domain skill đang `draft: true` **được phép** dùng nhưng handoff phải ghi rõ `draft_domains: [...]` để lớp Evolution biết mà review.

Điều 4 quan trọng với tầng network: nếu thiếu `data_bindings_summary`, `mobile-screen` buộc phải mở lại `api-contracts.json` — mất đúng lợi ích "cô đặc message" mà hợp đồng cạnh thiết kế ra.

Điều 5 là thứ làm tính nhất quán xuyên suốt app **kiểm được bằng máy** thay vì bằng cảm nhận: 20 story cùng trỏ `token:color.primary` thì chắc chắn cùng màu, còn 20 story mỗi story tự ghi mã hex thì không có cách nào biết chúng có khớp nhau hay không cho tới khi nhìn app thật.

---

## Khi FAIL

Trả về `designer` kèm danh sách **cụ thể** state/field/token còn thiếu hoặc sai (không phải "chưa đủ"). Tăng `gate.consecutive_fail` như mọi gate khác; hết lượt thì → `waiting_human` + escalate kênh `design`.

**Nếu FAIL vì PRD mơ hồ** (không rõ story cần bao nhiêu error state) thì đó **không phải lỗi designer** — designer mở Sync Session với `ba`, và gate này chờ, không đếm là fail của designer. Kể từ khi `agents/ba/AGENT.md` có checklist UX-state bắt buộc trước Gate 1, ca này phải trở nên **hiếm** — nếu vẫn xảy ra thường xuyên thì lỗi nằm ở checklist của `ba`, ghi `shared/lessons_learned.md` (lớp Evolution).

**Nếu FAIL vì thiếu token cần dùng** (vd story cần 1 màu trạng thái mà `tokens.json` không có): **KHÔNG** tự thêm token vào `tokens.json` — `designer-screen` không phải writer của file đó (`kernel/contracts/data-ownership.json`), và thêm token lẻ sau khi đã khoá là phá SSOT style. Đường đúng: emit `doc_drift_detected` → `ba+cto` quyết định có mở lại `design-system` hay không.

## Khi PASS

Node `<STORY>-designer-screen` → `done`; `RECOMPUTE_READY()` mở khoá `<STORY>-mobile-screen` nếu `PROJ-mobile-shell` cũng đã `done`.
