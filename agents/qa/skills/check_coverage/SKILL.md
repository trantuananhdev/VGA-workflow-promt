# skill_check_coverage

**Dùng bởi:** `qa` (riêng).

**Input:** build artifact (sau khi `skill_run_tests` đã chạy)

**Quy trình:**
```
<TODO: điền lệnh đo coverage thật của dự án, vd `flutter test --coverage`, `jest --coverage`>
<TODO: điền ngưỡng pass đã thống nhất của dự án, vd 80%>
```

**Output:**
```json
{ "coverage_percent": 0, "threshold": 0, "pass": false }
```

**Verify (thành phần của Gate 4):** `coverage_percent >= threshold` mới được tính pass. Kèm smoke test riêng (app khởi động không crash) — 2 điều kiện độc lập, cả 2 phải đạt.
