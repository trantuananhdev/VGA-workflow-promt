# skill_implement_screen_contract

**Dùng bởi:** `mobile`, phase `mobile-screen` (riêng, không dùng chung role khác).

**Mục tiêu:** Dịch `shared/design/screens/<story_id>.json` thành code native — **từng field một, không bỏ sót field nào**. Đây là skill duy nhất tiêu thụ hợp đồng layout; không có nó thì mọi field chống-bug mà `designer-screen` đã khai (và Gate 5 đã kiểm) trở thành giấy tờ không ai thực hiện.

**Input:** `shared/design/screens/<story_id>.json` (hợp đồng chính) + `shared/design/component-registry/<story_id>.json` + `component-registry.core.json` (lib được phép dùng) + `token_keys` từ handoff của `designer-screen` + slice `shared/contracts/api-contracts.json`.

**Output:** code UI/business logic native cho đúng 1 story.

---

## Nguyên tắc: hợp đồng KHÔNG phải gợi ý

Layout JSON đã qua Gate 5 nghĩa là **từng component đã được kiểm** (`validate.py` mã `E13`-`E21`): mọi `target_state` trỏ đích tồn tại thật, mọi field có `on_null`, mọi input có `validation`, mọi control có `disabled_when` khai tường minh. Những field đó là **kết quả của quyết định thiết kế đã được kiểm**, không phải ý tưởng để tham khảo.

- **Bỏ qua 1 field = tái tạo đúng lớp bug mà nó sinh ra để chặn.** Ví dụ bỏ `on_null` của `product.price` thì người dùng thấy ô trắng — và không lint/test nào bắt được.
- **Thấy hợp đồng sai/thiếu → emit `doc_drift_detected`**, không tự sửa, không tự "cải thiện". Tự đổi UX flow khác output của `designer` là điều `AGENT.md` cấm tường minh.
- **Không được `TODO`/`FIXME` thay cho việc thực hiện field.** Chưa làm được thì báo drift, không để lại chỗ trống im lặng.

## Quy trình — lặp theo TỪNG component, không theo màn hình

```
1. Đọc layout. Dựng cây widget theo `parent` + `order`:
   parent=null -> ở gốc màn hình; order nhỏ trước. Component không có trong
   `appears_in_states` của state đang render thì KHÔNG dựng ở state đó.

2. Với MỖI state trong states[]: hiện thực đúng 1 UI state thật trong code.
   - `entered_when` -> điều kiện vào state đó phải là logic thật (không phải comment).
   - `recovery_action` -> đường thoát phải bấm được thật (vd nút Thử lại wired tới
     `target_state` đã khai), không chỉ là chữ hiển thị.

3. Với MỖI component: đi hết bảng "Field -> code" bên dưới. Tick từng dòng.
   Đây là chỗ áp `chia để trị`: kiểm theo component, không kiểm theo màn hình —
   1 màn 20 component thì có 20 lượt đối chiếu, không phải 1 lượt.

4. `registry_ref` khác null -> dùng ĐÚNG lib đã chọn trong component-registry,
   không tự thay lib khác (dù bạn biết lib "tốt hơn"): lựa chọn đó đã qua
   đánh giá tech-stack + popularity và Gate 5/7 đã kiểm. Muốn đổi -> drift.

5. `pattern_ref` khác null -> mở đúng mục đó trong
   agents/designer/skills/design_patterns/<tag>/SKILL.md để lấy ý đồ tỉ lệ/motion.
   ĐỌC CẢ MỤC 5: số nào file đó tự nhận là SUY ĐOÁN thì không bám cứng.

6. Tự kiểm theo checklist cuối file TRƯỚC khi chạy lint/test.
```

## Bảng Field → code (không bỏ dòng nào)

| Field hợp đồng | Code PHẢI làm | Bỏ qua thì sinh lỗi gì |
|---|---|---|
| `parent` + `order` | Cấu trúc cây widget + thứ tự hiển thị | Bố cục khác thiết kế, mỗi lần build 1 thứ tự |
| `appears_in_states` | Điều kiện render theo state | Component hiện ở state không nên hiện |
| `emphasis` | `primary` = nút filled/khối nổi nhất; `secondary`/`tertiary` giảm dần (outlined/text) | Mất phân cấp thị giác, user không biết bấm gì |
| `style: "token:..."` | Tra **theme system** của platform (Compose `MaterialTheme`, SwiftUI `Color`/`Font` từ design system) — **không** hard-code literal | 20 story lệch màu nhau, đổi theme phải sửa N file |
| `binds[].field` | Bind field thật từ model của `api-contracts.json` | Hiển thị sai dữ liệu |
| **`binds[].on_null`** | `hide_component` → ẩn hẳn widget; `placeholder` → khung giữ chỗ; `dash` → hiện "—"; `zero` → hiện 0; `fallback_text` → hiện đúng chuỗi đã khai; `skeleton` → shimmer | **Ô trắng / chữ `null` / crash NPE trước mặt user** |
| `binds[].format` | Dùng formatter của platform theo locale (`currency`/`date`/`relative_time`/`percent`/`duration`) — **không** `toString()` thô | Timestamp thô, số không phân cách hiện ra UI |
| **`text_overflow`** | Compose `maxLines` + `TextOverflow`; SwiftUI `lineLimit` + `truncationMode` | Tên dài làm **vỡ bố cục** — mock data tên ngắn không bao giờ lộ ra |
| `interaction.trigger` | Gắn đúng loại cử chỉ (tap/long-press/swipe/pull-refresh) | Cử chỉ không hoạt động hoặc sai loại |
| `interaction.action` + `target_state`/`target_screen` | Chuyển **đúng** state/màn đã khai | Nút bấm không đi đâu (lỗi logic hay gặp nhất) |
| **`interaction.disabled_when`** | Bind `enabled` thật theo điều kiện đó. `null` = luôn enabled | Bấm được lúc không nên bấm → gửi request rác / trừ tiền 2 lần |
| **`interaction.validation[]`** | Validate **client-side** theo từng `rule`, fail thì hiện đúng `error_state` đã khai | Input rác đi thẳng xuống backend |
| `a11y.label` | `contentDescription` (Android) / `accessibilityLabel` (iOS) | Icon là ô trống với screen reader |
| `a11y.decorative: true` | Đánh dấu bỏ qua với screen reader | Screen reader đọc rác |
| `a11y.min_tap_target_ok` | Bảo đảm vùng bấm ≥ 48dp / 44pt **thật** (thêm padding nếu icon nhỏ) | Bấm không trúng, fail a11y audit |
| `ad_slots[]` | Chèn đúng `region`/`after_component_id`; **không** chèn ở state `error`/`loading` | Quảng cáo trên màn lỗi = vi phạm chính sách |

## Verify trước khi báo "xong" (chạy TRƯỚC `run_lint`/`run_unit_test`)

Đối chiếu bằng cách **đếm**, không bằng cảm giác:

- Số UI state trong code **=** số phần tử `states[]`. Thiếu 1 state = chưa xong.
- Mỗi state `kind` ∈ {`error`,`offline`,`permission_denied`,`session_expired`} có đường thoát **bấm được thật** đúng `recovery_action`.
- Số component đã dựng **=** số phần tử `components[]` (trừ component không thuộc state nào được render — trường hợp này đáng ngờ, kiểm lại).
- **Mọi** `binds[]` có xử lý `on_null` trong code — tự quét lại, đây là lớp bug hay bị bỏ nhất vì happy-path test luôn có dữ liệu.
- **Mọi** control có `disabled_when` khác null đã bind `enabled` thật.
- **Mọi** input có validation client-side + hiện đúng `error_state`.
- **Mọi** text/badge có giới hạn dòng đúng `text_overflow`.
- **Không** literal màu/spacing nào trong code UI — tất cả qua theme system.
- Lib dùng đúng `registry_ref`, không thay thế.
- Chạy `python kernel/tools/validate.py`: nhóm `E13`-`E21` phải **sạch** — nếu hợp đồng bạn đang code bị lỗi thì lỗi nằm ở `designer-screen`, emit `doc_drift_detected` thay vì code theo hợp đồng sai.
