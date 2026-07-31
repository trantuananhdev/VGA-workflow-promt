# lessons_learned.md — Ghi bởi Evolution protocol (xem ORCHESTRATOR.md §9)

Chỉ ghi khi: 1 pattern có thể tái dùng, trái trực giác, hoặc gây tốn nhiều turns/gate-fail. Mỗi mục nêu rõ nguyên nhân gốc và rule/skill nào đã được cập nhật để tránh lặp lại — không ghi chung chung.

---

<!-- Ví dụ format:
## [YYYY-MM-DD] US-014 — Sync Session BA-CTO vượt max_turns 2 lần liên tiếp
Nguyên nhân gốc: PRD thiếu acceptance criteria cho case OTP hết hạn, khiến CTO phải hỏi lại nhiều lần.
Đã cập nhật: agents/ba/rules/_role_policy.md — bắt buộc mỗi story phải có acceptance criteria
cho MỌI edge case liệt kê, không chỉ happy path, trước khi emit handoff sang CTO.
-->

## [2026-07-29] Nhánh Design — không có tầng style SSOT, và không có primitive "chờ người quyết định"

Nguyên nhân gốc (4 lỗi cùng 1 gốc: **thiếu bước cấp project cho design**):
1. `designer` chỉ có unit scope `story` → mỗi story tự quyết màu/spacing/typography. Không có SSOT cho style như `architecture.md` là SSOT cho tech stack, nên tính nhất quán của app phụ thuộc việc 2 lần chạy skill khác nhau có tình cờ giống nhau hay không — không kiểm được bằng máy.
2. Không ai **nhìn thấy** thiết kế trước khi code (`shared/design/<story>.json` là JSON máy đọc, handoff thẳng cho `client-screen`). Hướng style sai chỉ lộ ra ở Gate 4 hoặc khi khách xem build.
3. Hệ thống chỉ có 2 dạng "người can thiệp": `waiting_human` (= LỖI, sau khi fail ≥3 lần) và Sync Session (agent↔agent). **Không có** primitive cho "dừng bình thường, chờ người quyết định thẩm mỹ". Nếu dùng lại `waiting_human` thì `gate.consecutive_fail` mất nghĩa và `today.md` báo "blocker" cho một bước hoàn toàn bình thường.
4. `designer` chỉ có 1 skill generic cho mọi loại app → không tận dụng pattern/pitfall đã biết của từng domain, dù hệ thống đã có tiền lệ domain-knowledge tách rời (`shared/capabilities/ads.json`).

Đã cập nhật:
- `kernel/contracts/dag.json` — tách `designer` thành 2 phase `design-system` (project) + `designer-screen` (story), theo đúng mẫu `client-shell`/`client-screen`. `designer-screen.depends_on` thêm `design-system` — **ngoại lệ có chủ đích** với nguyên tắc "chỉ chờ Gate 1", đã ghi lý do + đánh đổi trong `kernel/rules/routing-table.md`.
- `kernel/gates/gate7-design-system-lock.md` (mới) + status node mới `awaiting_human_decision`, tách hoàn toàn khỏi `waiting_human`; cưỡng chế bằng `validate.py` mã `C31`/`C33`/`C34`, hiển thị riêng trong `digest.py`, quay lại bằng `resume.py --decision`.
- `kernel/gates/gate5-design-complete.md` — thêm điều 5 (token phải trỏ key tồn tại trong `tokens.json`, hard-code = fail) và điều 6 (domain tag hợp lệ). Điều 5 là thứ biến "nhất quán style" từ cảm nhận thành kiểm được bằng máy.
- `kernel/contracts/data-ownership.json` — bỏ entry thư mục `shared/design/`, khai theo từng writer (đúng tiền lệ `shared/capabilities/`); layout story chuyển vào `shared/design/screens/`.
- `agents/ba/AGENT.md` — checklist UX-state bắt buộc (loading/empty/error/permission_denied/partial/offline/session_expired) + khối `story:PROJ` design intent, **trước** Gate 1. Sync Session `designer ↔ ba` từ nay là lưới an toàn cuối, không còn là tuyến đầu.
- `agents/ba/skills/classify_domain/` (mới) → `shared/contracts/domain-map.json`; `agents/designer/skills/domain/` (mới, 3 domain đầu: `on-demand-booking`, `e-commerce-marketplace`, `fintech-payment`).

## [2026-07-29] BUG CÓ SẴN — validate.py `C10` báo lỗi sai trên mọi node story phụ thuộc node project

Nguyên nhân gốc: `check_wbs` gom "unit có node trong track này" theo **`track_id`**, nhưng track `build` có **nhiều `track_id` cùng lúc** (`PROJ` cho scope project, `REL` cho release, `US014`/`US015`… cho story — xem `wbs.json._tracks`). Vì vậy `PROJ-client-shell` bị coi là "không có node trong track" của story US014, phép giao tập loại nó ra, và `US014-client-screen` (`depends_on: [US014-designer-screen, PROJ-client-shell]`) bị báo `C10` sai. Lỗi này **đã tồn tại từ trước** thay đổi nhánh design — nó chưa bao giờ nổ vì `wbs.json` trong repo còn rỗng (`C1` bỏ qua toàn bộ kiểm C-group), và chính `wbs.json._node_example_build` là một ví dụ sẽ fail. Mọi project thật sẽ gặp ngay ở story đầu tiên.

Đã cập nhật: `kernel/tools/validate.py` — gom peer theo **`track`** với track `build`, vẫn theo `track_id` với `intake`/`runtime` (2 track runtime khác nhau có thể có entry unit khác nhau, gộp lại sẽ tạo lỗi sai theo chiều ngược). Đã xác minh bằng node giả: trước khi sửa 2 lỗi `C10` sai, sau khi sửa 0 lỗi, và track `runtime` vẫn đúng.

## [2026-07-29] BUG CÓ SẴN — node `scope: project` nhận Tier 2 rỗng

Nguyên nhân gốc: `context_compile.gather_tier2()` `return` ngay khi `story_id is None`, mà anchor-tag chỉ có trục `story:`. Nên `client-shell`, `devops-infra`, `ads-setup` (và `design-system` mới) **không nhận được gì** từ `shared/` — dù `AGENT.md` của chúng khai là "đọc anchor-tag slice của `architecture.md`/`system-spec.md`". Với `design-system` điều này là chí mạng: nó phải suy ra design token mà không có đầu vào nào về brand/đối tượng người dùng/app tham chiếu → sẽ bịa.

Đã cập nhật: `kernel/tools/context_compile.py` — dùng khoá `PROJ` làm story key cho node `scope: project`/`release` (`PROJECT_STORY_KEY`). Tương thích ngược hoàn toàn: chưa có block nào gắn `story:PROJ` thì kết quả y như trước. Đã thêm khối `story:PROJ` mẫu vào `shared/PRD.md` (design intent, do `ba` viết) và `shared/system-spec.md` (ràng buộc platform, do `cto` viết).

## [2026-07-29] Bản vá lần 1 của nhánh Design để lộ thêm 2 lỗ hổng — đã vá tiếp

Tự review lại toàn bộ chuỗi client → PO → BA → CTO → Gate 1 → `design-system`/`designer-screen` sau khi đã áp bản vá lần 1, phát hiện 2 vấn đề:

**1. Gate 1 chưa cưỡng chế nghĩa vụ mới của `ba`.** `kernel/gates/gate1-ba-cto-signoff.md` vẫn giữ nguyên điều kiện PASS cũ — không kiểm checklist UX-state, khối `PRD.md#PROJ`, hay độ phủ `domain-map.json`. `ba` có thể bỏ qua cả 3 việc mới thêm ở `agents/ba/AGENT.md` mà Gate 1 vẫn pass — vi phạm chính nguyên tắc "No LGTM without proof" của hệ thống.

Đã cập nhật: `kernel/gates/gate1-ba-cto-signoff.md` thêm điều 7-8 (cơ chế, validator kiểm) + điều 4 (nội dung, cto xác nhận đã đọc). `kernel/tools/validate.py` thêm nhóm kiểm mới `check_design_prereqs()` (mã `E9`: thiếu khối `story:PROJ` role `designer` trong `PRD.md`; `E10`: story thật thiếu entry trong `domain-map.json`; `E11`: `domain-map.json` không tồn tại/không parse được). Đã tiêm lỗi thật để xác minh cả 2 mã bắt đúng (thêm story không khai domain → `E10` nổ; xoá khối `PROJ` → `E9` nổ), rồi khôi phục file gốc.

**2. Bug do chính bản vá lần 1 gây ra: guard "Tier 2 rỗng" ở `context_compile.py` không áp dụng cho node scope=project.** Sửa lần 1 dùng khoá `PROJ` bên trong `gather_tier2()`, nhưng điều kiện chặn dispatch `if story_id and not blocks: die()` vẫn dùng biến `story_id` **gốc** (luôn `None` với node scope=project) — nên điều kiện không bao giờ đúng, và `design-system` có thể dispatch với Tier 2 **rỗng hoàn toàn** mà không lỗi, không cảnh báo. Lỗi chỉ lộ ra khi người xem `theme-preview.html` thấy 3 phương án vô hồn — muộn hơn nhiều so với việc bắt ngay tại Gate 1 (mục 1).

Đã cập nhật: tách biến `tier2_key` (khoá quét nội dung) khỏi `story_id` (metadata giữ nguyên `None`, ghi vào frontmatter boot context), bỏ điều kiện `if story_id` để guard áp dụng **đều** cho mọi node. Đã kiểm bằng `gather_tier2()` trực tiếp cho cả 4 role có unit scope=project/release (`designer`, `client`, `devops`, `ads`) — cả 4 đều có ≥1 nguồn nội dung thật (nhờ thêm khối `story:PROJ` vào `shared/architecture.md` với đúng role `ads` mà `ads-setup` cần), và khi xoá thử các khối `PROJ` thì cả 4 đều bị chặn đúng như kỳ vọng — không có role nào bị bỏ sót/regression.

## [2026-07-31] Kernel hết mặc định Mobile — đề bài quyết định tech stack (gián tiếp)

**Vấn đề gốc:** loại sản phẩm là **hằng số ẩn** của kernel. `dag.json` cố định 2 unit client-side tên `mobile-shell`/`mobile-screen`, role client-side tên `mobile`, và tri thức Android nằm **thẳng** trong `agents/mobile/skills/`. Hệ quả có 3 tầng, không tầng nào tự báo lỗi:

1. **Không có bước nào quyết định loại sản phẩm.** Một đề bài "cổng tra cứu công khai, cần Google index" vẫn sinh node native shell; sai đó chỉ lộ khi có người đọc bằng mắt.
2. **Project web nhận đúng bộ skill sai.** `agents/mobile/skills/` toàn skill Android/store; không có cơ chế nào phát hiện agent đang đọc tri thức của nền tảng khác.
3. **`devops-release` chỉ có 1 đường: submit store.** Với web/API, `check_app_store_policy` kiểm một lớp gác cổng **không tồn tại** (tạo cảm giác đã kiểm), trong khi thứ thật sự cần kiểm — URL live, health, rollback — không có điều kiện nào. Web không có store review nên **không ai** gác cổng.

**Đã cập nhật — chuỗi quyết định mới (tín hiệu nghiệp vụ → kết luận kỹ thuật → hình dạng DAG):**

- `kernel/memory/project-profile.json` — thêm `product_signals` (owner `po`): tín hiệu **nghiệp vụ** của đề bài (`how_users_arrive`, `primary_device`, `data_shared_between_users`, `needs_offline`, `needs_search_engine_discovery`, …). PO **không** được ghi tên nền tảng/framework; khách chỉ định công nghệ thì vào `hard_constraints`, không thành quyết định.
- `agents/cto/skills/decide_tech_stack/` (mới) → `shared/contracts/tech-stack.json`: `delivery_targets` ⊂ `{mobile_native, web_app, backend_service}` + `decision.evidence`/`alternatives_rejected`/`open_risks` + 1 `entries` cho mỗi target (kèm `platform_pack`). `locked: true` trước khi ký Gate 1.
- **Vì sao `delivery_targets` ở `tech-stack.json` mà không ở `project-profile.json`** dù cả 2 đều là dữ liệu cấp project: profile owner `po`, kết luận stack owner `cto` — gộp 1 file là 2 writer = race (`data-ownership.json`). Tín hiệu ở file của PO, kết luận ở file của CTO.
- `kernel/contracts/dag.json` — `only_if` đổi thành **mảng** biểu thức (AND) với **văn phạm đóng** 3 biểu thức (`_only_if_grammar`): `story.Monetization == true`, `tech_stack.has_client == true`, `tech_stack.has_backend == true`. Cú pháp tự do sẽ khiến `generate_wbs` (LLM) và `validate.py` (Python) hiểu khác nhau về việc unit nào tồn tại — đúng lớp lỗi đã khiến `manifest.depends_on` và `process-table.json` bị bỏ. Biểu thức lạ = `B16`, fail-closed.
- `agents/mobile/` → **`agents/client/`**, unit `client-shell`/`client-screen`; tri thức nền tảng chuyển vào `agents/client/skills/platform/<pack>/` (`mobile-native/` + stack pack `vga31-kotlin/`, `web-spa/` mới). Agent chọn pack ở **bước 0** theo `tech-stack.json`, không đoán. Cùng cơ chế `skills/domain/` của `designer` đã chạy tốt: `AGENT.md` giữ phần **vai trò** (bất biến), pack giữ phần **nền tảng** (thay theo đề bài).
- `shared/capabilities/native.json` → **`client.json`**: khối chung ở gốc + khối `mobile`/`web` riêng, `target` phải khớp `tech-stack.json`. Vẫn 1 writer (`client-shell`) vì 1 project có đúng 1 vỏ client.
- `kernel/gates/gate1-…` điều 10-11 (delivery_targets có bằng chứng + `product_signals` đủ 5 tín hiệu); `gate2-…` điều 7 kiểm **2 chiều**; `gate6-…` rẽ nhánh theo từng target (store submit / URL live / API health), điều kiện monitoring giữ nguyên cho mọi target vì nó là mối nối duy nhất sang Runtime Mode.
- `agents/devops/skills/verify_web_deployment/` (mới) — đối ứng `check_app_store_policy` cho nhánh web/API; **bắt buộc đã thử rollback thật** (điều 7/12), vì đó là lớp gác cổng gần nhất với vai trò của bản review store.
- `skills/generate_wbs/SKILL.md` bước 0 — **2 bộ lọc độc lập**: (a) core/capability ("công ty có bật agent đó không", `po` ghi), (b) `only_if` theo `delivery_targets` ("sản phẩm có phần đó không", `cto` ghi). Thêm `wbs.json.build_context` để người đọc sau phân biệt "thiếu vì không cần" với "thiếu vì bị quên".
- `kernel/tools/validate.py` — `eval_only_if()` + `tech_ctx()`; mã mới `B16` (biểu thức lạ), `C35` (node cho nhánh project **không có** → nằm `ready` mãi), `C36` (nhánh đáng lẽ phải có mà **thiếu hẳn** → gate xuôi dòng vẫn pass, không ai kiểm), `E23`/`E24` (`delivery_targets` + entry + `platform_pack` trỏ thư mục thật). `--selftest` mô phỏng **3 hình dạng sản phẩm** thay cho giả định "mọi project là mobile app".

**Đã xác minh bằng dữ liệu giả (không chỉ đọc lại file):** repo hiện tại `validate.py` 0 ERROR, `--selftest` exit 0 với cả 3 hình dạng (`qa` chờ đúng `[client-screen, dev-be]` / `[client-screen]` / `[dev-be]`). Tiêm lỗi thật: WBS có `PROJ-client-shell` khi `delivery_targets=[backend_service]` → `C35` nổ đúng; thiếu nhánh `dev-be` khi có backend → `C36` nổ đúng; WBS `web_app` hợp lệ → 0 lỗi (negative control).

### BUG CÓ SẴN phát lộ trong đợt này — `C19` báo lỗi sai trên mọi story của project thật

`C19` ("track toàn bộ blocked") gom node theo **`track_id`**, nhưng track `build` có nhiều `track_id` cùng lúc, và node của 1 story **hoàn toàn bình thường** khi toàn bộ `blocked` lúc mới sinh (chúng chờ `PROJ-design-system`/`PROJ-client-shell`). Đây đúng là lỗi mà `C10` đã gặp và đã sửa ngày 2026-07-29 — nhưng `C19` bị bỏ sót trong lần đó, và chưa bao giờ nổ vì `wbs.json` template chưa có node nào. Nó lộ ra ngay khi chạy thử WBS `web_app` đầu tiên.

Đã cập nhật: gom theo `track` với `build` (cả track phải có ≥1 đường chạy), vẫn theo `track_id` với `intake`/`runtime`. **Bài học lặp lại lần 2:** mỗi khi sửa 1 chỗ dùng `track_id` làm phạm vi gom, phải `grep` toàn bộ validator tìm chỗ còn lại — phạm vi gom là loại giả định dễ sai đồng loạt ở nhiều mã kiểm khác nhau.
