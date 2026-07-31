# Gate 6 — Release Verified

> Số gate đánh theo **thứ tự tạo ra**, không theo DAG. Đây là gate **cuối cùng** của vòng đời — sau Gate 4.

**Chạy khi:** `devops` (phase `devops-release`) emit `type: handoff` báo đã release.

**Vì sao cần:** trước đây `dag.json` để `devops-release.gate: null` — nghĩa là **bước đưa app lên chợ hoàn toàn không được kiểm**. Gate 4 chỉ xác nhận *code đúng*, không xác nhận *release thành công*. Hệ quả thực tế: pipeline chạy, node chuyển `done`, hệ thống coi như xong — nhưng app có thể chưa lên store, hoặc lên mà monitoring chưa gắn (khi đó `crash_alert` không bao giờ về, **toàn bộ Runtime Mode chết âm thầm**).

---

## Điều kiện PASS

**Chung cho mọi loại sản phẩm:**
1. **Artifact tồn tại thật:** package/bundle/image đã build, đường dẫn khai trong `artifact_refs` và Gate 0 (`D15`) đã kiểm file có thật.
2. **Tag semver đã tạo:** `git tag` khớp `v<major>.<minor>.<patch>`, KHÔNG dùng `latest` (xem `skills/git_workflow/SKILL.md`).
3. **Monitoring đã nhận được event thật** — `setup_monitoring` phải đã trigger 1 lỗi giả lập và thấy message `crash_alert`/`error_alert` xuất hiện trong `kernel/mailbox/`.
4. **Đã merge vào `main`** — merge chính là hành động trigger pipeline, không có bước deploy tay song song với pipeline.

**Theo TỪNG `delivery_target` trong `shared/contracts/tech-stack.json` — phải đủ cho MỌI target đã chọn:**

| Target | Điều kiện riêng | Bằng chứng |
|---|---|---|
| `mobile_native` | `check_app_store_policy` trả `violations: []`; bản build đã submit lên store/track nội bộ | link hoặc ID bản submit + output skill (`agents/devops/skills/check_app_store_policy/`) |
| `web_app` | `verify_web_deployment` đạt điều 1-7: URL production trả `200`, TLS hợp lệ, security header còn nguyên, bản live **đúng** bản vừa tag, không phục vụ HTML cũ, route chính đi được, **rollback đã thử thật** | output `curl` thật + `release_id` + log rollback (`agents/devops/skills/verify_web_deployment/`) |
| `backend_service` | `verify_web_deployment` đạt điều 8-12: health endpoint `200` đúng phiên bản, migration đã chạy và có đường lùi đã thử, secret không lộ trong log, **rollback đã thử thật** | output health + log migration + log rollback |

> **Vì sao điều kiện phải rẽ nhánh:** trước đây gate này chỉ có 1 đường — "lên store" — vì kernel
> mặc định mọi project là mobile app. Áp nguyên bộ đó cho web/API thì `check_app_store_policy`
> kiểm một thứ **không tồn tại** và tạo cảm giác đã kiểm, trong khi thứ **thật sự** cần kiểm (URL
> live, health, rollback) không có điều kiện nào. Với mobile, bản review của store là một lớp gác
> cổng bên ngoài; web/API **không có lớp đó** — nên bằng chứng bằng lệnh thật ở đây là lớp gác cổng
> duy nhất.

**Nhiều target = phải xong đủ từng target.** "1 cái xong coi như xong" là chỗ dễ sai nhất khi project có cả app và web: `qa` đã pass cho cả 2 nhánh, nên bỏ sót 1 nhánh ở release sẽ không có gì khác báo.

### Điều 3 là điều kiện quan trọng nhất về mặt hệ thống

Nó là **mối nối duy nhất giữa Build Mode và Runtime Mode**. Nếu webhook monitoring chưa hoạt động thì:
- `crash_alert` không bao giờ vào `kernel/mailbox/`
- Không track `runtime` nào được tạo
- Hệ thống trông như "chạy tốt" vì không có event lỗi nào — trong khi thực tế là **nó không thể nhận được event lỗi**

Đây đúng là loại lỗi im lặng mà toàn bộ thiết kế đang cố loại bỏ: sự vắng mặt của tín hiệu bị hiểu nhầm là tín hiệu tốt. Vì vậy điều 3 phải verify bằng **event thật đã đến**, không phải bằng "đã cấu hình webhook". Điều này **không** phụ thuộc loại sản phẩm: mobile bắn `crash_alert`, web/API bắn `error_alert`, nhưng mối nối phải thật ở cả hai.

---

## Khi FAIL

Trả về `devops` kèm điều kiện nào không đạt, **ghi rõ target nào** (không phải "release fail"). Riêng các điều cần sửa cấu hình **bên ngoài** repo — store policy, monitoring webhook, DNS/TLS/CDN, biến môi trường production — **không được retry mù**: fail 2 lần liên tiếp thì escalate ngay thay vì đợi hết `after_fail`, vì lần thử thứ 3 sẽ y hệt lần thứ 2.

## Khi PASS

- Node `REL-devops-release` → `done`. Track `build` kết thúc.
- Hệ thống chuyển sang **Runtime Mode**: từ đây node mới chỉ sinh từ event ngoài (`crash_alert`, `bug_report`, `feature_request`) — xem `ORCHESTRATOR.md` §7a.
- Ghi 1 dòng `event-log.jsonl` với `event: release` để lớp Evolution (§9) tính được thời gian từ intake tới release.
