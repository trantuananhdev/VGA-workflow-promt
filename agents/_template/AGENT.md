# AGENT.md — Template Process Image

> Copy toàn bộ thư mục `agents/_template/` thành `agents/<role>/`, rồi điền lại các mục dưới đây.
> Đây là "boot file" của agent — agent CHỈ nạp file trong thư mục của chính nó (rules/docs/memory/skills/commands), KHÔNG bao giờ đọc `memory/` của agent khác.

## Vai trò

<Mô tả 1 đoạn: agent này chịu trách nhiệm gì>

## Không được làm

<Liệt kê rõ ràng — vd "Dev không được tự đổi luồng nghiệp vụ nếu chưa có BA đồng ý">

## Input hợp lệ (chỉ nhận từ đâu)

**Đúng 1 nguồn: file `kernel/boot/<node_id>.md`** do `kernel/tools/context_compile.py` sinh ra, theo `kernel/contracts/boot-context.schema.json`. Agent KHÔNG tự đi tìm input ở đâu khác.

Cấu trúc cố định (agent bám theo **số mục**, không theo tên):

| Mục | Nội dung |
|---|---|
| frontmatter | `node_id` (dùng làm địa chỉ khi emit message), `phase`, `gate` phải qua, `attempt`, `allowed_handoff_to`/`allowed_sync_with`/`allowed_skills` |
| `## 0.` | Trạng thái hệ thống (Tier 0) |
| `## 1.` | Luật vai trò của bạn (Tier 1) |
| `## 2.` | Việc cần làm — message đã được nhúng sẵn |
| `## 3.` | Dữ liệu nghiệp vụ liên quan (Tier 2) |
| `## 4.` | *(chỉ khi `attempt > 1`)* lần trước fail vì gì |

**Agent KHÔNG cần đọc `dag.json`** — kernel đã cô đặc quyền hạn vào `allowed_*`. Cũng không cần tự mở `shared/*` nếu mục 3 đã đủ; chỉ mở khi thật sự cần chi tiết ngoài phạm vi đã trích.

## Output hợp lệ (chỉ được ghi ra đâu)

- Nháp làm việc: `memory/<node_id>.md` (**một file mỗi node** — xem `memory/README.md`; dùng chung 1 file là race khi `concurrency > 1`)
- Emit message mới vào `kernel/mailbox/` (`type: handoff` hoặc `request`/`response`)
- Ghi artifact vào đúng vị trí SSOT quy định (KHÔNG bao giờ ghi đè `shared/*.md` mà không qua Gate tương ứng)

## Skill được phép gọi

<Liệt kê tên skill trong thư mục `skills/` của agent này — agent KHÔNG được tự bịa hành vi ngoài danh sách này>

## Khi gặp mơ hồ / cần hỏi Agent khác

Mở 1 Sync Session (`type: request`, `max_turns` hợp lý — thường 3), KHÔNG tự đoán. Xem `kernel/rules/scheduling-policy.md`.

## Verification bắt buộc trước khi báo "xong"

<Liệt kê lệnh/skill cụ thể phải chạy và đọc output — không được nói "should work">
