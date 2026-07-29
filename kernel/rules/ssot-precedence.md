# ssot-precedence.md — Ai là sự thật khi tài liệu và thực tế lệch nhau

## Build Mode (đang thiết kế mới, chưa có code chạy thật)

```
PRD.md  →  architecture.md  →  code
(ý định dẫn dắt thực thi — code phải khớp doc, không phải ngược lại)
```

## Runtime Mode (app đã live, đang debug/maintain)

```
code + log thực tế  >  architecture.md  >  PRD.md
(thực tế đang chạy là sự thật — doc chỉ là tham chiếu lịch sử)
```

## Khi Dev phát hiện code khác với architecture.md lúc debug

1. **KHÔNG** tự ý sửa doc, và **KHÔNG** tự ý coi doc là sai rồi lờ đi.
2. Emit message `type: handoff` với `event: doc_drift_detected` kèm diff cụ thể (đoạn nào lệch, lệch từ khi nào nếu biết).
3. Route về `[ba+cto]` (Sync Session) để quyết định: cập nhật doc cho khớp code, hay code đang sai cần sửa lại.
4. Cho tới khi có quyết định, Dev vẫn được fix bug theo code thực tế (ưu tiên khôi phục service), nhưng PHẢI gắn cờ `pending_doc_update: true` vào task đó.

## Vì sao bắt buộc bước này

Nếu bỏ qua, PRD/architecture sẽ "thối" dần theo thời gian và trở thành nguồn gây hại — Agent sau tin vào doc sai sẽ ra quyết định sai theo. Chi phí phát hiện + báo cáo lệch (vài dòng message) luôn rẻ hơn chi phí 1 Agent khác dựa vào doc sai để thiết kế feature mới.
