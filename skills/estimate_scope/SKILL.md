# skill_estimate_scope

**Dùng bởi:** `po` (triage `feature_request` ở Runtime Mode), `ba` (size từng Epic/Story trước khi viết chi tiết), `generate_wbs` (gọi nội bộ khi sinh `wbs.json`).

**Mục tiêu:** Cho ra size S/M/L/XL theo tiêu chí cố định — KHÔNG đoán cảm tính, để cùng 1 loại việc luôn ra cùng 1 size dù ai/lúc nào chạy.

## Tiêu chí chấm điểm (cộng dồn)

| Tiêu chí | 0 điểm | +1 điểm | +2 điểm |
|---|---|---|---|
| Số endpoint API mới/thay đổi | 0-1 | 2-3 | 4+ |
| Thay đổi DB schema | không đổi | thêm/sửa field | thêm bảng mới hoặc quan hệ phức tạp |
| Số màn hình UI bị ảnh hưởng | 1 | 2-3 | 4+ |
| Đụng tới cross-cutting concern (auth, payment, notification hệ thống) | không | có | — (tối đa +1, không cộng dồn thêm) |

## Quy đổi tổng điểm → size

```
0-1 điểm  → S   (1 bước, không cần BA+CTO, đi thẳng Dev nếu ở Runtime Mode)
2-3 điểm  → M   (2-3 bước, có gate giữa)
4-5 điểm  → L   (tách theo đơn vị nhỏ nhất — per User Story, có thể chạy song song)
6+ điểm   → XL  (bắt buộc full Build Mode DAG, không được đi tắt)
```

## Output

```json
{
  "size": "M",
  "score": 3,
  "breakdown": { "api_endpoints": 1, "db_schema": 1, "ui_screens": 1, "cross_cutting": 0 },
  "reasoning": "2 endpoint mới (+1), thêm 1 field DB (+1), 2 màn hình bị ảnh hưởng (+1)"
}
```

**Verify:** `breakdown` phải cộng đúng ra `score`; `reasoning` phải giải thích được từng điểm — không được trả `size` mà thiếu `breakdown`/`reasoning` đi kèm (tránh việc gán size cảm tính rồi nguỵ biện lý do sau).
