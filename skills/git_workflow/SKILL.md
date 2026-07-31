# skill_git_workflow

**Dùng bởi:** `dev-be`, `client`, `ads` (và `devops` cho phần tag/release — xem cuối file).

**Mục tiêu:** Chuẩn hoá thao tác git để mọi branch/commit/PR đều truy vết được về đúng `task_id` — Gate 3 verify bằng cách grep git log thật, không tin lời agent tự báo "xong".

## Quy ước branch

```
feature/<task_id>-<slug>   # feature_request bình thường (Build Mode)
fix/<task_id>-<slug>       # bug_report (Runtime Mode)
hotfix/<task_id>-<slug>    # crash_alert (Runtime Mode, ưu tiên cao)
```

`task_id` phải trùng khớp với node trong `kernel/memory/wbs.json` hoặc event Runtime Mode tương ứng — đây là cầu nối duy nhất giữa git history và toàn bộ trace log (`event-log.jsonl`).

## Quy ước commit

- Dòng đầu: ngắn gọn, mô tả thay đổi.
- Dòng cuối bắt buộc trailer: `Refs: <task_id>`.
- Không bao giờ commit trực tiếp vào `main`/`develop` — luôn qua Pull Request (cùng kỷ luật GitOps: không thay đổi trực tiếp nhánh production, mọi thứ qua review + CI).
- Không `git push --force` lên nhánh chia sẻ, không `--no-verify` bỏ qua hook — nếu hook fail, sửa nguyên nhân gốc rồi commit lại, không bypass.

## Quy ước Pull Request

PR description bắt buộc có 3 phần:
1. `task_id` + tóm tắt từ handoff envelope gần nhất liên quan (link `kernel/mailbox/<message_id>.md`).
2. Checklist Gate 3: lint pass? test pass? — kèm link/log thật, không phải tick suông.
3. Nếu có `doc_drift_detected` phát sinh trong lúc code, ghi rõ và link message tương ứng.

## Verify bắt buộc trước khi emit handoff sang `qa`

```bash
git log --grep "Refs: <task_id>" --oneline        # phải có ít nhất 1 commit
<lint command>                                      # exit code 0
<unit test command>                                 # pass, đọc toàn bộ output
gh pr view <pr_number> --json statusCheckRollup     # CI xanh
```

Không có PR mở + CI xanh = chưa được phép báo "xong story", bất kể code đã viết xong về mặt logic.

## Phần dùng bởi `devops` (release)

- Tag release theo semver: `v<major>.<minor>.<patch>`, không dùng tag `latest`.
- Merge vào `main` chỉ xảy ra sau khi Gate 4 (QA) pass — merge chính là trigger pipeline release, không có bước "deploy tay" song song.
