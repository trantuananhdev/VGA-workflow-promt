# Gate 7 — Design System Lock (gate DUY NHẤT cần người quyết định)

> Số gate đánh theo **thứ tự tạo ra**, không theo thứ tự trong DAG. Gate này chạy rất sớm (sau `design-system`, song song `mobile-shell`/`devops-infra`/`dev-be`), **trước** Gate 5 của `designer-screen`.

**Chạy khi:** unit `design-system` emit `type: handoff` (node `PROJ-design-system`).

**Vì sao cần:** trước đây mỗi story `designer` tự quyết màu/spacing/typography riêng lẻ — không có SSOT cho style, nên tính nhất quán của app phụ thuộc vào việc 2 lần chạy skill khác nhau có tình cờ chọn giống nhau hay không. Và **không ai nhìn thấy thiết kế trước khi code**: hướng style sai chỉ lộ ra ở Gate 4 (QA) hoặc khi khách xem bản build — lúc đó đã có N story build lên trên nó.

Gate này là chỗ **duy nhất** trong toàn hệ thống mà pipeline dừng lại chờ **người** ra quyết định thẩm mỹ. Nó dùng status riêng `awaiting_human_decision`, **không dùng chung** với `waiting_human`:

| | `waiting_human` | `awaiting_human_decision` |
|---|---|---|
| Ý nghĩa | Gate fail liên tiếp hết lượt retry — **LỖI** | Bước bình thường của quy trình, **không phải lỗi** |
| `gate.consecutive_fail` | Đã ≥ `escalation.after_fail` | **Không tăng** |
| Field bắt buộc | `gate.escalated_at` | `gate.decision_requested_at` |
| Kênh thông báo | `escalation.json` (báo động) | `escalation.json` cùng kênh nhưng là **thông báo thường**, không phải báo động |
| Đường quay lại | `resume.py <node> --note` | `resume.py <node> --decision <theme_id> --note` |

Trộn 2 trạng thái này lại sẽ làm `gate.consecutive_fail` mất nghĩa (validator `C20`/`C22` dựa vào nó để phân biệt lỗi thật với việc đang chờ quyết định), và `today.md` sẽ báo "1 blocker" cho một việc hoàn toàn bình thường.

---

## Điều kiện PASS

1. **Người đã chọn:** `shared/design/theme-choice.json` → `chosen_theme` khác `null`, có `decided_at` + `note`, và giá trị đó **tồn tại** trong `shared/design/tokens.json` → `themes`. Thiếu → node → `awaiting_human_decision` (xem dưới), **không** phải fail.
2. **Token đã khoá đúng lựa chọn:** `tokens.json` → `locked: true`, `locked_at` khác `null`, `chosen_theme` **khớp** `theme-choice.json.chosen_theme`, và 5 nhóm token phẳng ở gốc (`color`/`typography`/`spacing`/`radius`/`elevation`) đã được điền **bằng đúng** nội dung của theme đã chọn. Lệch = agent khoá sai phương án so với cái người chọn.
3. **Ràng buộc accessibility thoả với phương án đã chọn** theo `tokens.json` → `a11y_contract`: contrast body ≥ 4.5:1, large text ≥ 3:1, mọi cặp `on_X`/`X` đạt ngưỡng, spacing scale cho phép tap target ≥ 44pt (iOS) / 48dp (Material). Handoff phải kèm **số đo thật** từng cặp màu, không phải câu "đã kiểm tra".
4. **`theme-preview.html` tồn tại và render đủ trạng thái:** mỗi phương án có ít nhất 1 màn list, 1 card, 1 CTA chính, 1 nút phụ, 1 **trạng thái lỗi**, 1 **trạng thái disabled/loading**. Thiếu trạng thái lỗi = người chọn theo cảm giác màu chứ không thấy app dùng thật ra sao — đúng lý do file HTML này tồn tại thay vì 1 bảng màu.
5. **Mọi phương án cùng tập key:** mọi theme trong `themes` phải có **y hệt** tập key ở cả 5 nhóm. Lệch key = đổi theme về sau làm layout vỡ, và Gate 5 điều 5 của story sẽ fail hàng loạt mà nguyên nhân gốc nằm ở đây.
6. **Handoff body có đủ field cô đặc** theo `kernel/rules/handoff-contracts.md` cạnh `design-system → designer-screen`: `chosen_theme`, `token_keys` (danh sách key phẳng theo nhóm), `a11y_measured`, `responsive_contract`, `locked_at`, `core_components_chosen`.
7. **`shared/design/component-registry.core.json` tồn tại, parse được, và mọi entry hợp lệ:** mỗi entry có `chosen.url` đã xác minh (`verified_url: true`) HOẶC `chosen: null` + `custom_needed: true` kèm `custom_note`. Không có entry nào thiếu cả 2 (chưa xác minh nhưng cũng chưa đánh dấu custom = chưa xong, xem `agents/designer/skills/component_discovery/SKILL.md`).

8. **`responsive_contract` đã chốt và người đã THẤY nó ở nhiều bề rộng:** `shared/design/tokens.json → responsive_contract` tồn tại ở **gốc file** (không nằm trong từng theme — breakpoint trong theme thì đổi theme sẽ đổi breakpoint, đúng lỗi mà điều 5 chặn), và `required_tiers`/`target_orientations`/`max_font_scale` **khớp** dòng "Dải kích thước màn hình mục tiêu" ở mục `PROJ` của `shared/system-spec.md` — không phải agent tự khai app có hỗ trợ tablet hay không. Đồng thời `theme-preview.html` render **mỗi** phương án ở **3 bề rộng (320 / 393 / 600dp)** và thêm **1 lượt ở cỡ chữ 200%**.

   Điều này ở Gate 7 chứ không ở Gate 5 vì đây là chỗ **duy nhất** trong hệ thống mà người nhìn thấy thiết kế trước khi có code. Một phương án theme vỡ ở 320dp hoặc cắt chữ ở cỡ chữ lớn thì lỗi nằm ở **nhịp spacing / type scale của chính theme đó** — bắt ở đây thì sửa 1 file, còn để lọt xuống Gate 5 thì N story đã vẽ lên trên nó và mỗi story phải tự xoay. Đúng lý do file HTML này tồn tại thay vì 1 bảng màu.

Điều 6 quan trọng với tầng network: thiếu `token_keys`/`core_components_chosen` thì mọi node `designer-screen` phải mở lại `tokens.json`/`component-registry.core.json` — mất đúng lợi ích "cô đặc message" mà hợp đồng cạnh này thiết kế ra. Điều 7 chặn rủi ro lớn nhất của `component_discovery`: AI liệt kê 1 thư viện không có thật rồi `mobile-screen` build theo mới phát hiện ra.

---

## Khi CHƯA có lựa chọn của người (điều 1 chưa thoả) — KHÔNG phải FAIL

```
node.status              = "awaiting_human_decision"     # KHÔNG phải waiting_human, KHÔNG phải failed
node.gate.decision_requested_at = now
node.gate.consecutive_fail      → GIỮ NGUYÊN (không tăng)
notify(escalation.json["design"])   # thông báo thường: "có 3 phương án chờ chọn"
```

Node **nhả slot concurrency** (capacity chỉ đếm `status: running` — xem `ORCHESTRATOR.md` §2), nên mọi nhánh song song khác (`mobile-shell`, `devops-infra`, `dev-be`) **chạy bình thường** trong lúc chờ. Chỉ nhánh `designer-screen` → `mobile-screen` bị chặn.

Người xem `shared/design/theme-preview.html` bằng browser rồi:

```bash
# chọn 1 phương án
python kernel/tools/resume.py PROJ-design-system --decision B-bold --note "khách muốn CTA nổi, app thiên bán hàng"

# hoặc: không phương án nào ổn -> yêu cầu làm lại (ĐÂY MỚI LÀ FAIL THẬT, tính vào consecutive_fail)
python kernel/tools/resume.py PROJ-design-system --note "cả 3 quá lạnh, khách muốn tông ấm/thủ công"
```

`resume.py --decision` làm nguyên tử: ghi `theme-choice.json`, đưa node về `ready`, xoá `decision_requested_at`, append `gate.resume_history` + `event-log.jsonl`. Node chạy lại (`attempt` **vẫn là 1** vì `consecutive_fail` không tăng — không có mục `## 4.` trong boot context, đúng: đây không phải retry sau lỗi) và chỉ còn việc khoá token theo lựa chọn.

---

## Khi FAIL (điều 2-7 sai, hoặc người từ chối cả 2-4 phương án)

Trả về `design-system` kèm **danh sách cụ thể** cặp màu nào không đạt contrast / key nào lệch giữa các theme / trạng thái nào thiếu trong preview — không phải "chưa đủ". Tăng `gate.consecutive_fail` như mọi gate khác; hết lượt thì → `waiting_human` + escalate kênh `design`.

**Nếu FAIL vì design intent cấp project mơ hồ** (không rõ brand/đối tượng người dùng/app tham chiếu khi clone) thì đó **không phải lỗi `design-system`** — mở Sync Session với `ba` (`type: request`, `max_turns: 3`) để bổ sung khối `story:PROJ` trong `shared/PRD.md`, và gate này chờ, không đếm là fail.

## Khi PASS

Node `PROJ-design-system` → `done`; `RECOMPUTE_READY()` mở khoá **mọi** node `<STORY>-designer-screen` (chúng chỉ `depends_on` node này). Từ lúc này `tokens.json` là **bất biến** trong Build Mode — muốn đổi token phải qua `doc_drift_detected` → `ba+cto` (xem `kernel/rules/ssot-precedence.md`), vì đổi token sau khi đã có story build lên trên nó là đổi giao diện toàn app.

---

## Đánh đổi đã biết (không che)

Story **đầu tiên** của project không thể bắt đầu `designer-screen` cho tới khi người chọn theme — thêm đúng **1 vòng chờ người** vào đường găng, xảy ra **1 lần/project**, không lặp lại per-story. Đổi lại: bỏ được rủi ro sửa hướng style sau khi đã build N story, và mọi story sau đó không còn phải tự quyết style. Nhánh `dev-be`/`mobile-shell`/`devops-infra` **không** bị ảnh hưởng vì chúng không phụ thuộc `design-system`.
