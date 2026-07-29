# skill_check_ad_policy

**Dùng bởi:** `ads` (phase `ads-placement`, mỗi story `monetization: true`) — điều kiện bổ sung của Gate 4.

**Quy trình:**
```
1. Kiểm tra consent management đã setup xong (ads-setup hoàn thành) — nếu chưa, FAIL ngay.
2. Kiểm tra vị trí quảng cáo không vi phạm chính sách phổ biến:
   - Không đặt quảng cáo sát/nằm trên nút bấm quan trọng (dễ bấm nhầm).
   - Interstitial không hiện ngay lúc mở app lần đầu (Google Play policy).
   - Rewarded ad phải cho user hoàn thành xem hết mới trả thưởng (không thưởng giả).
3. Kiểm tra tần suất quảng cáo khớp với PRD đã chốt (không tự tăng tần suất).
```

**Output:**
```json
{ "pass": true, "violations": [], "checked_at": "<timestamp>" }
```

**Verify:** nếu `violations` không rỗng, `ads` KHÔNG được emit handoff sang `qa` — phải sửa trước. Đây chính là điều kiện bổ sung của Gate 4 khi story có `monetization: true` (xem `kernel/gates/gate4-qa-to-release.md`).
