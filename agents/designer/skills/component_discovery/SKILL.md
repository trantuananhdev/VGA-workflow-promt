# skill_component_discovery

**Dùng bởi:** `designer`, cả 2 phase (`design-system` và `designer-screen`) — giống `domain`, không riêng 1 phase như `generate_wireframe`.

**Mục tiêu:** Tìm thư viện UI/component thật, đã tồn tại, đúng tech stack của project — thay vì `client-screen` phải tự tìm hoặc tự build lại từ đầu mỗi story. Khoanh vùng tìm kiếm bằng `shared/contracts/tech-stack.json` (platform/ui_framework/language) chứ không tìm chung chung ("spin wheel library" mà không biết Android hay iOS là vô nghĩa).

**Input:**
- (`design-system`) slice `shared/contracts/tech-stack.json` (entry `story_id: "PROJ"`) — platform/ui_framework/language/build_system/min_sdk cấp toàn app
- (`designer-screen`) `token_keys` + `core_components_chosen` (tên, không phải chi tiết) từ handoff của `design-system` — không đọc lại `tech-stack.json` trực tiếp, kế thừa qua handoff; **`component_need` list** từ `generate_wireframe` bước 3.5 (xem `skills/generate_wireframe/SKILL.md`) — đây là danh sách nhu cầu, KHÔNG phải chủ đề tự suy diễn
- Chủ đề cần tìm: (`design-system`) hạ tầng UI cấp app — animation engine, icon set, ...; (`designer-screen`) **đúng** các `component_need` nhận được ở trên, không tự thêm/bớt category

**Output:**
- (`design-system`) `shared/design/component-registry.core.json` (1 file, project-scope)
- (`designer-screen`) `shared/design/component-registry/<story_id>.json` (1 file/story, trong thư mục — KHÔNG được ghi vào 1 file chung, xem `kernel/contracts/data-ownership.json` mục `_component_registry_split_why`)

---

## Quy trình

**(`design-system`)** áp dụng thẳng quy trình tìm-kiếm-lõi (bước 0-4 bên dưới) cho từng category cấp app.

**(`designer-screen`)** với MỖI `component_need` nhận từ `generate_wireframe` bước 3.5, làm theo đúng thứ tự:

```
A. CORE REUSE-CHECK (bắt buộc làm TRƯỚC, không được bỏ qua):
   Tra shared/design/component-registry.core.json (tên đã có qua handoff
   core_components_chosen) — nếu 1 core component đã chọn ĐÁP ỨNG được component_need này,
   DÙNG LẠI: ghi "reused_from_core": "<category>" vào entry, KHÔNG chạy quy-trình-tìm-kiếm-lõi
   bên dưới, KHÔNG tự search 1 lib khác cho cùng nhu cầu (tránh 2 story chọn 2 lib khác nhau
   cho cùng 1 việc).

B. MINI SEARCH — CHỈ chạy khi bước A không tìm được component core nào phù hợp:
   Chạy quy-trình-tìm-kiếm-lõi (bước 0-4 bên dưới), scope theo topic riêng của story
   (vd spin wheel cho US-002), ghi vào registry per-story.
```

### Quy trình tìm kiếm lõi (bước 0-4 — dùng bởi `design-system` trực tiếp, và bởi `designer-screen` bước B ở trên)

```
0. Đọc tech_stack (platform/ui_framework/language) — từ tech-stack.json (design-system)
   hoặc từ handoff design-system (designer-screen). KHÔNG tìm kiếm khi chưa biết tech stack.

1. Với mỗi category cần tìm, ghép từ khoá tìm kiếm CÓ tech stack:
   Android Compose  -> thêm "jetpack compose", "compose-compatible"
   iOS SwiftUI       -> thêm "swiftui", "spm" (Swift Package Manager)
   Flutter           -> thêm "flutter", "pub.dev"
   VD: "spin wheel library" SAI -> "android jetpack compose spin wheel library kotlin" ĐÚNG.

2. Tìm kiếm thật (GitHub/pub.dev/CocoaPods/SPM) — không liệt kê tên lib từ trí nhớ mà
   không xác minh. MỌI lib được chọn (`chosen`) PHẢI có `url` đã thực sự mở/resolve được,
   đặt `verified_url: true` chỉ khi đã làm việc này. Đây là bước bắt buộc để chặn
   hallucination — lib không tồn tại thật là rủi ro lớn nhất của skill này.

3. Đánh giá & xếp hạng — MỖI ứng viên đã tìm ở bước 2 (kể cả ứng viên bị loại) phải
   ghi lại, theo đúng thứ tự ưu tiên:
   (1) Tương thích ui_framework đã chọn (native, không phải view-wrapper nếu tránh được)
   (2) Hỗ trợ min_sdk/min OS của project
   (3) License permissive (MIT/Apache-2.0) — license hạn chế phải nêu rõ trong `reason`
   (4) "popularity_signal": { "metric": "github_stars|pub_likes|downloads", "value": <số thật> }
       — tiêu chí phân định CUỐI CÙNG giữa các ứng viên còn lại sau (1)-(3), tức
       "được tin dùng bởi số đông nhất" LÀ SỐ, không phải cảm tính "còn maintain".
       Không lấy được số thật (lib quá mới/không public số liệu) -> nêu rõ trong `reason`,
       KHÔNG được bỏ trống field `popularity_signal`.
   `alternatives_considered` (>= 1 phần tử, có url + popularity_signal riêng) là BẮT BUỘC
   khi `custom_needed: false` — chỉ ghi 1 mình ứng viên thắng mà không so sánh là chưa đủ,
   vì không ai kiểm chứng được "tốt nhất" nếu không thấy ứng viên bị loại.

4. KHÔNG có lib nào đủ tiêu chí -> KHÔNG được chọn đại 1 lib không phù hợp.
   Ghi `"chosen": null, "custom_needed": true` kèm `custom_note` giải thích vì sao,
   để `client-screen` biết cần tự implement chứ không tốn công tìm thêm.

5. Ghi vào đúng file theo phase (xem Output ở trên). KHÔNG trộn core và story-level.
```

## Vì sao `verified_url` là điều kiện, không phải gợi ý

Domain skill chỉ đưa ra pitfall/pattern (không cần xác minh vì đó là tri thức thiết kế). Component discovery đưa ra **tên riêng của phần mềm thật** — sai 1 cái là `client-screen` build theo 1 dependency không tồn tại. Đây là lý do `verified_url`/`custom_needed` là 2 field máy có thể kiểm được (Gate 5 điều 7, Gate 7 điều 7) thay vì chỉ dựa vào lời văn "đã kiểm tra".

## Verify trước khi emit handoff

- Mọi entry có `chosen` khác `null` → `chosen.url` không rỗng và `verified_url: true`.
- Mọi entry có `chosen` khác `null` và không phải `reused_from_core` → có `popularity_signal.value` và `alternatives_considered` (>= 1 phần tử).
- Mọi entry không tìm được lib phù hợp → `chosen: null`, `custom_needed: true`, có `custom_note`.
- Không có entry nào vừa `chosen: null` vừa `custom_needed` không set (thiếu = chưa xong).
- (`designer-screen`) Mọi `component_need` từ `generate_wireframe` bước 3.5 đã được resolve — hoặc `reused_from_core`, hoặc có kết quả mini search (bước B), không còn need nào bỏ ngỏ.
- (`design-system`) `core_components_chosen` (tên, không phải url) được đưa vào handoff sang `designer-screen`.
- (`designer-screen`) `components_used` (tên + `custom_needed`) được đưa vào handoff sang `client-screen`.
