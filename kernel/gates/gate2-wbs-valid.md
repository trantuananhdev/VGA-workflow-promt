# Gate 2 — WBS Valid

**Chạy khi:** ngay sau khi **một track mới được append** vào `kernel/memory/wbs.json` — `build` (bởi `generate_wbs`) hoặc `runtime` (bởi Orchestrator). Cũng chạy cho track `intake` lúc khởi tạo.

**Phạm vi kiểm: CHỈ node của track vừa append.** Không validate lại track cũ đã `done` — làm vậy sẽ fail oan (node `done` không còn thoả điều kiện "phải có ≥1 node ready", và node `intake` vốn không có `size`).

**Vì sao gate này khắt khe:** `wbs.json` là bảng tiến trình duy nhất của scheduler. Một DAG sai ở đây không gây lỗi ồn ào — nó làm scheduler **treo im lặng** (node ở `blocked` mãi, không ai báo lỗi). Phải bắt tại đây.

---

## Cách chạy Gate này

```bash
python kernel/tools/validate.py
```

Toàn bộ điều kiện dưới đây **đã được cài đặt** trong validator (mã kiểm tra `B*`, `C*`). Exit code `0` = pass. Đừng "đọc hiểu rồi tự kết luận pass" — chạy lệnh và đọc output.

> **Không có Python?** Script là đường nhanh, không phải điều kiện bắt buộc của Gate. Thiếu Python thì đọc danh sách điều kiện dưới đây và kiểm bằng tay/bằng AI — chậm hơn và tốn context hơn (phải nạp nhiều file), nhưng Gate vẫn thoả được. Nguyên tắc "không tự kết luận pass" vẫn giữ: phải kiểm từng điều, không đọc lướt rồi kết luận.


Kiểm tra riêng **luật sinh track** mà không cần dữ liệu thật (dùng khi vừa sửa `dag.json`):
```bash
python kernel/tools/validate.py --selftest
```

## Điều kiện PASS — tất cả đều là lookup xác định vào `kernel/contracts/dag.json`

**Tính đúng đắn của đồ thị (nhóm quan trọng nhất — chống treo im lặng):**
1. **Mọi `node_id` trong `depends_on` phải TỒN TẠI** trong `nodes` (được phép trỏ sang track khác, vd node `runtime` phụ thuộc node `PROJ-client-shell` của track `build`). Trỏ vào node không có = `blocked` vĩnh viễn.
2. **Không có chu trình** trong đồ thị `depends_on`.
3. **Track vừa append phải có ít nhất 1 node `status: ready`.** Nếu toàn bộ đều `blocked` thì track đó không bao giờ khởi động — chắc chắn sai.
4. **`node_id` duy nhất** toàn file, xuyên mọi track (nó là địa chỉ của message — trùng là routing sai).

**Khớp grammar (lookup `dag.json`):**
5. Với mỗi node, `depends_on` (dịch từ node_id về unit) phải đúng **quy tắc giao tập**:
   `depends_on == ( dag.units[unit].depends_on + conditional_depends_on thoả điều kiện ) \ {gate1} ∩ {unit có node trong CÙNG track}`
   Đây là quan hệ **bằng**, không phải "tập con tuỳ ý" — thiếu 1 dependency đáng lẽ phải có (unit đó CÓ node trong track) là lỗi nghiêm trọng: node sẽ chạy sớm trước khi input sẵn sàng. Cũng không được tự thêm quan hệ chéo (vd `client-screen` KHÔNG `depends_on` `dev-be`: 2 track song song, contract-first).
   Track `runtime` dùng thêm `runtime_feeds` để xác định **tập unit trong track**, nhưng `depends_on` vẫn tính từ `depends_on`/`conditional_depends_on` như trên.
6. **Số node đúng theo `scope`** (trong track `build`): `scope:project` → đúng 1 node; `scope:story` → 1 node/story đã signoff; `scope:release` → 1 node.
7. **Node có `unit` mang `only_if` chỉ được tồn tại khi MỌI biểu thức đúng** (`only_if` là **mảng**, ngữ nghĩa AND — văn phạm đóng ở `dag.json` → `_only_if_grammar`; validator mã `C35`/`C36`, biểu thức lạ = `B16`):

   | Biểu thức | Đúng khi | Chi phối unit |
   |---|---|---|
   | `story.Monetization == true` | story đó có `Monetization: true` trong `shared/PRD.md` | `ads-placement` |
   | `tech_stack.has_client == true` | `shared/contracts/tech-stack.json` → `delivery_targets` ∩ {`mobile_native`,`web_app`} ≠ ∅ | `design-system`, `designer-screen`, `client-shell`, `client-screen`, `ads-setup`, `ads-placement` |
   | `tech_stack.has_backend == true` | `delivery_targets` chứa `backend_service` | `dev-be` |

   Kiểm **2 chiều**, không chỉ 1: node tồn tại mà điều kiện sai = `C35` (làm việc không tồn tại — vd project web sinh node native shell); điều kiện đúng mà **không có node nào** = `C36` (việc bị bỏ im lặng — vd project có backend nhưng thiếu hẳn nhánh `dev-be`, `qa` sẽ pass mà chưa ai kiểm backend).

   > **Vì sao điều này giờ là điều kiện nặng:** trước đây kernel **mặc định** mọi project là mobile app — `mobile-shell`/`mobile-screen` luôn sinh node, nên `only_if` chỉ dùng cho đúng 1 việc nhỏ (`ads-placement` theo story). Từ khi loại sản phẩm do đề bài quyết định (`cto` ghi `delivery_targets`), `only_if` quyết định **hình dạng của cả WBS**. Sai một chiều nào cũng không làm file invalid về cú pháp — đó chính là lý do phải kiểm bằng máy ở đây.
8. Mọi `role` xuất hiện phải có `agents/<role>/manifest.json` tồn tại.
9. Unit thuộc agent có `core: false` trong **`agents/<role>/manifest.json`** (hiện tại: `ads` → `ads-setup`, `ads-placement`) chỉ được xuất hiện nếu agent đó nằm trong `active_capability_agents` của `kernel/memory/project-profile.json`. (`core` khai ở manifest, **không** ở `dag.json`.)
10. **`generate_wbs` không được tạo lại node cho unit `po`/`ba`/`cto`** — chúng thuộc track `intake`. Có node `po` mới trong track `build` = lỗi chạy vòng (`po` có `depends_on` rỗng → `ready` → spawn lại).

**Khởi tạo trạng thái:**
11. Node track `build` có `size` phải kèm `size_reasoning` (từ `skill_estimate_scope`) — không nhận nhãn S/M/L/XL suông. Node track `intake` không cần `size`.
12. `status` khởi tạo nhất quán: `depends_on` rỗng → `ready`; ngược lại → `blocked`. Không node nào được khởi tạo ở `running`/`done`/`failed`.
13. Mọi node có `gate.name` khớp `dag.json.units[<unit>].gate` (`null` nếu unit không có gate).

---

**Khi FAIL:** trả về `cto` xem lại. Điều 1/2/5 thường là dấu hiệu thiết kế kiến trúc tạo phụ thuộc không hợp lệ; điều 3/10/12 là lỗi khởi tạo của chính bên tạo track (`generate_wbs` hoặc Orchestrator).

**Riêng điều 7 fail thì phải phân biệt 2 nguyên nhân gốc khác nhau** — sửa sai chỗ là sửa 2 lần:
- `delivery_targets` **đúng** mà node lệch → lỗi của `generate_wbs` (bỏ bước lọc 0(b)). Sinh lại track `build`.
- `delivery_targets` **sai** → lỗi của `cto` ở Gate 1 (`skills/decide_tech_stack/`). Phải sửa `tech-stack.json` **rồi** sinh lại WBS; sửa `wbs.json` cho khớp cái sai là để lại 2 nguồn sự thật lệch nhau.

**Khi PASS:** Orchestrator vào PHA B của Event Loop — dispatch mọi node `status: ready` trong giới hạn `concurrency` của từng role.
