# Gate 0 — Context Integrity

**Chạy khi:** mọi lần Orchestrator chạm vào 1 message — pha A (tiêu thụ) và pha B (dispatch) của Event Loop (`ORCHESTRATOR.md` §7).

---

## Cách chạy phần A

```bash
python kernel/tools/validate.py
```

Điều kiện 1-7 (phần A) cài đặt trong `validate.py` (mã `D*`). Điều kiện 8-10 (phần B) cài đặt trong `context_compile.py`. **Cả 2 phần đều chạy được**, đừng tự kết luận pass.

> **Không có Python?** Script là đường nhanh, không phải điều kiện bắt buộc của Gate. Thiếu Python thì đọc danh sách điều kiện dưới đây và kiểm bằng tay/bằng AI — chậm hơn và tốn context hơn (phải nạp nhiều file), nhưng Gate vẫn thoả được. Nguyên tắc "không tự kết luận pass" vẫn giữ: phải kiểm từng điều, không đọc lướt rồi kết luận.


## A. Kiểm lúc TIÊU THỤ message (pha A)

Toàn bộ đều là **lookup xác định**, không cần đọc hiểu văn bản:

1. **Frontmatter hợp lệ** theo `kernel/contracts/message.schema.json` (đủ field required, đúng enum).
2. **`node_id` tồn tại** trong `kernel/memory/wbs.json` (bất kể track `intake`/`build`/`runtime`) — trỏ vào node không có = message vô địa chỉ, không xử lý được. Điều kiện này luôn thoả được vì node **sinh ra trước khi agent chạy** (PHA 0 của Event Loop, `ORCHESTRATOR.md` §7a) — kể cả message đầu tiên của `po` cũng đã có node `INTAKE<nnn>-po`.
3. **`from` khớp `role` của node đó** — `wbs.json.nodes[node_id].role == msg.from`. Chặn việc 1 agent gửi message mạo danh node của agent khác.
4. **`to` hợp lệ theo `kernel/contracts/dag.json`** (thay cho việc đọc bảng markdown) — chú ý `dag.json` có **2 đồ thị riêng**, tra đúng cái tương ứng chế độ đang chạy:
   - `type: handoff`, Build Mode → `to` phải là `role` của một unit trong `units[<unit của node_id>].feeds`
   - `type: handoff`, Runtime Mode (đường tắt: `feature_request` size S, `bug_report`) → tra `units[...].runtime_feeds`
   - `type: request`/`response` → `to` phải nằm trong `sync_allowed[msg.from]` (map này đối xứng, nên hỏi được thì trả lời được)
   - `type: request`: thêm điều kiện `turn <= max_turns` (vượt thì không dispatch, escalate — xem `scheduling-policy.md`)
5. **`message_id` theo quy ước `msg-<node_id>-<n>` và không trùng** — đánh số tự do thì 2 agent chạy song song sẽ cùng chọn 1 số rồi ghi đè file của nhau (validator `D16`, `D17`).
6. **Body không vượt ngưỡng** khai ở `kernel/config/limits.json` → `message.body_max_lines` / `body_max_chars` (**không lặp lại con số ở đây** — SSOT ở 1 nơi). Body được nạp vào context agent nhận; message dài làm nổ `max_context_tokens` của nó mà phần B **không chặn được**, vì phần B chỉ kiểm bundle Tier 0+1+2. Log dài phải ra file (validator `D14`).
7. **Mọi path trong `artifact_refs` phải tồn tại thật** — đây là bằng chứng mà Gate 3/Gate 4/Gate 6 sẽ đối chiếu; trỏ vào file không có nghĩa là **không có bằng chứng** (validator `D15`).

## B. Kiểm lúc DISPATCH agent (pha B)

```bash
python kernel/tools/context_compile.py <node_id>
```

Tool **tự thực hiện** cả 3 điều dưới đây — exit code `0` = phần B pass. Không còn là "chưa tự động hoá được":

8. **Bundle context không vượt `max_context_tokens`** của `agents/<role>/manifest.json` — tool đếm token thật của cả file boot context và ghi vào `bundle_tokens`. Dùng `--explain` để xem phân bổ theo từng nguồn (biết đúng anchor-tag nào phình to).
9. **Tier 2 trích được không rỗng** với node `scope: story` — rỗng nghĩa là **LỖI TAG**, không phải "story không có nội dung". Tool phân biệt 3 ca: chưa gắn tag / có tag nhưng khác story / có story nhưng `role:` không chứa role này.
10. **`attempt > 1` thì phải có `last_error`** — thiếu là retry mù, agent sẽ làm lại y như lần trước.

---

## Khi FAIL

| Điều kiện fail | Hành động |
|---|---|
| 1, 2, 3 (message hỏng/vô địa chỉ/mạo danh) | Không dispatch. Ghi event-log kèm field sai. **Vẫn set `processed_at`** để message rác không quay lại mỗi vòng. |
| 4 (route sai vai trò) | Không dispatch. Ghi event-log. Đây là dấu hiệu agent hiểu sai luồng → cập nhật `agents/<role>/rules/` (lớp Evolution), không chỉ bỏ qua. |
| 4 (vượt `max_turns`) | Escalate theo `scheduling-policy.md`. Node bên treo → `waiting_human` + `escalated_at`, quay lại bằng `kernel/tools/resume.py`. |
| 5 (`message_id` trùng/sai quy ước) | Không dispatch. Trả về agent gửi: đánh lại theo `msg-<node_id>-<n>`. Trùng = **mất message**, phải sửa trước khi làm gì khác. |
| 6 (body quá dài) | Không dispatch. Trả về agent gửi: chuyển log ra file + dùng `artifact_refs`. |
| 7 (`artifact_refs` treo) | Không dispatch. Coi như **chưa có bằng chứng** — Gate 3/4 phải fail dù agent tự báo pass. |
| 8 (vượt token budget) | **Lỗi thiết kế tagging**, KHÔNG phải lỗi Agent — báo `cto`. Tuyệt đối không tự cắt bớt context rồi dispatch. `--explain` chỉ ra đúng nguồn nào phình to. |
| 9 (Tier 2 rỗng) | Báo về **writer của file đó** theo `kernel/contracts/data-ownership.json` (`ba` cho PRD, `cto` cho architecture/db-schema/system-spec/api-contracts) để sửa anchor-tag. |
| 10 (retry thiếu `last_error`) | Lỗi của **Orchestrator**, không phải agent — Gate fail mà không ghi `gate.last_error` vào `wbs.json`. Sửa bookkeeping rồi compile lại. |

**Nguyên tắc chung khi Gate 0 fail:** không bao giờ để 1 message fail nằm lại `processed_at: null` — nếu không nó sẽ được thử lại vô hạn mỗi vòng lặp.
