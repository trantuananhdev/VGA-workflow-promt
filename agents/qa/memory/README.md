# Bo nho lam viec cua agent — MOT FILE MOI NODE

> **Quy uoc bat buoc:** `<node_id>.md`, vi du `US014-client-screen.md`, `BUG042-qa.md`.
> **KHONG dung 1 file chung** (truoc day la `today.md`).

## Vi sao

Agent nay co the chay nhieu instance song song (`concurrency` trong `manifest.json`).
Neu moi instance ghi cung 1 file `today.md` thi ban ghi sau de mat ban ghi truoc —
dung loai race ma `kernel/contracts/data-ownership.json` sinh ra de chan.
Dat ten theo `node_id` thi moi instance co file rieng, khong the tranh chap.

## Ai duoc doc

- Chinh agent nay (instance dang xu ly node do)
- Orchestrator (CHI DOC, khong sua)
- **Khong agent nao khac** — muon biet ket qua thi doc handoff message trong `kernel/mailbox/`

## Noi dung goi y

```markdown
## <node_id>
**Dang lam:** <buoc hien tai>
**Ket qua gan nhat:** <...>
**Cho phan hoi tu:** <role, neu dang mo Sync Session>
**Ghi chu:** <thong tin can nho giua cac lan retry cua CUNG node nay>
```

Ket qua CHINH THUC di qua handoff message, khong qua file nay. File nay chi la nhap
nhay lam viec cua 1 node — xoa duoc ma khong mat gi quan trong.
