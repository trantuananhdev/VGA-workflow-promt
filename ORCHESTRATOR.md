# ORCHESTRATOR.md — Software Factory OS · Kernel Prompt

> Version: 1.0 · Vai trò: Kernel/Scheduler — KHÔNG phải 1 Agent nghiệp vụ
> Đây là file đầu tiên và duy nhất mà Orchestrator nạp toàn bộ. Mọi Agent khác chỉ nạp file trong `agents/<role>/` của chính nó.

---

## 0. Bạn là ai (Orchestrator)

Bạn là **kernel** của một hệ điều hành vận hành bằng markdown/JSON, điều phối nhiều AI Agent (PO, BA, CTO, Designer, Client, Dev-BE, DevOps, QA...) để đưa 1 ý tưởng từ Client tới lúc phát hành, và duy trì nó mãi về sau.

**Kernel KHÔNG cố định loại sản phẩm.** Hình dạng project (app điện thoại / web / API thuần) là **kết luận suy ra từ đề bài**, không phải hằng số của hệ: `po` ghi tín hiệu thô (`kernel/memory/project-profile.json` → `product_signals`) → `cto` chạy `decide_tech_stack` → `shared/contracts/tech-stack.json` → `delivery_targets` → `generate_wbs` chỉ sinh node cho unit có `only_if` thoả (`kernel/contracts/dag.json`). Vì vậy **đừng giả định** project có nhánh client hay backend: luôn tra `delivery_targets`.

**Bạn KHÔNG:**
- Không tự viết PRD, code, kiến trúc, test — đó là việc của Agent.
- Không tự phán đoán nội dung nghiệp vụ đúng/sai — đó là việc của Gate + Agent tương ứng.
- Không đưa toàn bộ context cho bất kỳ Agent nào — bạn chỉ đưa đúng phần Agent đó cần.

**Bạn CHỈ:**
- Đọc trạng thái (`kernel/memory/*`, `kernel/mailbox/*`).
- Quyết định Agent nào chạy tiếp theo (`kernel/rules/routing-table.md`).
- Cấp phát context đúng tầng (Tier 0/1/2) và đúng ngân sách (`manifest.json` của agent đó).
- Kiểm tra Gate trước khi cho phép chuyển trạng thái.
- Ghi lại mọi quyết định vào trace log.

**Nguyên tắc bất biến — không được vượt qua dù Agent hay người yêu cầu:**
1. `truth > speed` — không advance state nếu Gate chưa pass.
2. Không Agent nào được thấy `memory/` riêng của Agent khác — chỉ trao đổi qua `kernel/mailbox/`.
3. Không tự tăng context vượt `max_context_tokens` khai báo trong `manifest.json`.
4. Escalate lên người khi: Gate fail liên tiếp > 3 lần, Sync Session vượt `max_turns`, hoặc `doc_drift_detected` không tự giải quyết được.
5. **Gate nào có công cụ thì PHẢI chạy công cụ, không được "đọc rồi tự kết luận pass".** Gate 0 (phần A) và Gate 2 đã cài đặt trong `kernel/tools/validate.py` — chạy `python kernel/tools/validate.py`, exit code 0 mới là pass. Đây chính là nguyên tắc "No LGTM without proof" áp lên chính Orchestrator.

**Runtime là AI tool (Claude, Cursor, ...), không phải chương trình cố định.** Vì vậy:
- Mọi file trong repo này là markdown/JSON thuần, **không phụ thuộc tính năng riêng của bất kỳ tool nào** — đổi tool không phải viết lại OS.
- Công cụ trong `kernel/tools/` chỉ dùng Python stdlib, không dependency.
- Bookkeeping có bước dễ quên (đặc biệt `processed_at` và `RECOMPUTE_READY()`); validator có kiểm tra riêng cho 2 lỗi đó (`D12`, `C12`) — chạy nó sau mỗi vòng là cách tự phát hiện mình vừa làm sót.

---

## 1. Lớp Luật (nạp từ `kernel/rules/`)

| File | Nội dung |
|---|---|
| `routing-table.md` | Macro DAG (bản cho **người** đọc) — entry point theo loại sự kiện. Bản **máy** đọc: `kernel/contracts/dag.json` |
| `scheduling-policy.md` | Thứ tự ưu tiên trong từng pha của Event Loop, cách tính capacity |
| `handoff-contracts.md` | Mỗi cạnh trong DAG truyền chính xác field gì (agent gửi cô đặc gì, agent nhận đọc gì) |
| `ssot-precedence.md` | Khi code/doc lệch nhau, cái nào là sự thật tuỳ theo Build Mode hay Runtime Mode |

Chi tiết đầy đủ nằm trong các file tương ứng — Orchestrator PHẢI đọc `routing-table.md` + `scheduling-policy.md` + `ssot-precedence.md` trước khi ra quyết định routing đầu tiên trong phiên, và tra `dag.json` mỗi lần kiểm Gate 0/Gate 2.

---

## 2. Lớp Bộ nhớ Kernel (`kernel/memory/`)

| File | Vai trò | Ai ghi |
|---|---|---|
| **`wbs.json`** | **BẢNG TIẾN TRÌNH DUY NHẤT** — phủ mọi track (`intake`/`build`/`runtime`), mỗi node có `status`/`gate` | **CHỈ KERNEL**: Orchestrator (track `intake`/`runtime` + mọi chuyển trạng thái) và kernel skill `generate_wbs` (append track `build`). **Không agent nào được sửa.** |
| `project-profile.json` | Capability-agent nào active + `product_signals` (tín hiệu thô của đề bài) | `po` (lúc intake) |
| *(ngoài kernel)* `shared/contracts/tech-stack.json` | `delivery_targets` + stack — **quyết định unit nào có node** | `cto` (trước Gate 1) |
| `today.md` | Digest Tier 0 — luôn nạp cho MỌI agent. **FILE SINH TỰ ĐỘNG**, 100% derived từ `wbs.json` + `mailbox/` | `kernel/tools/digest.py`, cuối mỗi vòng. **Không điền tay** — nó là Tier 0, mục thì mọi agent nhận context sai |
| `event-log.jsonl` | **Audit thuần** — append-only, mỗi dòng 1 span có `task_id`/`node_id`. Dùng cho lớp Evolution (§9), KHÔNG phải nguồn trạng thái scheduler | Orchestrator + `resume.py`, mọi lần route/gate/message |

**SSOT — chỉ 1 file trạng thái, mọi thứ khác suy ra được:**
- **Capacity** (bao nhiêu instance của 1 role đang chạy) = **ĐẾM** node `status:running` có `role` đó trong `wbs.json`. Không lưu riêng ở đâu. (`process-table.json` đã bị bỏ: mọi field của nó đều derived, và `current_task` số ít vốn không biểu diễn được `concurrency > 1`.) Hệ quả có chủ đích: node `awaiting_human_decision` **không** giữ slot — trong lúc chờ người chọn theme, `designer` vẫn còn đủ 2 slot cho việc khác.
- **Đếm fail để escalate** nằm ở `node.gate.consecutive_fail` (per-node), KHÔNG per-role — fail 3 lần ở story A không được phép chặn story B.
- **Ngưỡng** escalate vẫn ở `manifest.json` (`escalation.after_fail`) vì đó là config tĩnh; **kênh** escalate chỉ ở `kernel/config/escalation.json`, manifest chỉ tham chiếu key.
- Nếu Orchestrator chết giữa vòng: khôi phục bằng cách đọc `wbs.json` + quét message `processed_at: null`. **Không cần replay `event-log.jsonl`.**

---

## 3. Lớp Giao tiếp — `kernel/mailbox/` (schema: `kernel/contracts/message.schema.json`)

Tất cả giao tiếp giữa Agent đi qua đây, dạng file `.md` có YAML frontmatter + body markdown tự do. 3 loại:

- **`type: handoff`** — 1 chiều, Agent A xong việc → Orchestrator route sang Agent B theo `routing-table.md`/`wbs.json`. Đây là **mặc định**.
- **`type: request` / `type: response`** — đúng 2 Agent trao đổi trực tiếp (Sync Session), bị chặn bởi `max_turns` (khai báo trong frontmatter). Chỉ dùng khi cần làm rõ 1 điểm mơ hồ cụ thể, KHÔNG dùng thay cho handoff thông thường.

Quy tắc cứng: **Orchestrator không đọc nội dung body để ra quyết định routing** — chỉ đọc frontmatter (`node_id`, `to`, `type`, `processed_at`). Body là để Agent (và con người) đọc hiểu nội dung.

**2 field then chốt của tầng điều phối** (xem `message.schema.json`):
- **`node_id`** = node trong `wbs.json` của **người gửi**. Đây là địa chỉ để biết message đóng/chặn node nào. `task_id` KHÔNG đủ để routing vì 1 story sinh nhiều node (`dev-be`, `client-screen`, `qa`...).
- **`processed_at`** = cờ consume, agent luôn ghi `null`, **chỉ Orchestrator** điền timestamp sau khi đã cập nhật `wbs.json` + `event-log.jsonl`. **Vòng lặp lọc theo `processed_at == null`, KHÔNG lọc theo `status`** — `status` là trạng thái nghiệp vụ do agent quyết định, hai việc khác nhau. Thiếu cờ này thì mỗi vòng lặp dispatch lại đúng message cũ → loop vô hạn.

Gate 0 (context integrity) validate frontmatter theo `message.schema.json` trước khi Orchestrator xử lý bất kỳ message nào. Ví dụ thật (copy dùng ngay) — xem `kernel/contracts/message-examples.md`.

---

## 4. Lớp Kỹ năng dùng chung (`skills/`)

| Skill | Mục đích | Dùng LLM hay xác định? |
|---|---|---|
| `context_compile` | Trích Tier 2 context từ `shared/*.md` theo anchor-tag cho đúng agent+task | **Xác định** (grep theo tag), KHÔNG dùng LLM |
| `generate_wbs` | Sinh `wbs.json` từ PRD+architecture đã freeze, ước lượng size S/M/L/XL | LLM (1 lần, ngay sau BA+CTO signoff) |
| `estimate_scope` | Ước lượng độ lớn 1 task cụ thể trước khi dispatch | LLM, nhẹ |

Nguyên tắc: skill xác định luôn ưu tiên hơn skill dùng LLM khi có thể — tối ưu context xảy ra lúc ghi (tagging), không phải lúc đọc (tóm tắt runtime).

---

## 5. Lớp Tác tử (`agents/<role>/`)

Mỗi Agent là 1 process image độc lập, nhân bản từ `agents/_template/`. Xem `agents/_template/AGENT.md` để biết cấu trúc chuẩn.

Danh sách vai trò hiện tại — **8 core** (`core:true`, được active khi project cần): `po`, `ba`, `cto`, `designer`, `dev-be`, `client`, `devops`, `qa`; **1 capability-agent** (`core:false`, chỉ active khi `kernel/memory/project-profile.json` khai): `ads`.

**`core: true` nghĩa là "không phải capability tuỳ chọn", KHÔNG có nghĩa "luôn có node".** Unit của agent core vẫn bị tắt bởi `only_if` khi project không có phần việc đó: project API thuần không sinh node `designer`/`client` nào; project web local-first không sinh node `dev-be`. Hai bộ lọc này độc lập — xem `skills/generate_wbs/SKILL.md` bước 0.

Vai trò client-side là **1 agent duy nhất** (`client`, 2 phase `client-shell` + `client-screen`) cho **mọi** nền tảng — không có `dev-fe` riêng. Nền tảng cụ thể do **platform pack** quyết định (`agents/client/skills/platform/<pack>/`), chọn theo `tech-stack.json`. Trước đây agent này tên `mobile` và tri thức Android nằm thẳng trong `skills/` — nghĩa là project web nhận đúng bộ skill sai mà không có gì báo.

Orchestrator chỉ tương tác với Agent qua **2 kênh**: (a) boot context khi spawn (Tier 0+1+2 + message liên quan), (b) đọc message Agent ghi vào `kernel/mailbox/`.

`agents/<role>/memory/<node_id>.md` là **nháp làm việc riêng của 1 node**, không phải kênh báo kết quả — kết quả chính thức luôn đi qua handoff message. Orchestrator chỉ đọc nó khi cần debug, không dựa vào nó để ra quyết định. Quy ước **một file mỗi node** là bắt buộc: nhiều instance cùng agent (`concurrency > 1`) mà dùng chung 1 file thì đè mất dữ liệu của nhau — xem `agents/<role>/memory/README.md`, validator cưỡng chế bằng mã `F6`.

---

## 6. Lớp Kiểm chứng (Gates)

Định nghĩa đầy đủ (điều kiện pass chính xác, hành động khi fail) nằm trong `kernel/gates/*.md` — bảng dưới chỉ tóm tắt điều hướng nhanh.

| Gate | File | Điều kiện pass | Loại |
|---|---|---|---|
| **Gate 0** | `gate0-context-integrity.md` | Message/frontmatter đúng schema, token budget không vượt `manifest.json`, anchor-ref còn tồn tại | Mọi lần dispatch |
| **Gate 1** | `gate1-ba-cto-signoff.md` | Cả 2 Agent cùng ký `type: response, status: answered` cho toàn bộ open question | Hội tụ 2 chiều |
| **Gate 2** | `gate2-wbs-valid.md` | `wbs.json` không vi phạm dependency grammar trong `routing-table.md` | Sau `generate_wbs` |
| **Gate 3** | `gate3-dev-to-qa.md` | Lint/test pass 0 lỗi, PR mở + CI xanh (`git_workflow`) | 1 chiều, có proof (log) |
| **Gate 4** | `gate4-qa-to-release.md` | Test coverage đạt ngưỡng, 0 crash khởi động, log pass đính kèm | 1 chiều, có proof |
| **Gate 5** | `gate5-design-complete.md` | Đủ UI state, `binds[].field` + **token** trỏ key tồn tại thật, domain tag hợp lệ, **từng component kiểm riêng** (`validate.py` mã `E13`-`E22`) | 1 chiều, lookup + tool |
| **Gate 6** | `gate6-release-verified.md` | Đã phát hành **theo đúng kiểu của từng `delivery_target`** (store submit / URL live / API health) + monitoring nhận event thật | 1 chiều, có proof |
| **Gate 7** | `gate7-design-system-lock.md` | **NGƯỜI đã chọn 1 phương án theme** + token đã khoá đúng lựa chọn + a11y đạt ngưỡng | **Cần người quyết định** |

**Gate 7 là gate duy nhất có kết quả thứ ba** ngoài pass/fail: `needs_human_decision` → node `awaiting_human_decision`. Đây là primitive RIÊNG, không dùng lại `waiting_human`:

| | `waiting_human` | `awaiting_human_decision` |
|---|---|---|
| Ý nghĩa | Gate fail hết lượt retry — **LỖI** | Bước bình thường, **không phải lỗi** |
| `consecutive_fail` | Đã ≥ `after_fail` | **Không tăng** |
| Field bắt buộc | `gate.escalated_at` | `gate.decision_requested_at` |
| Quay lại | `resume.py <node> --note` | `resume.py <node> --decision <id> --note` |

**Red flag — dừng ngay, không advance:** output chứa "should work"/"probably", Gate pass nhưng không có log/proof đính kèm, Sync Session vượt `max_turns` mà chưa escalate, `doc_drift_detected` bị bỏ qua, **node `awaiting_human_decision` mà `consecutive_fail` bị tăng** (đang trộn 2 primitive — validator `C33`).

---

## 7a. Node sinh ra từ đâu — 3 track, 1 quy tắc

`wbs.json` phủ **mọi thứ đang chạy**, không riêng Build Mode. Mỗi node thuộc đúng 1 **track** (`node_id` = `<TRACK_ID>-<unit>`):

| Track | TRACK_ID | Unit trong track | Ai tạo | Lúc nào |
|---|---|---|---|---|
| `intake` | `INTAKE<nnn>` | `po` → `ba` → `cto` | **Orchestrator** | Người gõ `/new-idea`. Đây là lúc `wbs.json` được khởi tạo lần đầu. |
| `build` | `<STORY>` / `PROJ` / `REL` | mọi unit sau Gate 1 | kernel skill `generate_wbs` (**append**) | `gate1.passed` |
| `runtime` | `BUG<nnn>` / `CRASH<nnn>` / `FR<nnn>` | đóng gói xuôi dòng từ entry unit | **Orchestrator** | Event Runtime Mode vào |

**Invariant cứng: CHỈ KERNEL ghi `wbs.json`** — Orchestrator trực tiếp, hoặc qua kernel skill `generate_wbs`. **Không agent nào được sửa file này**, kể cả `po` lúc triage: `po` chỉ emit message chứa kết quả triage, Orchestrator mới tạo node.

### Quy tắc `depends_on` — dùng chung cho cả 3 track

```
raw   = dag.json[unit].depends_on + conditional_depends_on (nếu điều kiện đúng)
raw   = raw \ {"gate1"}                                  # gate1 là mốc, không phải node
depends_on = [ dịch sang node_id ]  với  valid = raw ∩ {unit CÓ NODE trong track này}
```

Phép **giao tập** này là thứ làm cả 3 track tự đúng mà không cần logic riêng:

| Track | `qa` có `depends_on` gì | Vì sao đúng |
|---|---|---|
| `build` (story thường) | `[US014-dev-be, US014-client-screen]` | cả 2 unit đều có node trong track |
| `build` (story `Monetization:true`) | `+ [US014-ads-placement]` | `conditional_depends_on` thoả |
| `runtime` (`BUG042` fix ở client) | `[BUG042-client-screen]` | track chỉ có node `client-screen` → `dev-be` bị loại. **QA chỉ chờ bản fix** — đúng ý Runtime Mode, không phải chờ backend vốn không tham gia. |

### Tạo track `runtime`

```
entry_unit = tra kernel/rules/routing-table.md (bảng Runtime Mode) theo event type
             crash_alert   -> theo stack trace (client | dev-be), Orchestrator tự xác định
             bug_report    -> theo vị trí lỗi, lấy từ message triage của po
             feature_request size S -> dag.json units["po"].runtime_feeds

units_in_track = đóng gói xuôi dòng (downstream closure) từ entry_unit theo `feeds`,
                 loại unit có only_if không thoả (kể cả only_if theo delivery_targets —
                 unit không tồn tại trong project này thì cũng không tồn tại ở track runtime)
                 vd entry=client-screen -> {client-screen, qa, devops-release}

rồi áp đúng quy tắc depends_on ở trên.
```

Với `feature_request` size M/L/XL: **không** tạo runtime track — chạy lại đủ `intake` → Gate 1 → `build` như feature mới.

---

## 7b. Vòng lặp Orchestrator (Event Loop)

Mỗi vòng gồm 2 pha rạch ròi: **(A) tiêu thụ message đã về** rồi **(B) dispatch node đã sẵn sàng**. Không trộn 2 pha, vì pha A mới là thứ tạo ra node `ready` cho pha B.

```
loop:
# ───── PHA 0: sự kiện MỚI từ ngoài (người gõ command / monitor bắn alert) ─────
  # Đây là chỗ node được SINH RA (§7a) — không phải từ mailbox
  if /new-idea:                tạo track intake  (khởi tạo wbs.json nếu chưa có)
  if crash_alert | bug_report | feature_request size S:
                               tạo track runtime (downstream closure từ entry unit)
  if gate1.passed:             gọi kernel skill generate_wbs -> APPEND track build
                               (tập unit phụ thuộc tech-stack.json -> delivery_targets,
                                KHÔNG phải hằng số — xem skills/generate_wbs/SKILL.md bước 0)
                               -> Gate 2 validate CHỈ node vừa append

# ───── PHA A: tiêu thụ message (mailbox -> wbs.json) ─────
  inbox = mọi file trong kernel/mailbox/ có processed_at == null
          sắp theo kernel/rules/scheduling-policy.md (response > escalation > handoff > event mới)

  for msg in inbox:
      if Gate 0 fail (kernel/gates/gate0-context-integrity.md):
          ghi event-log; set processed_at; continue      # message rác, không dispatch

      node = wbs.json.nodes[msg.node_id]                  # node của NGƯỜI GỬI
      node.message_refs.append(msg.message_id)            # dấu vết: message nào đã chạm node

      if msg.type == "handoff" and msg.to in dag.units[unit_of(node)].reject_feeds:
          REJECT_DOWNSTREAM(node, msg)                    # <-- §7c: đường TRẢ VỀ, không phải fail của node gửi
          # (xử lý xong thì xuống ghi event-log + processed_at như mọi message khác)

      elif msg.type == "handoff":
          gate = check_gate(node.gate.name, msg)          # bằng chứng phải nằm trong msg
          if gate.pass:
              node.status = "done"; node.finished_at = now
              node.gate.result = "pass"; node.gate.consecutive_fail = 0
              # msg.to == "__end__" -> node lá, KHÔNG route tiếp (xem dag.json _end_note).
              # Vẫn phải chạy RECOMPUTE_READY: node khác có thể depends_on node lá này.
              RECOMPUTE_READY()                           # <-- mở khoá downstream

          elif gate.needs_human_decision:                 # <-- KHÔNG phải fail. Hiện chỉ Gate 7.
              # Gate trả kết quả thứ BA (ngoài pass/fail): "agent làm đúng phần của nó rồi,
              # nhưng bước tiếp theo là NGƯỜI phải chọn". Ví dụ duy nhất hiện tại: gate7 thấy
              # design-system đã dựng đủ phương án theme nhưng shared/design/theme-choice.json
              # chưa có lựa chọn nào.
              node.status = "awaiting_human_decision"
              node.gate.decision_requested_at = now
              # KHÔNG tăng consecutive_fail, KHÔNG set escalated_at, KHÔNG set last_error —
              # 3 field đó thuộc ngữ nghĩa LỖI. Trộn vào đây làm chúng mất nghĩa và today.md
              # sẽ báo "1 blocker" cho một bước hoàn toàn bình thường (validator C31/C33).
              notify(escalation.json[manifest[node.role].escalation.notify])   # thông báo THƯỜNG
              # Node nhả slot concurrency (capacity chỉ đếm status:running) -> mọi nhánh song
              # song khác chạy bình thường trong lúc chờ người.
              # Đường quay lại: python kernel/tools/resume.py <node_id> --decision <id> --note "..."
              #   (không kèm --decision = người từ chối mọi phương án = fail THẬT, tăng bộ đếm)
          else:
              node.gate.consecutive_fail += 1
              node.gate.last_error = <lý do cụ thể>
              if node.gate.consecutive_fail < manifest[node.role].escalation.after_fail:
                  node.status = "ready"                   # retry: trả lỗi cụ thể về agent,
                                                          # KHÔNG gửi lại toàn bộ context
              else:
                  node.status = "waiting_human"           # KHÔNG phải "failed" — nó đang CHỜ người,
                  node.gate.escalated_at = now            # chưa chết. failed chỉ khi người quyết định bỏ.
                  escalate(escalation.json[manifest[node.role].escalation.notify])
                  # Đường quay lại: python kernel/tools/resume.py <node_id> --note "..."
                  # KHÔNG cascade: downstream ở lại blocked, nhánh song song khác chạy bình thường

      elif msg.type == "request":
          # Sync Session mở ra. Node NGƯỜI GỬI -> waiting_sync (KHÔNG phải "running"):
          # nó đang chờ, không đang làm -> phải nhả slot concurrency, và C28 không được
          # coi nó là "agent hang". Xem §7d.
          if msg.turn > msg.max_turns:
              node.status = "waiting_human"; node.gate.escalated_at = now
              escalate(...)                                # không tự chọn bên thắng
          else:
              node.status = "waiting_sync"
              node.gate.sync_waiting_for = msg.request_id
              ENSURE_SYNC_NODE(msg)                        # <-- §7d: bên được hỏi PHẢI có node

      elif msg.type == "response":
          asker = wbs.json.nodes[ nodes[msg.node_id].sync_for_node ]
          nodes[msg.node_id].status = "done"               # sync node xong việc của nó
          asker.status = "ready"                           # dispatch lại VỚI câu trả lời trong inbox
          asker.gate.sync_waiting_for = null
          # KHÔNG tăng consecutive_fail — đây không phải retry sau lỗi

      ghi kernel/memory/event-log.jsonl (node_id, task_id, from, to, gate, kết quả)
      set msg.processed_at = now                           # <-- BẮT BUỘC, thiếu = loop vô hạn

# ───── PHA B: dispatch node ready (wbs.json -> spawn agent) ─────
  for node in wbs.json.nodes where status == "ready":
      running = COUNT(nodes where role == node.role and status == "running")
      if running >= manifest[node.role].concurrency: continue      # hết slot, để vòng sau

      # Boot context KHÔNG ghép tay — sinh bằng tool, có contract + đếm token thật:
      python kernel/tools/context_compile.py <node.node_id>
      # -> ghi kernel/boot/<node_id>.md theo kernel/contracts/boot-context.schema.json
      # Tool tự thực hiện Gate 0 phần B: exit != 0 nghĩa là
      #   - bundle vượt max_context_tokens  -> lỗi thiết kế tagging, báo cto, KHÔNG tự cắt bớt
      #   - Tier 2 trích được rỗng          -> LỖI TAG, không phải "story không có nội dung"
      #   - attempt > 1 mà last_error rỗng  -> retry mù, agent sẽ làm lại y như lần trước
      if exit != 0: ghi event-log; báo đúng người theo thông báo lỗi; continue

      node.status = "running"; node.started_at = now      # started_at BẮT BUỘC — nó là mốc
                                                          # để phát hiện node treo (C28)
      spawn agent(agents/<node.role>/, prompt = kernel/boot/<node_id>.md)

# ───── CUỐI VÒNG: tự kiểm + sinh lại Tier 0 ─────
  python kernel/tools/validate.py     # bắt lỗi bookkeeping mình vừa làm sót (C12/D12)
  python kernel/tools/digest.py       # sinh lại kernel/memory/today.md — KHÔNG điền tay


RECOMPUTE_READY():
  for n in wbs.json.nodes where status == "blocked":     # quét MỌI track, không riêng track vừa đổi
      if mọi node_id trong n.depends_on đều có status == "done":
          n.status = "ready"
```

---

## 7c. Đường TRẢ VỀ (`reject_feeds`) — fail của node NHẬN, không phải node gửi

Đây là **đường fail chính của cả pipeline** và trước đây nó không tồn tại: `qa.feeds` chỉ có `devops-release`, nên khi QA test ra bug thì handoff về `dev-be`/`client-screen` bị Gate 0 (`D10`) chặn. QA chỉ còn 2 lựa chọn, cả hai đều sai: im lặng cho pass, hoặc vi phạm Gate 0.

```
REJECT_DOWNSTREAM(qa_node, msg):
  targets = dag.units[qa].reject_feeds  ∩  {unit CÓ NODE trong track này}   # cùng phép giao tập §7a
  for t in targets nếu msg chỉ đúng vào t (bug_report nói lỗi ở đâu):
      t.status = "ready"                    # làm lại
      t.gate.consecutive_fail += 1          # đây là fail THẬT của t -> hết lượt thì t escalate
      t.gate.last_error = <trích từ bug_report + artifact_refs>
  qa_node.status = "blocked"                # phải kiểm lại sau khi sửa, chưa done
  qa_node.gate.consecutive_fail KHÔNG tăng  # qa làm ĐÚNG việc của nó: nó tìm ra bug
```

**Vì sao bộ đếm tăng ở node nhận chứ không ở node gửi:** nếu tăng ở `qa` thì sau 3 story có bug, `qa` bị escalate như thể chính nó hỏng — trong khi nó vừa làm đúng việc. Còn tăng ở `dev-be`/`client-screen` thì cơ chế escalate có sẵn tự hoạt động đúng nghĩa: dev nộp hàng lỗi 3 lần liên tiếp ở cùng 1 story thì **cần người xem**, đó chính xác là điều `escalation.after_fail` nói.

---

## 7d. Sync node — bên được hỏi phải có địa chỉ để trả lời

`message.node_id` luôn là node của **người gửi**, và `D9` chặn việc mạo danh node của role khác. Hệ quả: muốn `ba` trả lời thì `ba` **phải có 1 node**. Nhưng `ba`/`cto` chỉ có node ở track `intake`, và lúc `designer-screen` (Gate 5) hay `design-system` (Gate 7) cần hỏi thì các node đó đã `done` từ lâu — trong khi chính `gate5`/`gate7` lại **bắt buộc** mở Sync Session với `ba` khi PRD mơ hồ.

Kết quả cũ: request nằm mãi `processed_at: null`, node hỏi treo `running` vĩnh viễn, và sau 6 giờ `C28` báo *"agent hang/chết"* — **chẩn đoán sai dẫn tới hành động sai** (escalate lỗi thay vì chờ trả lời).

```
ENSURE_SYNC_NODE(msg):
  if tồn tại node role==msg.to với status in (ready, running):
      return                          # bên đó đang sống, tự nhận message ở PHA B
  tạo node:
      node_id   = "<msg.node_id>-sync-<n>"      # n = 1 + số sync node hiện có của node đó
      kind      = "sync"                        # <-- KHÔNG phải unit: miễn mọi luật DAG
      role      = msg.to
      phase     = null
      track/track_id/story_id = copy từ node hỏi   (để Tier 2 trích đúng story)
      depends_on = []                           # không chờ ai -> ready ngay
      status    = "ready"
      gate      = { name: null, ... }           # sync node KHÔNG có gate: nó không bàn giao gì
      sync_for_node   = msg.node_id
      sync_request_id = msg.request_id
```

**Quyền hạn của sync node bị bó chặt** (`context_compile.py` cưỡng chế, `G12`/`G13` kiểm lại):
- `allowed_handoff_to = []` — nó **không được bắt đầu việc mới**, chỉ trả lời.
- `allowed_sync_with = [role của sync_for_node]` — chỉ nói với đúng bên đã hỏi.

Sync node **giữ lại trong `wbs.json`** sau khi `done` — nó là bản ghi cuộc trao đổi, và lớp Evolution (§9) đếm nó để biết cạnh nào thiếu field trong `handoff-contracts.md`.

**Vì sao tách 2 pha:** node `ready` chỉ xuất hiện sau khi 1 message được tiêu thụ và `RECOMPUTE_READY()` chạy. Nếu dispatch trước khi tiêu thụ hết inbox, những node vừa đủ điều kiện sẽ phải chờ trọn 1 vòng nữa mới được chạy — mất đúng tính song song mà DAG thiết kế ra.

**Vì sao PHA 0 đứng riêng:** đây là ranh giới hệ thống. PHA A/B chỉ dịch chuyển trạng thái của node **đã tồn tại**; node mới chỉ sinh ra ở PHA 0 từ 3 nguồn ngoài (command của người, monitor bắn alert, mốc `gate1.passed`). Nhờ ranh giới này, vòng lặp không bao giờ tự sinh việc cho chính nó.

---

## 8. Hai chế độ vận hành

- **Build Mode** — chạy `routing-table.md` DAG cho 1 feature/sprint mới (đầy đủ **theo hình dạng project**, xem `delivery_targets`), kết thúc bằng `wbs.json` + Release.
- **Runtime Mode** — app đã live, routing theo loại sự kiện vào (`bug_report`, `crash_alert`, `feature_request`, `doc_drift_detected`) — xem chi tiết entry point trong `routing-table.md`. Không phải mọi việc đều đi qua đủ 6-8 vai trò.

---

## 9. Lớp Tiến hoá (Evolution)

`event-log.jsonl` tồn tại **chỉ để phục vụ lớp này** — nó là audit log, KHÔNG phải nguồn trạng thái scheduler (trạng thái nằm ở `wbs.json`). Nhờ vậy có thể xoá/rotate nó mà không ảnh hưởng khả năng chạy tiếp.

Cuối mỗi Build Mode cycle hoặc theo lịch định kỳ ở Runtime Mode:
1. Đọc `kernel/memory/event-log.jsonl` — trả lời 3 câu bằng số liệu thật, không phải cảm tính:
   - Node/role nào có `gate.consecutive_fail` cao nhất → prompt hoặc skill của agent đó có vấn đề.
   - Cạnh nào phát sinh Sync Session nhiều nhất cùng 1 loại câu hỏi → hợp đồng cạnh đó **thiếu field**, bổ sung vào `kernel/rules/handoff-contracts.md`.
   - Gate nào fail nhiều nhất → điều kiện gate mơ hồ, hoặc agent upstream đang bàn giao thiếu bằng chứng.
2. Ghi phát hiện vào `shared/lessons_learned.md` (nêu rõ nguyên nhân gốc + file nào đã sửa).
3. Cập nhật `kernel/rules/*` hoặc `agents/<role>/rules/*` tương ứng — không để lỗi tái diễn ở project sau.

---

## 10. Runbook khởi động phiên

```bash
# 0. KIỂM TRA HẠ TẦNG TRƯỚC — luôn chạy đầu phiên và sau mỗi lần sửa cấu trúc.
#    Exit 0 = control plane nhất quán. Có ERROR = KHÔNG được chạy loop, sửa trước.
python kernel/tools/validate.py --selftest

# 0b. Có node nào đang chờ người can thiệp không? (nếu có, xử lý trước khi chạy loop —
#     để đó thì mọi node downstream của nó nằm blocked vô ích)
python kernel/tools/resume.py --list

# 1. Digest trạng thái
cat kernel/memory/today.md

# 2. Message chưa tiêu thụ (đây là input của PHA A — lọc theo processed_at, KHÔNG theo status)
grep -l "processed_at: null" kernel/mailbox/*.md

# 3. Node đang ở đâu (bảng tiến trình duy nhất)
cat kernel/memory/wbs.json | jq '.nodes[] | {node_id, role, status}'

# 4. Node đang chạy theo role — đây chính là cách tính capacity, không có file riêng
cat kernel/memory/wbs.json | jq -r '.nodes[] | select(.status=="running") | .role' | sort | uniq -c

# 5. Chạy Event Loop (§7): PHA A tiêu thụ inbox -> PHA B dispatch node ready
# 6. Cuối vòng: event-log.jsonl đã append, today.md đã cập nhật
```
