# handoff-contracts.md — Mỗi cạnh trong DAG truyền chính xác cái gì

> **Nguyên tắc nền:** agent GỬI phải **cô đặc** đủ thông tin vào body message, để agent NHẬN
> làm được việc mà **không cần mở lại file gốc**. Đây là cách khiến "đọc ngắn" thành thật —
> Tier 2 (`context_compile`) vẫn có thể dài nếu story phức tạp, còn message thì luôn ngắn.
>
> Con trỏ (`shared/...#anchor`) chỉ để mở khi agent nhận **thực sự cần chi tiết**, không phải đọc mặc định.
>
> Cạnh nào hợp lệ: xem `kernel/contracts/dag.json` (`units[*].feeds`). File này quy định **nội dung** truyền qua cạnh đó.

---

## Khung chung cho mọi handoff body

```markdown
## Tóm tắt
<2-4 dòng: đã làm xong cái gì, có gì bất thường agent nhận CẦN biết>

## Bàn giao          ← các field bắt buộc riêng theo từng cạnh, xem bảng dưới
<...>

## Bằng chứng        ← chỉ ĐOẠN QUYẾT ĐỊNH, ≤20 dòng. File đầy đủ đi qua artifact_refs
```
flutter analyze: No issues found. (2.1s)
flutter test: 00:04 +12: All tests passed!
```

## Con trỏ (mở nếu cần)
- `shared/...#anchor`
```

### ⚠ Giới hạn kích thước body — **120 dòng / 8000 ký tự**

Body message được nạp vào context của agent nhận. Một log test 5000 dòng dán vào body sẽ làm **nổ `max_context_tokens`** của agent đó, mà **Gate 0 không chặn được** — nó chỉ kiểm bundle Tier 0+1+2, không kiểm kích thước message.

Vì vậy: **log/output dài để ở FILE, message chỉ mang con trỏ + đoạn quyết định.**

```yaml
artifact_refs:
  - logs/US014-mobile-screen/flutter-analyze.txt
  - logs/US014-mobile-screen/flutter-test.txt
```

Gate 0 kiểm mọi path trong `artifact_refs` có tồn tại thật (validator `D15`); giới hạn body do `D14` cưỡng chế. Nguyên tắc "No LGTM without proof" **không đổi** — bằng chứng vẫn phải có thật và kiểm được, chỉ là nó nằm ở file thay vì nhét hết vào body.

Nếu agent gửi thấy có điểm mơ hồ **chưa giải quyết**, KHÔNG được nhét vào handoff rồi bàn giao — phải mở Sync Session (`type: request`) trước. Handoff nghĩa là "xong, đủ để người sau làm tiếp".

---

## Bảng hợp đồng theo từng cạnh

| Cạnh | `## Bàn giao` phải có | Agent nhận chỉ cần đọc |
|---|---|---|
| `po → ba` | `epic_id`, mục tiêu **đo lường được**, `size` + `size_reasoning` từ `estimate_scope` | Body. Không cần đọc `epics.json`. |
| `ba → cto` | `story_id`, số edge case, số acceptance criteria, `Monetization: true\|false`, **danh sách điểm cần CTO xác nhận khả thi** | Body + `PRD.md#<story>` (cần đọc kỹ vì CTO phải phủ hết edge case) |
| `cto → gate1` (signoff) | Xác nhận **từng** edge case đã có phương án kỹ thuật; `api-contracts.json` đã valid + **freeze** | Gate 1 kiểm, không phải agent |
| `cto → design-system` | Platform mục tiêu + min OS (ảnh hưởng quy ước iOS HIG vs Material), mức accessibility bắt buộc đạt, ràng buộc kỹ thuật ảnh hưởng style (vd theme tối bắt buộc, font hệ thống) | Body + `PRD.md#PROJ` (**design intent cấp project** do `ba` viết: brand, đối tượng người dùng, app tham chiếu nếu clone) |
| `cto → designer-screen` | `story_id`, danh sách **error state** cần vẽ (từ `system-spec.md`), tên các field dữ liệu sẽ hiển thị | Body + `PRD.md#<story>` (user flow) |
| `cto → dev-be` | `story_id`, danh sách endpoint, bảng DB bị ảnh hưởng, migration có/không | Body + `db-schema.md#<story>` + `api-contracts.json#<endpoints>` |
| `cto → mobile-shell` | Danh sách permission cần khai **kèm `story_id` lý do** (least-privilege), min OS target, cần push/deep-link không | Body + `system-spec.md#<story>` |
| `cto → devops-infra` | Stack đã chọn, môi trường cần dựng, ràng buộc hạ tầng | Body + `architecture.md#<story>` |
| `cto → ads-setup` | Platform, yêu cầu vùng địa lý (ảnh hưởng GDPR/ATT) | Body |
| `design-system → designer-screen` | `chosen_theme`, **`token_keys`** (danh sách key phẳng theo 5 nhóm `color`/`typography`/`spacing`/`radius`/`elevation` — để designer-screen không phải mở lại `tokens.json` mọi story), `a11y_measured` (số đo contrast thật từng cặp), `locked_at` | Body. Chỉ mở `shared/design/tokens.json` khi cần giá trị thật (bình thường chỉ cần TÊN key). |
| `designer-screen → mobile-screen` | `story_id`, `ui_states_count`, **`data_bindings_summary`** (tên field đã dùng — để mobile không phải mở lại `api-contracts.json`), **`domains_applied`** (+ `draft_domains` nếu có), `token_keys_used`, có slot quảng cáo hay không | Body. Chỉ mở `shared/design/screens/<story>.json` khi cần layout chi tiết. |
| `mobile-shell → mobile-screen` | Danh sách permission/feature **đã dựng thật** (khớp `native.json`), kết quả `check_platform_compliance` | Body. Không cần đọc lại manifest/plist. |
| `mobile-screen → qa` | `story_id`, **kết quả** lint/test (dòng tổng kết, không phải nguyên văn) + `artifact_refs` trỏ file log đầy đủ, PR link + CI status, đã test với mock hay backend thật | Body + `PRD.md#<story>` (QA cần acceptance criteria gốc để đối chiếu — đây là ngoại lệ **cố ý**: QA phải đọc bản gốc, không tin bản cô đặc của Dev) |
| `dev-be → qa` | `story_id`, endpoint đã xong, **kết quả** lint/test + `artifact_refs` trỏ file log, PR link + CI status | Body + `PRD.md#<story>` + `api-contracts.json` (cùng lý do trên) |
| `mobile-screen → ads-placement` | `story_id`, screen đã xong, vị trí slot quảng cáo trong layout | Body + `shared/design/screens/<story>.json` (cần toạ độ slot thật) |
| `ads-setup → ads-placement` | Network + mediation đã chọn, **kết quả test consent 3 case** (đồng ý/từ chối/ngoài GDPR) | Body |
| `ads-placement → qa` | Loại + tần suất quảng cáo đã chèn, kết quả `check_ad_policy` (`violations: []`) | Body + `PRD.md#<story>` (đối chiếu tần suất PRD đã chốt) |
| `qa → devops-release` | Kết quả **từng** acceptance criteria (pass/fail từng dòng), coverage %, smoke test — kèm `artifact_refs` trỏ file log thật. Tuyệt đối không chỉ ghi "đã pass" | Body |

---

## Cạnh `design-system → designer-screen` — vì sao truyền TÊN key chứ không truyền giá trị

`token_keys` là danh sách **tên** (`color.primary`, `spacing.md`…), **không** phải giá trị (`#1A56DB`, `16`). Đây không phải để tiết kiệm context mà là ràng buộc thiết kế: `designer-screen` **không được biết** giá trị thật thì mới không thể hard-code nó vào layout. Nếu message mang cả giá trị, một lúc nào đó agent sẽ dán `#1A56DB` vào layout "cho nhanh" và Gate 5 điều 5 sẽ fail — tốn 1 vòng retry cho một lỗi đáng lẽ không xảy ra được.

Đây là cạnh **1 → N** duy nhất trong hệ thống mà cùng 1 handoff mở khoá **mọi** story (`RECOMPUTE_READY()` chuyển toàn bộ node `<STORY>-designer-screen` sang `ready` cùng lúc). Vì vậy body phải đủ để dùng cho **bất kỳ** story, không được chỉ nói về story đầu tiên.

## Ngoại lệ cố ý: QA luôn đọc bản gốc

Mọi cạnh khác đều theo hướng "tin bản cô đặc của agent gửi". Riêng `→ qa` thì **QA phải mở `PRD.md` gốc** để đối chiếu, không tin phần Tóm tắt của Dev. Lý do: nếu Dev hiểu sai acceptance criteria, bản cô đặc của Dev sẽ **mang theo đúng cái hiểu sai đó**, và QA đọc lại chỉ để xác nhận cái sai. Đây chính là vai trò "đóng vai ác" trong `agents/qa/AGENT.md` — chi phí đọc thêm ở đây là có chủ đích, không phải thiếu tối ưu.

## Khi 1 cạnh cần thêm field mới

Sửa bảng trên **và** cập nhật `agents/<role>/AGENT.md` (mục Output hợp lệ) của agent gửi. Nếu thấy 1 cạnh liên tục phải hỏi lại bằng Sync Session cùng 1 loại câu hỏi → đó là dấu hiệu hợp đồng cạnh đó thiếu field; ghi vào `shared/lessons_learned.md` rồi bổ sung vào đây (lớp Evolution, `ORCHESTRATOR.md` §9).
