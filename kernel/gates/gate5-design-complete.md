# Gate 5 — Design Complete (per story)

> Số gate đánh theo **thứ tự tạo ra**, không theo thứ tự trong DAG. Gate này chạy sau `designer-screen`, **sau** Gate 7 (`design-system` đã khoá token), **trước** Gate 3 của `mobile-screen`.

**Chạy khi:** `designer` (phase `designer-screen`) emit `type: handoff` cho 1 story.

**Vì sao cần:** `agents/designer/skills/generate_wireframe/SKILL.md` đã ghi rõ tiêu chí verify, nhưng **trước đây không gate nào cưỡng chế** — `dag.json` để `designer.gate: null`. Nghĩa là designer tự nhận xong là xong. Wireframe thiếu error state thì `mobile-screen` code theo và **chỉ lộ ra ở Gate 4** (QA test edge case) — lúc đó phải sửa cả design lẫn code đã build lên trên nó. Bắt tại đây rẻ hơn nhiều.

---

## Điều kiện PASS

1. **Đủ UI state:** số state trong `shared/design/screens/<story_id>.json` ≥ số (acceptance criteria + error state) liệt kê cho story đó trong `shared/PRD.md` + `shared/system-spec.md`. Thiếu = chỉ vẽ happy path.
2. **Binding hợp lệ:** mọi `components[].binds[].field` phải tồn tại thật trong `shared/contracts/api-contracts.json` (slice của story đó). Field lạ = designer bịa tên, `mobile-screen` sẽ code sai rồi mới phát hiện. Binding nằm **trong từng component** (`binds[]`), **không** phải mảng `data_bindings` phẳng ở gốc — vì field thuộc về component hiển thị nó, và đó chính là điều kiện để kiểm được "component này có xử lý field rỗng chưa" (điều 8, mã `E17`). Tên `data_bindings_summary` ở handoff là chuyện khác: đó là field **message body** cô đặc, không phải cấu trúc file.
3. **Layout JSON parse được** — nó là input máy đọc cho `mobile-screen`, không phải mô tả cho người.
4. **Handoff body có đủ field cô đặc** theo `kernel/rules/handoff-contracts.md` cạnh `designer-screen → mobile-screen`: `ui_states_count`, `data_bindings_summary`, `domains_applied`, `components_used`, có slot quảng cáo hay không.
5. **Mọi token đều tồn tại thật:** mọi giá trị màu/typography/spacing/radius/elevation trong layout phải là **tham chiếu** tới key phẳng trong `shared/design/tokens.json` (dạng `token:color.primary`, `token:spacing.md`), **không** được hard-code giá trị (`#1A56DB`, `16`). Token lạ hoặc giá trị hard-code = **fail**. Đây là điều kiện **đối xứng với điều 2**: `data_bindings` phải trỏ field thật thì token cũng phải trỏ key thật — cùng một lý do (bịa tên thì lỗi chỉ lộ ra ở tầng dưới).
6. **Domain tag hợp lệ:** mọi tag trong `domains_applied` của handoff phải (a) khớp domain của story đó trong `shared/contracts/domain-map.json`, và (b) là 1 tag trong `known_domains` **có** thư mục skill tương ứng ở `agents/designer/skills/domain/`. Tag lạ = designer nạp bộ pattern không tồn tại rồi tự bịa ra pattern. Domain skill đang `draft: true` **được phép** dùng nhưng handoff phải ghi rõ `draft_domains: [...]` để lớp Evolution biết mà review.
7. **Component registry hợp lệ:** mọi category trong `shared/design/component-registry/<story_id>.json` có `chosen.url` đã xác minh (`verified_url: true`) HOẶC `chosen: null` + `custom_needed: true` kèm `custom_note`. Không entry nào thiếu cả 2 (xem `agents/designer/skills/component_discovery/SKILL.md`) — bịa 1 lib không tồn tại chỉ lộ ra khi `mobile-screen` cài dependency thất bại, đắt hơn nhiều so với bắt ở đây. **Ngoại lệ `reused_from_core`:** entry có `reused_from_core` khác rỗng thì không cần lặp lại `alternatives_considered`/`popularity_signal` (đã kiểm ở `component-registry.core.json` lúc Gate 7). Mọi entry còn lại (không `reused_from_core`, `custom_needed: false`) phải có thêm `alternatives_considered` (>= 1 phần tử) và `popularity_signal.value` — chọn 1 lib mà không so sánh với ứng viên khác và không có số liệu phổ biến thật thì không được coi là "đã chọn kỹ".

8. **Từng component kiểm riêng, không kiểm ở mức màn hình** — chạy `python kernel/tools/validate.py`, nhóm mã `E13`-`E21` phải **sạch**. Đây là điều kiện duy nhất trong gate này có công cụ chấm, nên theo `ORCHESTRATOR.md` bất biến #5: **phải chạy công cụ**, đọc file này không tính là đã kiểm. Layout phải đúng `kernel/contracts/screen-layout.schema.json`.

| Mã | Chặn lớp lỗi |
|---|---|
| `E13` | Hình dạng/ID: `screen_id` lệch tên file, `state_id`/`component_id` trùng |
| `E14` | **Ref trỏ vào hư không** — `appears_in_states`/`parent`/`target_state`/`error_state`/`registry_ref` trỏ đích không tồn tại |
| `E15` | `parent` tạo vòng |
| `E16` | **Lỗi logic**: control thiếu `interaction`; action `navigate`/`submit`/`retry` không có đích; input không có `validation`; `disabled_when` không khai tường minh; state lỗi không có `recovery_action`; thiếu `order`; thiếu `a11y` |
| `E17` | **Lỗi hiển thị**: `binds[]` thiếu `on_null` (ô trắng / chữ `null` hiện ra cho user); text/badge thiếu `text_overflow` (nội dung dài làm vỡ bố cục) |
| `E18` | Hard-code style thay vì `token:` (đối xứng điều 5, nhưng kiểm tới từng component) |
| `E19` | Nhiều hơn **1** `emphasis: primary` mỗi state (trần, không phải đẳng thức — 0 primary hợp lệ với màn danh sách/so sánh) |
| `E20` | Vượt ngưỡng design metric, hoặc `design_metrics_declared` khai lệch số đếm thật |
| `E21` | Ad slot đặt trên state lỗi/đang tải, hoặc `inline` mà không biết chèn sau component nào |

Điều 4 quan trọng với tầng network: nếu thiếu `data_bindings_summary`, `mobile-screen` buộc phải mở lại `api-contracts.json` — mất đúng lợi ích "cô đặc message" mà hợp đồng cạnh thiết kế ra.

Điều 8 là thứ chuyển "bug vặt" từ **phát hiện ở Gate 4 / người dùng thật** sang **phát hiện ở tầng dữ liệu, trước khi `mobile-screen` sinh 1 dòng code nào**. Trước đây gate này chỉ đếm được ở mức màn hình, nên 1 layout "đủ state, đủ token" vẫn có thể chứa nút bấm dẫn tới state không tồn tại hoặc field null không ai xử lý.

> **Ngưỡng design metric (`E20`) đặt ở mức "gần như chắc chắn SAI", không phải "lý tưởng"** — xem `kernel/config/limits.json` → `design._threshold_philosophy`. Gate **chặn** pipeline thì phải dựa trên sự chắc chắn: không thể chặn 1 thiết kế hợp lệ chỉ vì nó chưa tối ưu. Phần tinh chỉnh thẩm mỹ (5 vs 4 cỡ chữ, bố cục có "sang" hay không) **vẫn thuộc về người** — gate này không thay được mắt người, nó chỉ dọn sạch lớp lỗi cơ học để mắt người tập trung vào phần đáng nhìn.

Điều 5 là thứ làm tính nhất quán xuyên suốt app **kiểm được bằng máy** thay vì bằng cảm nhận: 20 story cùng trỏ `token:color.primary` thì chắc chắn cùng màu, còn 20 story mỗi story tự ghi mã hex thì không có cách nào biết chúng có khớp nhau hay không cho tới khi nhìn app thật.

---

## Khi FAIL

Trả về `designer` kèm danh sách **cụ thể** state/field/token còn thiếu hoặc sai (không phải "chưa đủ"). Tăng `gate.consecutive_fail` như mọi gate khác; hết lượt thì → `waiting_human` + escalate kênh `design`.

**Nếu FAIL vì PRD mơ hồ** (không rõ story cần bao nhiêu error state) thì đó **không phải lỗi designer** — designer mở Sync Session với `ba`, và gate này chờ, không đếm là fail của designer. Kể từ khi `agents/ba/AGENT.md` có checklist UX-state bắt buộc trước Gate 1, ca này phải trở nên **hiếm** — nếu vẫn xảy ra thường xuyên thì lỗi nằm ở checklist của `ba`, ghi `shared/lessons_learned.md` (lớp Evolution).

**Nếu FAIL vì thiếu token cần dùng** (vd story cần 1 màu trạng thái mà `tokens.json` không có): **KHÔNG** tự thêm token vào `tokens.json` — `designer-screen` không phải writer của file đó (`kernel/contracts/data-ownership.json`), và thêm token lẻ sau khi đã khoá là phá SSOT style. Đường đúng: emit `doc_drift_detected` → `ba+cto` quyết định có mở lại `design-system` hay không.

## Khi PASS

Node `<STORY>-designer-screen` → `done`; `RECOMPUTE_READY()` mở khoá `<STORY>-mobile-screen` nếu `PROJ-mobile-shell` cũng đã `done`.
