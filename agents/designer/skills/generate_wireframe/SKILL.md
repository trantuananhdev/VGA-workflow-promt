# skill_generate_wireframe

**Dùng bởi:** `designer`, phase `designer-screen` (riêng, không dùng chung role khác).

**Mục tiêu:** Từ 1 User Story (PRD slice) + data shape (`api-contracts.json` slice) + design token đã khoá (`tokens.json`) + domain của story (`domain-map.json`), sinh layout JSON — không phải ảnh/prose mô tả, để `mobile` (phase `mobile-screen`) parse trực tiếp thay vì phải "đọc hiểu" mô tả bằng lời.

**Input:** anchor-tag slice của `shared/PRD.md` + `shared/system-spec.md` (story_id đang xử lý) + slice `shared/contracts/api-contracts.json` + slice `shared/contracts/domain-map.json` + `token_keys` từ handoff của `design-system`

**Output:** `shared/design/screens/<story_id>.json`

---

## Quy trình

```
0. NẠP NGỮ CẢNH TRƯỚC KHI VẼ — 2 thư viện, 2 mục đích khác nhau.
   Đọc ĐÚNG 2 file dưới, KHÔNG đọc file index (domain/SKILL.md, design_patterns/SKILL.md):
   index là spec cho người VIẾT thư viện, chỉ cần khi bootstrap tag mới (xem bước 0c).

   a) AN TOÀN (cái gì SAI):
      domains = domain-map.json.stories[story_id].domains       # có thể NHIỀU domain
      với mỗi domain: đọc agents/designer/skills/domain/<tag>/SKILL.md
      -> pattern UX chuẩn, pitfall, quy ước platform, checklist a11y đặc thù
      Domain `primary` quyết định layout chính; domain phụ chỉ bổ sung state/pitfall.

   b) CRAFT (cái gì ĐẸP) — CHỈ domain `primary`, không nạp domain phụ:
      đọc agents/designer/skills/design_patterns/<primary>/SKILL.md
      -> mục 1 bố cục, mục 2 hierarchy/emphasis, mục 3 cấu trúc bên trong component,
         mục 4 interaction & motion, mục 6 thích ứng kích thước (dùng ở bước 3.7)
      LƯU Ý: mục 5 của file đó ghi rõ phần nào là SUY ĐOÁN (chưa có spec chống lưng),
      và tuyên bố đó áp cả cho số trong mục 6 (mục 6 cố ý đứng sau mục 5 — xem
      design_patterns/SKILL.md). Số nào là suy đoán thì điều chỉnh theo tokens.json
      của project, đừng bám cứng.

   c) Thiếu thư mục cho 1 tag -> lúc đó MỚI đọc file index tương ứng để làm bootstrap
      `draft: true` (2 thư viện có cơ chế riêng, cùng nguyên tắc).

1. Với mỗi acceptance criteria trong story, xác định 1 màn hình/trạng thái UI tương ứng.

2. Với mỗi error state liệt kê trong shared/system-spec.md (cùng story_id), PHẢI có 1 UI state
   tương ứng — không được chỉ vẽ happy path.

3. ĐỐI CHIẾU VỚI DOMAIN: domain skill liệt kê state mà app loại này LUÔN cần
   (vd on-demand-booking luôn cần "chờ đối tác xác nhận" + "huỷ/đổi lịch").
   State nào domain đòi mà PRD KHÔNG nêu -> KHÔNG tự thêm vào layout, cũng KHÔNG bỏ qua:
   mở Sync Session với `ba` (max_turns: 3) hỏi story có cần state đó không.
   Đây là giá trị chính của domain skill: phát hiện thiếu sót của PRD TRƯỚC khi vẽ,
   thay vì để QA phát hiện ở Gate 4.

3.5. BẺ MÀN HÌNH THÀNH COMPONENT — tới TỪNG PHẦN BÊN TRONG (bước "Screen")
   Đây là bước "chia để trị". Không dừng ở "1 cái card" — bẻ card thành các phần bên
   trong (ảnh / tên / giá / rating), vì kiểm 1 card như 1 khối thì KHÔNG phát hiện được
   "giá bị null không ai xử lý". Dùng mục 3 của file pattern làm căn cứ bẻ.
   Với mỗi phần cần 1 widget không tầm thường (spinner, chart, calendar picker, sheet…),
   ghi 1 component_need: { category, description, ui_state_ref }
   KHÔNG chọn lib ở bước này — chỉ liệt kê NHU CẦU. Chọn lib là việc của
   component_discovery bước A (core reuse-check) rồi B (mini search) — chạy SAU bước
   này, TRƯỚC bước 4.

3.7. KHAI KÍCH THƯỚC MÀN HÌNH — gọi skill responsive_layout.
   Đọc agents/designer/skills/responsive_layout/SKILL.md + mục 6 của file pattern primary,
   rồi điền `responsive` cho MỌI khối chứa (section/card/list/grid/row/column) và mọi
   image/chart/media_player, cộng `responsive_declared` ở gốc.
   VÌ SAO Ở ĐÂY, KHÔNG PHẢI TRONG BƯỚC 4: biết trước "hàng này phải wrap ở 320dp" hoặc
   "khối này không được khoá chiều cao" có thể đổi cả cách bẻ component ở bước 3.5 —
   khai sau khi đã chốt cây thì luôn thành "điền cho đủ field".

4. Sinh layout JSON — CHỈ sau khi mọi component_need đã resolve. Dùng bảng field ngay
   dưới mục "Quy trình" này làm chuẩn; KHÔNG cần mở
   kernel/contracts/screen-layout.schema.json (file đó ~7000 token, dành cho
   validate.py và cho người — mở nó chỉ làm loãng chú ý của chính bạn).

4.5. TỰ ĐO design_metrics_declared rồi khai bằng SỐ (không phải câu "đã kiểm tra"):
   distinct_type_sizes, distinct_colors, spacing_keys_used, root_level_component_count.
   validate.py SUY RA lại từ style thật và đối chiếu — khai lệch = bị bắt. Cùng nguyên
   tắc Gate 7 điều 3 đã áp cho contrast.

5. Ghi vào shared/design/screens/<story_id>.json (screen_id PHẢI khớp tên file)
```

## Bảng field layout JSON — đủ để viết, không cần mở schema

Gốc: `{ schema_version: 1, screen_id, states[], components[], ad_slots[], responsive_declared, design_metrics_declared }` — **không có key nào khác** (mã `E13` bắt key lạ).

`responsive_declared` (bắt buộc, khai ở bước 3.7): `{ tiers_covered[], orientations[], font_scale_verified, keyboard_avoidance }` — phải phủ đủ `required_tiers`/`target_orientations` của `responsive_contract`, `font_scale_verified` ≥ 2.0, và `keyboard_avoidance: "not_applicable"` chỉ hợp lệ khi màn không có input/select/search_field. Binding nằm **trong từng component**, không có mảng `data_bindings` phẳng ở gốc.

`states[]`:

| Field | Bắt buộc khi | Ghi chú |
|---|---|---|
| `state_id` | luôn | duy nhất; là đích của `interaction.target_state` |
| `kind` | luôn | `success` \| `loading` \| `empty` \| `error` \| `permission_denied` \| `partial_success` \| `offline` \| `session_expired` |
| `entered_when` | mọi `kind` ≠ `success` | không nói rõ khi nào xảy ra = dev phải đoán |
| `recovery_action` | `error`/`offline`/`permission_denied`/`session_expired` | state lỗi không có đường ra là **bug UX**, không phải quyết định thiết kế |

`components[]` — mảng **phẳng**, lồng bằng `parent`:

| Field | Bắt buộc khi | Ghi chú |
|---|---|---|
| `component_id` | luôn | duy nhất |
| `type` | luôn | enum đóng (container/content/control/overlay/nav/feedback/`ad_slot`) — xem enum trong schema nếu cần tra tên chính xác |
| `appears_in_states` | luôn | ≥1, mọi giá trị phải là `state_id` thật. Rỗng = component chết |
| `emphasis` | luôn | `primary`/`secondary`/`tertiary`. **Nhiều nhất 1 `primary` mỗi state** — 0 hợp lệ với màn danh sách/so sánh |
| `order` | trừ overlay | thiếu = thứ tự đọc không xác định, mỗi lần sinh code ra 1 thứ tự khác |
| `parent` | luôn (`null` = ở gốc) | **cơ chế bẻ nhỏ**: card → ảnh/tên/giá/rating |
| `style` | khi có style | mọi value là `"token:<nhóm>.<key>"`. SAI: `"#FFF"`, `16` |
| `binds[]` | khi hiển thị dữ liệu | mỗi phần tử: `field` (tồn tại thật trong `api-contracts.json`) + **`on_null`** (`hide_component`/`placeholder`/`dash`/`zero`/`fallback_text`/`skeleton`) + `format` với số/thời gian. Thiếu `on_null` = ô trắng hoặc chữ `null` hiện ra trước mặt user |
| `text_overflow` | `type` = `text`/`badge` | `{ max_lines, behavior }` — chặn nội dung dài làm vỡ bố cục (mock data tên ngắn **không bao giờ** phát hiện ra lỗi này) |
| `responsive` | mọi khối chứa (`section`/`card`/`list`/`grid`/`row`/`column`) + `image`/`chart`/`media_player` | `{ axis, columns, wrap_behavior, degrade_order, sizing, aspect_ratio, min_height_dp, safe_area, pinned }` — cùng vai trò `text_overflow` nhưng ở mức **khối**: chặn vỡ ở 320dp / cỡ chữ 200% / landscape / bàn phím / notch. Điền ở bước 3.7, xem `responsive_layout/SKILL.md`. `min_height_dp` **phải `null`** nếu khối chứa text |
| `group` | khi vài phần KHÔNG được tách rời khi wrap | nhãn logic (vd `product_meta`). Khác `responsive`: `group` nói **cái gì** đi cùng nhau, `responsive` nói khối chứa **phản ứng thế nào** |
| `interaction` | mọi control | xem bảng dưới |
| `a11y` | mọi control + image/icon có nghĩa | `min_tap_target_ok: true` với control; `label` bắt buộc với `icon_button`; `decorative: true` cho ảnh trang trí |
| `pattern_ref` | khi có căn cứ craft | `"design_patterns/<tag>#<số mục>"` |
| `registry_ref` | khi dùng lib ngoài | `category` thật trong component-registry |

`interaction`:

| Field | Bắt buộc khi | Ghi chú |
|---|---|---|
| `trigger` | luôn | `tap`/`long_press`/`text_change`/`submit`/`swipe`/`pull_refresh`/… |
| `action` | luôn | `navigate`/`submit`/`toggle`/`retry`/`dismiss`/`select`/`expand`/`collapse`/`none` |
| `target_state` hoặc `target_screen` | `action` ∈ {`navigate`,`submit`,`retry`} | phải **tồn tại thật** — action trỏ vào hư không là lỗi logic |
| `disabled_when` | **luôn khai tường minh** | `null` = KHẲNG ĐỊNH luôn bấm được, không phải "chưa nghĩ tới" |
| `validation[]` | `type` ∈ {`input`,`select`,`search_field`} | ≥1 luật, mỗi luật `{ rule, error_state }` với `error_state` tồn tại thật. Không có = input rác đi thẳng xuống backend |

`ad_slots[]`: `{ slot_id, format, region, after_component_id (bắt buộc khi region=inline), appears_in_states }` — **không** đặt trên state `kind` = `error`/`loading`.

## Thứ tự bắt buộc với `component_discovery`

Bước 3.5 (liệt kê nhu cầu) PHẢI chạy trước khi gọi `component_discovery`, và bước 4 (chốt JSON)
PHẢI chạy sau khi `component_discovery` đã resolve xong mọi component_need — xem
`agents/designer/AGENT.md` mục "Skill được phép gọi" để biết chuỗi gọi đầy đủ
(generate_wireframe 0-3.5 → component_discovery bước A → component_discovery bước B → generate_wireframe 4).

## Vì sao token là TÊN chứ không phải giá trị

Handoff từ `design-system` cố ý chỉ mang **tên** key. Nếu layout mang giá trị thật thì 20 story sẽ có 20 bản sao của cùng 1 mã màu — và không có cách nào (ngoài mắt người nhìn app đã build) biết được chúng có còn khớp nhau hay không. Trỏ tên thì tính nhất quán **kiểm được bằng máy** (Gate 5 điều 5), và đổi theme về sau chỉ sửa `tokens.json`, không phải sửa N file layout.

## Verify trước khi emit handoff sang `mobile`

**Cách tự kiểm rẻ nhất: chạy `python kernel/tools/validate.py` và đọc mã `E13`-`E22`.** Nó kiểm được đúng những thứ dưới đây bằng máy — đừng để Gate 5 bắt việc mình tự kiểm được.

- Số UI state ≥ số (acceptance criteria + error state) liệt kê cho story đó — thiếu là chưa xong.
- Mọi `component_need` ở bước 3.5 đã được resolve bằng `component_discovery` (bước A hoặc B) trước khi ghi vào `components` — không còn need nào bỏ ngỏ.
- **Từng component một** (không kiểm ở mức màn hình): mọi ref trỏ đích tồn tại thật (`appears_in_states`, `parent`, `interaction.target_state`, `validation[].error_state`, `registry_ref`); `parent` không tạo vòng.
- **Nhiều nhất 1 `emphasis: primary` mỗi state** — 2 primary = 2 CTA tranh tiêu điểm. Đây là **trần**, không phải đẳng thức: 0 primary hợp lệ với màn danh sách/so sánh, vì nâng 1 card lên là phá chính chức năng so sánh (xem `limits.json → design._primary_why_not_exactly_one`).
- Mọi `binds[]` có `on_null`; mọi text/badge có `text_overflow`; mọi control có `interaction` + `a11y.min_tap_target_ok`; mọi input có `validation`; mọi `disabled_when` khai tường minh.
- **Mọi khối chứa + `image`/`chart`/`media_player` có `responsive`**; không khối nào `axis` ngang + nhiều con + `wrap_behavior: none`; không khối chứa text nào có `min_height_dp` khác `null`; mọi `pinned: true` có `safe_area` khác `none`; `columns` phủ đủ `required_tiers` và đơn điệu theo bề rộng.
- `responsive_declared` phủ đủ `required_tiers` + `target_orientations`, `font_scale_verified` ≥ 2.0, `keyboard_avoidance` đúng với việc màn có input hay không.
- Mọi `data_bindings`/`binds[].field` trỏ tới field **tồn tại** trong `api-contracts.json` slice — field lạ = lỗi, sửa trước khi handoff.
- **Tự quét lại toàn bộ layout tìm giá trị style hard-code** (chuỗi bắt đầu `#`, số trần ở field spacing/radius/size). Còn 1 chỗ = Gate 5 fail.
- Mọi `token:` trỏ key **tồn tại** trong `token_keys` đã nhận từ handoff.
- `design_metrics_declared` khớp số đếm thật, và không vượt ngưỡng ở `kernel/config/limits.json` → `design`.
- Handoff body đủ field theo cạnh `designer-screen → mobile-screen` trong `kernel/rules/handoff-contracts.md`: `ui_states_count`, `data_bindings_summary`, `domains_applied` (+ `draft_domains` nếu có), `token_keys_used`, có slot quảng cáo hay không.
