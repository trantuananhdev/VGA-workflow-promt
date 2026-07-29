# scheduling-policy.md — Cách Orchestrator chọn việc tiếp theo

> Vòng lặp 2 pha (tiêu thụ message → dispatch node ready) định nghĩa ở `ORCHESTRATOR.md` §7.
> File này quy định **thứ tự ưu tiên** trong từng pha.

---

## PHA A — thứ tự tiêu thụ message (`processed_at == null`)

1. `type: response` — **ưu tiên cao nhất**, vì đang có 1 node ở `status: running` bị block chờ câu trả lời. Để nó chờ là giữ 1 slot concurrency mà không làm gì.
2. Message có `event: doc_drift_detected` hoặc node sắp `failed` (`gate.consecutive_fail` = `after_fail - 1`) — cần người/BA+CTO xử lý sớm.
3. `type: handoff` — mỗi cái tiêu thụ xong có thể mở khoá nhiều node downstream, nên xử lý hết trước khi sang pha B.
4. `type: request` mới — mở Sync Session, chưa chặn ai ngay.
5. Event Runtime Mode mới vào (`bug_report`, `crash_alert`, `feature_request`) — FIFO theo thời gian đến, trừ khi `crash_alert` (đang ảnh hưởng user thật) thì vượt lên trên `feature_request`.

---

## PHA B — thứ tự dispatch node `status: ready`

Khi nhiều node cùng `ready` mà không đủ slot, ưu tiên theo:

1. **Node nằm trên đường găng dài nhất** — node có nhiều node khác `depends_on` nó (đếm số node trỏ tới nó trong `wbs.json`). Chạy trước để mở khoá được nhiều việc nhất. Ví dụ `PROJ-mobile-shell` chặn MỌI `mobile-screen` → luôn ưu tiên hơn 1 node `dev-be` lẻ.
2. **Node `scope: project`** trước node `scope: story` — cùng lý do, node project thường chặn nhiều node story.
3. **Node đang retry** (`gate.consecutive_fail > 0`) trước node chạy lần đầu — để phát hiện sớm nếu nó sẽ `failed`, thay vì để tới cuối mới lộ.
4. Còn lại: FIFO theo thứ tự trong `wbs.json`.

## Capacity — đếm, không tra file riêng

```
running_of(role) = COUNT(wbs.json.nodes where role == <role> and status == "running")
```
Nếu `running_of(node.role) >= manifest[node.role].concurrency` → **bỏ qua node này, để vòng sau**. Không huỷ, không hạ ưu tiên vĩnh viễn — nó vẫn giữ `status: ready`.

Không có file capacity riêng: `process-table.json` đã bị bỏ vì mọi field của nó đều derived từ `wbs.json`, và bản `current_task` số ít của nó không biểu diễn được `concurrency > 1` (vd `mobile` có `concurrency: 3` = 3 node `mobile-screen` của 3 story chạy cùng lúc).

## Khi nhiều node độc lập cùng `ready` và ĐỦ slot

Spawn **tất cả** — đây chính là điểm tận dụng DAG song song. Ví dụ ngay sau Gate 2: `PROJ-design-system`, `PROJ-devops-infra`, `US014-dev-be`, `PROJ-mobile-shell` đều `ready` và thuộc 4 role khác nhau → chạy đồng thời cả 4, không ép tuần tự. (`US014-designer-screen` thì `blocked` — nó chờ `PROJ-design-system` done, xem `routing-table.md`.)

---

## Khi Sync Session vượt `max_turns`

- Dừng ngay, **không tự ý chọn 1 bên "thắng"**.
- Node của bên đang treo giữ nguyên `status: running` (chưa done, cũng chưa failed) — chờ người quyết.
- Ghi 1 dòng `escalation` vào `kernel/memory/event-log.jsonl` kèm `node_id` + `request_id`.
- Thông báo người: resolve kênh thật qua `kernel/config/escalation.json[<key>]`, với `<key>` = `escalation.notify` trong `agents/<role>/manifest.json` của bên treo.

## Khi 1 node hết lượt retry — `waiting_human`, KHÔNG phải `failed`

Đây là điểm phân biệt quan trọng: node hết `escalation.after_fail` **không chết vĩnh viễn**, nó chuyển `waiting_human` = *đang chờ người can thiệp*. `failed` chỉ dành cho trường hợp người đã xem và quyết định bỏ.

```
running --(fail, còn lượt)------> ready            # retry, chỉ trả lỗi cụ thể về agent
running --(consecutive_fail >= after_fail)--> waiting_human + escalate
waiting_human --(người sửa xong)--> ready | blocked  # qua resume.py, tính lại depends_on
waiting_human --(người bỏ)--------> failed
```

**Bắt buộc khi chuyển `waiting_human`:** set `gate.escalated_at`, gửi thông báo theo `kernel/config/escalation.json[<key>]`. Validator mã `C20` chặn nếu `waiting_human` mà thiếu `escalated_at` — vì khi đó không rõ người có thật sự được báo hay không.

### Đường quay lại — chỉ qua 1 lệnh

```bash
python kernel/tools/resume.py --list                            # node nào đang chờ người
python kernel/tools/resume.py <node_id> --note "<đã sửa gì>"    # đưa lại vào vòng lặp
python kernel/tools/resume.py <node_id> --abandon --note "..."  # bỏ hẳn node này
```

**Không sửa tay `wbs.json` để resume.** Sửa tay rất dễ quên reset `gate.consecutive_fail` — node sẽ escalate lại ngay lần fail tiếp theo, người tưởng đã xử lý xong nhưng hệ thống thì không. Tool làm nguyên tử 4 việc: đổi `status`, reset bộ đếm, ghi `gate.resume_history`, append `event-log`. `--note` là bắt buộc.

`resume.py` **tính lại `depends_on`** thay vì mặc định về `ready` — vì trong lúc node treo, dependency của nó có thể đã đổi (vd bị `abandon`), nên nó có thể phải về `blocked`.

## Không cascade

- Node `waiting_human`/`failed` **không** làm downstream `failed` theo — chúng ở lại `blocked` (đúng, vì dependency thật sự chưa xong). Validator `C21` cảnh báo rõ node nào đang bị chặn.
- Toàn bộ nhánh song song khác **vẫn chạy bình thường** — 1 story treo không dừng cả project.
- Node phải cứu ≥3 lần: validator `C22` nhắc đây không còn là lỗi ngẫu nhiên — ghi `shared/lessons_learned.md` và sửa `rules`/`skill` của role đó (lớp Evolution).
