# skill_decide_tech_stack

**Dùng bởi:** `cto` (riêng). Chạy **1 lần/project**, trong track `intake`, **TRƯỚC khi ký Gate 1**.

**Mục tiêu:** Biến **tín hiệu nghiệp vụ của đề bài** thành 2 quyết định máy đọc được:
1. `delivery_targets` — project này có những phần nào (client mobile / client web / backend). Đây là **input của scheduler**: `generate_wbs` bật/tắt unit theo nó (`dag.json` → `only_if`).
2. `stack` cho từng target — platform/framework/language/build, và `platform_pack` mà agent `client` sẽ nạp.

**Input:** `kernel/memory/project-profile.json` → `product_signals` (do `po` ghi) + `shared/PRD.md` (Epic/User Story do `ba` viết) + `shared/architecture.md` đang dựng.

**Output:** `shared/contracts/tech-stack.json` (đầy đủ `delivery_targets` + `decision.evidence` + `entries`) và phần "Tech stack đã chọn" tương ứng trong `shared/architecture.md`.

> **Vì sao skill này tồn tại:** TRƯỚC ĐÂY hệ thống mặc định mọi project là app điện thoại — `dag.json`
> cố định 2 unit client-side, nên **không có bước nào quyết định loại sản phẩm**; nó là hằng số ẩn
> trong kernel. Hệ quả: một đề bài "cổng tra cứu công khai, cần Google index"
> vẫn sinh ra node native shell, và sai đó chỉ lộ ra khi có người đọc bằng mắt. Từ nay loại sản
> phẩm là **kết luận có bằng chứng**, không phải mặc định.

---

## Bước 1 — Kiểm tín hiệu ĐỦ chưa (không đoán thay PO)

Bắt buộc phải có giá trị (khác `null`) trước khi suy luận:

`how_users_arrive` · `primary_device` · `data_shared_between_users` · `needs_offline` · `needs_search_engine_discovery`

Thiếu bất kỳ tín hiệu nào trong 5 cái trên → mở Sync Session với `ba` (`type: request`, `max_turns: 3`) để `ba`/`po` bổ sung. **KHÔNG** tự điền hộ, và **KHÔNG** suy từ "app kiểu này thường là…". Tự đoán 1 tín hiệu ở đây là quyết định thay khách hàng về cả hình dạng sản phẩm.

`device_features_needed`, `compliance_constraints`, `existing_assets`, `hard_constraints` được phép rỗng — rỗng là **thông tin** (đã hỏi, không cần), khác `null` (chưa hỏi).

## Bước 2 — Suy `delivery_targets` (bảng quyết định, theo thứ tự)

**2a. Có client không, và loại nào**

| Tín hiệu | Kết luận |
|---|---|
| `how_users_arrive = he_thong_khac_goi_api` **và** `primary_device = khong_co_nguoi_dung_truc_tiep` | **không có client** → chỉ `backend_service` |
| `device_features_needed` chứa capability **chỉ có ở app đã cài** (chạy ngầm, quét NFC, sinh trắc học, nhận thông báo đẩy khi app đóng, dùng bluetooth liên tục) | `mobile_native` |
| `needs_offline = true` **và** `primary_device = dien_thoai` | `mobile_native` (web offline được nhưng phải thêm service worker + trần dung lượng — chỉ chọn khi các tín hiệu khác đẩy mạnh về web) |
| `needs_search_engine_discovery = true` | `web_app` (app trong store **không** được máy tìm kiếm index nội dung) |
| `how_users_arrive = mo_link_tren_browser` | `web_app` |
| `primary_device = may_tinh` | `web_app` |
| `how_users_arrive = nhieu_duong` **và** `primary_device = ca_hai` | cả `mobile_native` + `web_app` — **chỉ khi** PRD có story cho **cả hai** đường vào; nếu không thì chọn 1 và ghi cái kia vào `open_risks` |

**2b. Có backend không**

| Tín hiệu | Kết luận |
|---|---|
| `data_shared_between_users = true` | `backend_service` |
| `needs_realtime = true` | `backend_service` |
| `compliance_constraints` chứa `thanh_toan` / `du_lieu_suc_khoe` / `du_lieu_tre_em` | `backend_service` (không đặt bí mật/kiểm tra quyền ở client) |
| `existing_assets` có backend đang chạy | **KHÔNG** thêm `backend_service` mới — dùng lại; ghi rõ trong `architecture.md` và `open_risks` |
| không tín hiệu nào ở trên | không có backend riêng — dữ liệu local hoặc dịch vụ bên thứ ba (phải nêu tên trong `architecture.md`) |

**Xung đột giữa 2 bảng thì tín hiệu nào thắng:** capability thiết bị > cách người dùng tới > thiết bị chính. Lý do: capability là ràng buộc **cứng** (không có thì nghiệp vụ không chạy được), 2 cái sau là ràng buộc **mềm** (đổi cách phân phối vẫn làm được việc). Mọi lần thắng/thua như vậy **phải** ghi vào `alternatives_rejected`.

## Bước 3 — Chọn stack cho từng target

Thứ tự cân nhắc, **không** đảo:

1. **Ràng buộc cứng** — `compliance_constraints`, `hard_constraints`, capability bắt buộc. Loại thẳng stack không đáp ứng.
2. **`existing_assets`** — template/repo/kỹ năng sẵn có. Stack quen mà đủ tốt **thắng** stack tốt hơn trên giấy: rủi ro lớn nhất của project không phải hiệu năng framework, mà là đội không thành thạo thứ mình đang dùng. Repo này có stack pack nội bộ `vga31-kotlin` cho Android — nếu target là `mobile_native` + Android thì mặc định dùng nó, muốn khác phải ghi lý do.
3. **Phù hợp `expected_scale`** — đừng chọn kiến trúc cho quy mô chưa tồn tại.
4. **`platform_pack` phải có thật** — kiểm tên thư mục trong `agents/client/skills/platform/`. Chưa có pack cho stack đã chọn → vẫn được chọn, nhưng **phải** ghi vào `open_risks` rằng `client` sẽ phải bootstrap pack `draft` (xem `agents/client/skills/platform/SKILL.md` bước 3), vì đó là rủi ro lịch thật.

## Bước 4 — Ghi `tech-stack.json` (đúng shape, đủ bằng chứng)

```
delivery_targets            = kết luận bước 2 (mảng, KHÔNG rỗng)
decision.evidence           >= 1 phần tử CHO MỖI target, mỗi phần tử trỏ 1 tín hiệu THẬT
decision.alternatives_rejected >= 1 phần tử, kèm why_not cụ thể
decision.open_risks         = rủi ro đã biết + điều kiện phải xem lại
entries                     = ĐÚNG 1 entry cho mỗi target đã chọn, xoá hết entry mẫu còn lại
  roles của entry client   >= [designer, client, devops, qa]
  roles của entry backend  >= [dev-be, devops, qa]
  -> `devops` PHẢI có trong MỌI entry: pipeline phải khớp `build_system` của từng phần, và
     kiểu release ở Gate 6 khác nhau theo target. Thiếu `devops` ở entry nào thì
     context_compile lọc mất entry đó khỏi boot context của `devops-infra` — nó sẽ dựng
     pipeline cho nửa project và không có gì báo.
locked                      = true + locked_at, ngay trước khi ký Gate 1
```

Rồi cập nhật `shared/architecture.md` mục "Tech stack đã chọn" cho khớp — 2 file này là **cùng 1 sự thật ở 2 dạng**: prose cho người, JSON cho máy. Lệch nhau là lỗi.

## Không được làm

- **Không nhận chỉ định công nghệ của khách một cách suông.** Khách yêu cầu 1 stack cụ thể vẫn hợp lệ (ghi vào `hard_constraints`), nhưng `evidence` phải nói rõ đó là ràng buộc thương mại, và `open_risks` phải nêu cái mất về mặt kỹ thuật. Không có ghi chú đó thì người sau không hiểu vì sao chọn.
- **Không chọn cả `mobile_native` + `web_app` "cho chắc".** Mỗi target thêm vào là thêm 1 nhánh client trong DAG, thêm shell riêng, thêm compliance riêng — nhân đôi chi phí cho mọi story. Chỉ chọn 2 khi PRD có story cho cả hai đường vào.
- **Không bỏ trống `alternatives_rejected`.** Quyết định không so sánh với gì thì không kiểm được, và mọi tranh luận về sau sẽ phải làm lại từ đầu.
- **Không tự sửa `product_signals`** — file đó owner `po` (`kernel/contracts/data-ownership.json`). Thấy tín hiệu sai/thiếu → Sync Session, không sửa hộ.
- **Không đổi `tech-stack.json` sau khi `locked: true`** — từ đó nó chi phối cả DAG. Đổi = `doc_drift_detected` → `ba+cto` quyết định, vì có thể phải sinh lại WBS.

## Verify trước khi ký Gate 1

- `python kernel/tools/validate.py` → không có `E12`/`E23`/`E24`. Đây là điều kiện **có công cụ chấm**, nên theo `ORCHESTRATOR.md` bất biến #5: phải **chạy** công cụ, đọc file này không tính là đã kiểm.
- `delivery_targets` không rỗng, mọi phần tử thuộc tập cho phép; **mỗi** target có đúng 1 entry và **không** có entry lạc.
- Với mỗi target: `evidence` ≥ 1 và mỗi `signal` **tồn tại thật** trong `product_signals`/PRD (bịa tín hiệu = cùng lớp lỗi với bịa tên field trong `api-contracts.json`).
- Có client → `platform_pack` trỏ **thư mục thật**; chưa có pack thì đã ghi `open_risks`.
- Có backend → `datastore` khớp `shared/db-schema.md`.
- `architecture.md` và file này nói **cùng một stack**.
