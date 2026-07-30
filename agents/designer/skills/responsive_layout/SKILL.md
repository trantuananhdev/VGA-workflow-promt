# skill_responsive_layout

**Dùng bởi:** `designer`, phase `designer-screen` — **bước 3.7**, sau khi `component_discovery` đã resolve mọi `component_need`, TRƯỚC bước 4 (chốt layout JSON). Phase `design-system` dùng mục 2 + mục 3 để chốt `responsive_contract` và để render `theme-preview.html` ở nhiều bề rộng.

**Mục tiêu:** điền `components[].responsive` + `responsive_declared` cho ĐÚNG 1 màn hình, sao cho layout còn đúng ở **máy hẹp nhất**, ở **cỡ chữ hệ thống 200%**, ở **hướng mà project cam kết hỗ trợ**, và khi **bàn phím mở lên**.

**Input:** layout đang dựng (bước 1–3.5) + `responsive_contract` từ `shared/design/tokens.json` (qua handoff của `design-system`) + mục **6** của file `design_patterns/<primary>/SKILL.md`

**Output:** field `responsive` trên mọi khối chứa + `responsive_declared` ở gốc `shared/design/screens/<story_id>.json`

---

## 1. Vì sao có skill này (đọc 1 lần, rồi bỏ qua)

Bốn field `on_null` / `text_overflow` / `disabled_when` / `validation` chặn lớp bug **của một component đứng yên**. Nhưng lớp bug hay gặp nhất khi app ra máy thật lại là **khối bị vỡ khi hoàn cảnh đổi**: máy 320dp, cỡ chữ 200%, xoay ngang, bàn phím che nút Gửi. Không mock data nào lộ ra — vì bạn (và mọi test) đang xem ở 393dp, cỡ chữ 100%, portrait, bàn phím đóng.

Vậy nên **hoàn cảnh cũng phải là field**, không phải thiện chí. Cưỡng chế: `validate.py` mã `E22` + Gate 5 điều 9.

## 2. Thang bậc — dùng đúng tên bậc trong `responsive_contract`

| Bậc | dp | Máy thật |
|---|---|---|
| `compact_small` | < 360 | 320–359dp: máy giá rẻ, máy cũ, **và mọi máy khi người dùng bật display-size lớn** — đây là bậc bị bỏ quên nhiều nhất |
| `compact` | 360–599 | 360 / 393 / 412 / 430dp — đa số điện thoại hiện nay |
| `medium` | 600–839 | tablet nhỏ, foldable mở, phone landscape |
| `expanded` | ≥ 840 | tablet lớn |

**Chỉ khai bậc mà project cam kết** (`responsive_contract.required_tiers`, suy từ `system-spec.md` mục `PROJ`). App pin portrait chỉ làm phone thì `["compact_small","compact"]` là đủ — khai thêm `medium`/`expanded` cho có là tự tạo 2 cột dữ liệu không ai kiểm.

Trần cứng: `columns` ở bậc < 600dp **≤ 2** (`limits.json → responsive.max_columns_compact`).

## 3. Bảy lớp vỡ layout — mỗi lớp có đúng 1 field chặn nó

| # | Lớp vỡ | Biểu hiện thật | Field chặn |
|---|---|---|---|
| a | **Tràn ngang** | hàng chip/nút/meta bị cắt mất phần tử cuối ở 320dp | `axis: horizontal` + `wrap_behavior` ≠ `none` |
| b | **Khoá chiều cao quanh text** | chữ bị cắt ngang thân, hoặc `...` giữa câu ở cỡ chữ lớn | `min_height_dp: null` cho mọi khối chứa text |
| c | **Cỡ chữ 200%** | nhãn + giá trị chồng nhau; nút cao 48dp chứa chữ 2 dòng | `responsive_declared.font_scale_verified` ≥ 2.0, và `sizing` ≠ `fixed` cho khối có text |
| d | **Landscape** | hero/ảnh/map chiếm hết chiều cao, nội dung tụt hết xuống dưới fold | `sizing: aspect_ratio` (không phải % chiều cao viewport) + `orientations` khai đúng |
| e | **Bàn phím** | bàn phím che đúng cái nút "Gửi"/"Tiếp tục" | `responsive_declared.keyboard_avoidance` |
| f | **Safe area** | tiêu đề lọt vào notch; CTA đáy nằm dưới gesture bar, bấm ra Home | `safe_area` + `pinned` |
| g | **Ảnh/video** | ảnh bị bóp méo, hoặc letterbox bị vẽ cứng vào khung nội dung | `sizing: aspect_ratio` + `aspect_ratio` |

Hai lớp hay bị bỏ nhất: **(b)** vì trên máy dev nó không bao giờ xảy ra, và **(f)** vì emulator mặc định không có notch.

## 4. Thứ tự degrade — cái gì bị bỏ TRƯỚC khi hết chỗ

`degrade_order` là **thứ tự bỏ/thu gọn**, phần tử đầu bỏ trước. Thứ tự đúng, từ ngoài vào:

```
1. Chrome trang trí   — gridline phụ, divider, khoảng đệm trang trí, icon lặp lại nhãn
2. Nhãn / phụ đề      — nhãn trục, mô tả phụ, caption, timestamp tương đối
3. Thông tin phụ trợ  — badge phụ, số liệu thứ cấp, avatar người phụ
4. Mật độ dữ liệu     — giảm SỐ ĐIỂM/SỐ DÒNG hiển thị (không giảm nội dung mỗi dòng)
```

**Không bao giờ** nằm trong `degrade_order`: dữ liệu chính, CTA `emphasis: primary`, đáp án của một câu hỏi, giá, số dư, đường thoát của state lỗi (`recovery_action`). Cắt những thứ này là làm sai chức năng màn hình, không phải làm gọn.

Nguồn của quy tắc này: `design_patterns/health-fitness` mục 6 phát biểu nó cho biểu đồ ("không bao giờ giảm dữ liệu trước khi giảm nhãn"); ở đây tổng quát hoá cho mọi khối.

## 5. Điền `responsive` theo từng `axis`

| `axis` | Khi nào | `columns` | `wrap_behavior` hợp lý |
|---|---|---|---|
| `vertical` | khối xếp dọc (card, section, form) | không khai | `none` (trục dọc không hết chỗ ngang) |
| `horizontal` | hàng ngang (chip row, meta row, action row) | **bắt buộc** | `wrap` với chip/nhãn · `scroll_horizontal` với carousel (con kế tiếp phải hở để báo cuộn được) · `stack_vertical` khi 2 khối to · `shrink` chỉ khi con co được thật |
| `grid` | grid card/ô | **bắt buộc**, ≤2 ở bậc < 600dp | `wrap` |
| `stack` | xếp lớp (scrim trên ảnh, overlay) | không khai | `none` |
| `none` | component lá (image/chart/media_player) | không khai | `none` |

Quy tắc phụ, hay sai:
- `columns` phải **đơn điệu không giảm** theo bề rộng — màn rộng hơn không được ít cột hơn.
- `sizing: fixed` chỉ dành cho icon / avatar / divider. Khối chứa text dùng `fill` hoặc `weight`.
- `pinned: true` **luôn** đi kèm `safe_area` khác `none`. Tối đa 2 vùng `pinned` mỗi state.
- `keyboard_avoidance: not_applicable` chỉ hợp lệ khi màn **không có** `input`/`select`/`search_field`. Màn có form mà CTA `pinned` ở đáy → `pin_cta_above_keyboard`; form dài → `scroll_content`.

## 6. Tự kiểm trước khi sang bước 4

Chạy `python kernel/tools/validate.py`, đọc mã `E22` — nó kiểm bằng máy đúng những điều dưới, đừng để Gate 5 bắt:

- Mọi khối chứa (`section`/`card`/`list`/`grid`/`row`/`column`) và mọi `image`/`chart`/`media_player` có `responsive`.
- Không khối nào `axis` ngang + nhiều con + `wrap_behavior: none`.
- `columns` phủ đủ `required_tiers`, đơn điệu, ≤ trần ở bậc compact.
- `degrade_order` chỉ trỏ **con thật** của chính khối đó; khối > 3 con thì không được rỗng.
- Không khối chứa text nào có `min_height_dp` khác `null`.
- Mọi `pinned: true` có `safe_area` khác `none`.
- `responsive_declared` phủ đủ `required_tiers` + `target_orientations`, `font_scale_verified` ≥ 2.0, `keyboard_avoidance` đúng với việc màn có input hay không.

Và một lượt **đọc bằng đầu**, máy không kiểm được: đọc lại màn ở bậc hẹp nhất — thứ tự `order` có còn hợp lý khi mọi thứ xếp dọc? CTA chính có còn ở trên fold?

## 7. Nguồn tham chiếu

**Tier 1:** Material 3 window size class (`compact <600dp`, `medium 600–839dp`, `expanded ≥840dp`); tap target 48dp (M3) / 44pt (Apple HIG); safe area / layout margin là khái niệm chính thống của cả 2 nền tảng. Lưu ý: `m3.material.io` và `developer.apple.com` render bằng JS nên `WebFetch` trả rỗng — đối chiếu qua token spec.

**Suy đoán của tôi (chỉnh nếu thấy sai):** mốc `compact_small` 360dp là tôi **chia nhỏ** bậc `compact` của M3, không phải bậc chính thống — lý do chia: giữa 320dp và 430dp là chênh 34% bề rộng, coi chúng như một bậc là chỗ sinh vỡ layout nhiều nhất. Thứ tự 4 nấc degrade ở mục 4 là tổng quát hoá từ `design_patterns/health-fitness`, không có spec nào chốt. Trần 2 cột ở bậc < 600dp là suy từ số học (360dp / 3 cột ≈ 110dp/cột), không phải quy định.

**Ranh giới IP:** file này chỉ chứa quan hệ và ngưỡng số học — không lấy bố cục, hex, hay tài sản của app nào.
