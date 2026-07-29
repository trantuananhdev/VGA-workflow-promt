# Gate 6 — Release Verified

> Số gate đánh theo **thứ tự tạo ra**, không theo DAG. Đây là gate **cuối cùng** của vòng đời — sau Gate 4.

**Chạy khi:** `devops` (phase `devops-release`) emit `type: handoff` báo đã release.

**Vì sao cần:** trước đây `dag.json` để `devops-release.gate: null` — nghĩa là **bước đưa app lên chợ hoàn toàn không được kiểm**. Gate 4 chỉ xác nhận *code đúng*, không xác nhận *release thành công*. Hệ quả thực tế: pipeline chạy, node chuyển `done`, hệ thống coi như xong — nhưng app có thể chưa lên store, hoặc lên mà monitoring chưa gắn (khi đó `crash_alert` không bao giờ về, **toàn bộ Runtime Mode chết âm thầm**).

---

## Điều kiện PASS

1. **Artifact tồn tại thật:** package (APK/IPA hoặc tương đương) đã build, đường dẫn khai trong `artifact_refs` và Gate 0 (`D15`) đã kiểm file có thật.
2. **Tag semver đã tạo:** `git tag` khớp `v<major>.<minor>.<patch>`, KHÔNG dùng `latest` (xem `skills/git_workflow/SKILL.md`).
3. **`check_app_store_policy` trả `violations: []`** (xem `agents/devops/skills/check_app_store_policy/SKILL.md`).
4. **Monitoring đã nhận được event thật** — `setup_monitoring` phải đã trigger 1 crash giả lập và thấy message `crash_alert` xuất hiện trong `kernel/mailbox/`.
5. **Đã merge vào `main`** — merge chính là hành động trigger pipeline, không có bước deploy tay song song.

### Điều 4 là điều kiện quan trọng nhất về mặt hệ thống

Nó là **mối nối duy nhất giữa Build Mode và Runtime Mode**. Nếu webhook monitoring chưa hoạt động thì:
- `crash_alert` không bao giờ vào `kernel/mailbox/`
- Không track `runtime` nào được tạo
- Hệ thống trông như "chạy tốt" vì không có event lỗi nào — trong khi thực tế là **nó không thể nhận được event lỗi**

Đây đúng là loại lỗi im lặng mà toàn bộ thiết kế đang cố loại bỏ: sự vắng mặt của tín hiệu bị hiểu nhầm là tín hiệu tốt. Vì vậy điều 4 phải verify bằng **event thật đã đến**, không phải bằng "đã cấu hình webhook".

---

## Khi FAIL

Trả về `devops` kèm điều kiện nào không đạt. Riêng điều 3 (store policy) và điều 4 (monitoring) **không được retry mù** — chúng cần sửa cấu hình bên ngoài (metadata store, webhook), nên nếu fail 2 lần liên tiếp thì escalate ngay thay vì đợi hết `after_fail`.

## Khi PASS

- Node `REL-devops-release` → `done`. Track `build` kết thúc.
- Hệ thống chuyển sang **Runtime Mode**: từ đây node mới chỉ sinh từ event ngoài (`crash_alert`, `bug_report`, `feature_request`) — xem `ORCHESTRATOR.md` §7a.
- Ghi 1 dòng `event-log.jsonl` với `event: release` để lớp Evolution (§9) tính được thời gian từ intake tới release.
