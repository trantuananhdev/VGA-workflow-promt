# kernel/tools/ — công cụ xác định của control plane

> Chỉ dùng **Python stdlib**, không dependency, không phụ thuộc AI tool nào cụ thể —
> chạy được bởi Claude, Cursor, hay người. Đây là ràng buộc thiết kế: OS prompt này phải
> portable giữa các tool, nên phần xác định không được viết bằng tính năng riêng của 1 tool.

## `validate.py`

Biến Gate 0 (phần A) và Gate 2 từ *"điều kiện ghi trong tài liệu"* thành *kiểm tra thực thi được*.

```bash
python kernel/tools/validate.py              # kiểm trạng thái repo hiện tại
python kernel/tools/validate.py --selftest   # + mô phỏng 3 track từ dag.json (kiểm LUẬT, không cần dữ liệu thật)
python kernel/tools/validate.py --json       # output JSON cho tool tự động đọc
```

Exit code: `0` = không có ERROR · `1` = có ERROR (không được chạy Event Loop).

### Nhóm kiểm tra

| Mã | Phạm vi | Bắt gì |
|---|---|---|
| `A*` | `agents/*/manifest.json` | Sai schema, `agent_id` khác tên thư mục, `escalation.notify` trỏ key không tồn tại, và **field trùng lặp bò trở lại** (`depends_on`/`triggers` — chúng thuộc `dag.json`) |
| `B*` | `kernel/contracts/dag.json` | Lệch chiều `feeds`↔`depends_on`, chu trình, `sync_allowed` không đối xứng, unit trỏ role/gate không tồn tại, agent không có unit nào (→ không bao giờ được dispatch) |
| `C*` | `kernel/memory/wbs.json` | `node_id` trùng, dependency treo, **sai quy tắc giao tập**, `ready` khi dep chưa done, **`blocked` khi mọi dep đã done** (= quên `RECOMPUTE_READY()`), vượt `concurrency`, `po`/`ba`/`cto` lọt vào track `build`, track toàn `blocked` |
| `D*` | `kernel/mailbox/*.md` | Frontmatter sai schema, `node_id` vô địa chỉ, `from` mạo danh node khác, `to` không hợp lệ theo `dag.json`, `turn > max_turns`, **`processed_at: null` khi node đã `done`** (`D12` — loop vô hạn), body vượt ngưỡng (`D14`), `artifact_refs` trỏ file không có (`D15`), `message_id` trùng hoặc sai quy ước `msg-<node_id>-<n>` (`D16`/`D17`) |
| `F*` | single-writer (`data-ownership.json`) | File có >1 writer, file đơn bị unit `scope:story` `concurrency>1` ghi (`F3`), agent memory không đặt tên theo node (`F6`), file `shared/` chưa khai chủ sở hữu |
| `E*` | tham chiếu chéo | Thư mục skill rỗng, skill không được `AGENT.md` cho phép gọi, anchor-tag trỏ role không tồn tại, capability-agent kích hoạt sai, tham chiếu tới thứ đã bị gỡ, **thiếu tiền đề Gate 1 cho nhánh Design** (`E9`: khối `story:PROJ` role `designer` trong `PRD.md`; `E10`/`E11`: `domain-map.json` phủ đủ story) |
| `G*` | `kernel/boot/*.md` (chiều kernel→agent) | `bundle_tokens` vượt `max_context_tokens` (`G6` = Gate 0 điều 8), retry thiếu `last_error` (`G9`), `allowed_*` lệch `dag.json` (`G12`/`G13` — agent bị chặn oan hoặc được quá quyền), `tier2_sources` rỗng với node có story (`G11` = lỗi tag), body thiếu/đổi số mục (`G15`) |
| `S*` | `--selftest` | Mô phỏng sinh track `intake`/`build`/`build+ads`/`runtime` rồi kiểm: có unit nào `ready` không, `depends_on` có đúng kỳ vọng không |

### 3 kiểm tra quan trọng nhất — chúng bắt lỗi *im lặng*

`C12`, `D12` và `C28` nhắm vào 3 failure mode **không tự báo lỗi** của Event Loop:

- **`D12`** — message `processed_at: null` nhưng node đã `done`: vòng sau sẽ tiêu thụ lại đúng message đó → **loop vô hạn**.
- **`C12`** — node `blocked` nhưng mọi `depends_on` đã `done`: `RECOMPUTE_READY()` bị bỏ sót → **treo im lặng**, không ai báo gì, project đứng.
- **`C28`** — node `running` quá `limits.json → node.stale_running_hours`: agent hang/chết mà không trả message. Nó **giữ 1 slot `concurrency` vĩnh viễn**; không có gì tự báo vì về mặt trạng thái nó vẫn "đang chạy".

Đây là lý do phải chạy validator **sau mỗi vòng lặp**, không chỉ lúc sửa cấu trúc.

### Validator đã được kiểm chứng

Không phải "viết ra rồi tin". Đã test bằng cách **tiêm lỗi cố ý** vào bản copy rồi kiểm validator có bắt không:

| Lớp lỗi tiêm vào | Mã bắt được |
|---|---|
| Phá đối xứng `dag`, lệch `sync_allowed` | `B9`, `B13` |
| Nhét lại `depends_on` vào manifest, `notify` sai key | `A3`, `A8` |
| Node sai quy tắc giao tập, dependency treo, `ready` sớm, `po` lọt track `build` | `C10`, `C8`, `C11`, `C15` |
| `waiting_human` thiếu `escalated_at`, cứu ≥3 lần | `C20`, `C21`, `C22` |
| Gate 1 thiếu chữ ký, 1 bên ký 2 lần, signoff thiếu `message_id` | `C25`, `C24`, `C26` |
| Node `running` quá lâu, `running` thiếu `started_at` | `C28`, `C29` |
| Message mạo danh, `to` sai, sót `processed_at` | `D9`, `D10`, `D12` |
| Body quá dài, `artifact_refs` treo, `message_id` trùng/sai quy ước | `D14`, `D15`, `D16`, `D17` |
| Race: file đơn bị `concurrency>1` ghi, agent memory dùng file chung | `F3`, `F6` |
| Story thật thiếu entry `domain-map.json`, thiếu khối `story:PROJ` cho `designer` | `E10`, `E9` |

Mỗi lần thêm nhóm kiểm tra mới đều test lại theo cách này — validator không bao giờ báo lỗi thì vô dụng.

## `resume.py` — đường quay lại duy nhất sau escalation

```bash
python kernel/tools/resume.py --list                            # node nào đang chờ người
python kernel/tools/resume.py <node_id> --note "<đã sửa gì>"    # waiting_human -> ready|blocked
python kernel/tools/resume.py <node_id> --abandon --note "..."  # waiting_human -> failed
python kernel/tools/resume.py <node_id> --decision <id> --note "..."  # awaiting_human_decision -> ready
```

`--decision` dùng riêng cho status `awaiting_human_decision` (hiện chỉ Gate 7 — chọn theme): ghi thêm `shared/design/theme-choice.json` (owner `__human__`), và **không** tăng `gate.consecutive_fail` vì đây không phải lỗi. Xem `kernel/gates/gate7-design-system-lock.md`.

Node `waiting_human` **không tự thoát ra được**. Tool này làm nguyên tử 4 việc: đổi `status`, reset `gate.consecutive_fail`, append `gate.resume_history`, append `event-log`.

**Không sửa tay `wbs.json` để resume** — rất dễ quên reset bộ đếm, node sẽ escalate lại ngay lần fail tiếp theo, người tưởng đã xử lý xong nhưng hệ thống thì không. `--note` bắt buộc để lớp Evolution biết người đã sửa gì. Tool **tính lại `depends_on`** thay vì mặc định `ready`, vì trong lúc treo dependency có thể đã đổi.

`--abandon` cảnh báo rõ node nào sẽ `blocked` vĩnh viễn — hệ thống **không** cascade fail, phải xử lý từng node.

## `digest.py` — sinh `kernel/memory/today.md`

```bash
python kernel/tools/digest.py            # ghi file
python kernel/tools/digest.py --stdout   # xem trước
```

`today.md` là **Tier 0** — nạp vào boot context của **mọi** agent. Nếu điền tay và bị mục thì không chỉ scheduler sai mà mọi agent nhận context sai. Và mọi field của nó derived 100% từ `wbs.json` + `mailbox/`, nên nó phải là **artifact sinh ra**, không phải file điền tay (đúng lý do đã khiến `process-table.json` bị bỏ).

Digest tự nêu 2 tín hiệu nguy hiểm ngay trên đầu file: node **`waiting_human` đang chặn ai**, và node **đủ điều kiện nhưng vẫn `blocked`** (= quên `RECOMPUTE_READY()`, hệ đang treo im lặng).

Chạy cuối mỗi vòng Event Loop, sau khi đã cập nhật `wbs.json`.

## Format `kernel/memory/event-log.jsonl`

File này phải **rỗng** trong repo template — ví dụ để ở đây, không để trong file log (tránh lớp Evolution đếm ví dụ thành event thật).

Mỗi dòng 1 span. Bắt buộc: `ts`, `event`, `node_id`. `event` ∈ `dispatch` | `gate_check` | `handoff` | `sync_session` | `escalation` | `resume` | `abandon` | `gate0_reject`.

```jsonl
{"ts":"2026-07-28T10:02:00Z","event":"dispatch","node_id":"US014-designer-screen","task_id":"US-014","role":"designer","phase":"designer-screen"}
{"ts":"2026-07-28T10:14:30Z","event":"handoff","node_id":"US014-designer-screen","task_id":"US-014","from":"designer","to":"mobile","message_id":"msg-US014-designer-screen-1","gate":"gate5","result":"pass","unblocked":["US014-mobile-screen"]}
{"ts":"2026-07-28T11:40:12Z","event":"gate_check","node_id":"US014-mobile-screen","task_id":"US-014","gate":"gate3","result":"fail","consecutive_fail":1,"reason":"flutter analyze: 3 errors in otp_screen.dart"}
{"ts":"2026-07-28T12:05:00Z","event":"sync_session","node_id":"US014-mobile-screen","task_id":"US-014","request_id":"sync-US014-01","participants":["mobile","cto"],"turns":2,"outcome":"resolved"}
{"ts":"2026-07-28T13:20:00Z","event":"escalation","node_id":"US014-mobile-screen","task_id":"US-014","reason":"consecutive_fail=3 >= after_fail","notify":"dev-alerts"}
{"ts":"2026-07-28T15:02:00Z","event":"resume","node_id":"US014-mobile-screen","task_id":"US-014","from_status":"waiting_human","to_status":"ready","note":"sua STACK BINDING lint","by":"human"}
```

`node_id` cho phép trace vòng đời 1 node; `task_id` cho phép trace 1 story qua nhiều node (`grep task_id=US-014`).

## Chạy khi nào — tóm tắt

| Thời điểm | Lệnh |
|---|---|
| Đầu phiên | `validate.py --selftest` rồi `resume.py --list` |
| Sau khi sửa `dag.json` / thêm-xoá agent / đổi gate / đổi `concurrency` | `validate.py --selftest` |
| Cuối mỗi vòng Event Loop | `validate.py` rồi `digest.py` |
| Gate 2, sau khi append track mới | `validate.py` |
| Khi có node `waiting_human` | `resume.py <node_id> --note "..."` |

## `context_compile.py` — sinh boot context (kernel → agent)

```bash
python kernel/tools/context_compile.py <node_id>            # ghi kernel/boot/<node_id>.md
python kernel/tools/context_compile.py <node_id> --explain   # bảng phân bổ token theo nguồn
python kernel/tools/context_compile.py <node_id> --stdout    # xem trước
```

Đây là mắt xích cuối của hạ tầng — nó biến 2 thứ từ "mô tả" thành "thực thi được":
1. Chiều kernel→agent có **contract thật** (`kernel/contracts/boot-context.schema.json`), đối xứng với `message.schema.json` ở chiều ngược lại.
2. **Gate 0 phần B** (điều 8-10) kiểm được: đếm token thật, phát hiện Tier 2 rỗng, chặn retry mù.

**Nguyên tắc: xác định, KHÔNG dùng LLM.** Trích theo anchor-tag/`story_id`, không tóm tắt. Nếu bước này tóm tắt thì mọi bảo đảm về "agent đọc đúng bản gốc" mất hết.

**Không có danh sách "role nào đọc file nào" trong tool** — cố ý. Quyền đọc khai ở đúng 1 nơi: `role:` trong anchor-tag (markdown) và `roles` của từng entry (JSON). Tool chỉ quét và lọc. Nhờ vậy thêm file mới vào `shared/` **không cần sửa tool**.

3 lỗi nó chặn trước khi dispatch:

| Lỗi | Thông báo |
|---|---|
| Bundle vượt `max_context_tokens` | Chỉ ra nguồn nào phình to (`--explain`), và **không tự cắt bớt** — đó là lỗi thiết kế tagging, phải sửa tag |
| Tier 2 trích được rỗng | Phân biệt 3 ca: chưa gắn tag / tag khác story / `role:` không chứa role này. Đây là **lỗi tag**, không phải "story không có nội dung" |
| `attempt > 1` mà `last_error` rỗng | Retry mù — agent sẽ làm lại y như lần trước. Đây là lỗi bookkeeping của Orchestrator |

## Chưa có (xem `README.md` gốc)

- `next.py` / `consume.py` — gộp bookkeeping thành lệnh nguyên tử để *phòng ngừa* thay vì chỉ *phát hiện*. Hoãn tới khi chạy loop thật thấy sai bookkeeping nhiều.
