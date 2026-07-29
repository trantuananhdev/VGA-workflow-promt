#!/usr/bin/env python3
"""
kernel/tools/resume.py — Duong quay lai duy nhat sau escalation.

Node o `waiting_human` khong tu thoat ra duoc. Tool nay la CACH DUY NHAT dua no tro lai
vong lap — va la mot lenh NGUYEN TU, khong the lam nua voi.

    python kernel/tools/resume.py US014-mobile-screen --note "sua STACK BINDING lint sang flutter analyze"
    python kernel/tools/resume.py US014-mobile-screen --abandon --note "story bi huy, PO da xac nhan"
    python kernel/tools/resume.py --list          # liet ke moi node dang cho nguoi

Vi sao khong sua tay wbs.json: sua tay rat de quen reset gate.consecutive_fail, node se
escalate lai NGAY lan fail tiep theo — con nguoi tuong da xu ly xong nhung he thong thi khong.
Tool nay lam dung 4 viec cung luc: doi status, reset bo dem, ghi resume_history, append event-log.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
WBS = os.path.join(ROOT, "kernel", "memory", "wbs.json")
LOG = os.path.join(ROOT, "kernel", "memory", "event-log.jsonl")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load():
    if not os.path.exists(WBS):
        print("LOI: khong tim thay kernel/memory/wbs.json", file=sys.stderr)
        sys.exit(2)
    with open(WBS, encoding="utf-8") as f:
        return json.load(f)


def save(wbs):
    with open(WBS, "w", encoding="utf-8") as f:
        json.dump(wbs, f, ensure_ascii=False, indent=2)
        f.write("\n")


def append_log(entry):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def cmd_list(wbs):
    stuck = [n for n in wbs.get("nodes", []) if n.get("status") in ("waiting_human", "failed")]
    if not stuck:
        print("Khong co node nao dang cho nguoi can thiep.")
        return 0
    print(f"{len(stuck)} node dang cho nguoi:\n")
    for n in stuck:
        g = n.get("gate") or {}
        print(f"  {n['node_id']}  [{n.get('status')}]  role={n.get('role')} track={n.get('track')}")
        print(f"      gate={g.get('name')} fail={g.get('consecutive_fail')} escalated_at={g.get('escalated_at')}")
        if g.get("last_error"):
            print(f"      loi cuoi: {g['last_error']}")
        if g.get("resume_history"):
            print(f"      da cuu {len(g['resume_history'])} lan truoc do")
        # node bi chan boi node nay
        blocked = [m["node_id"] for m in wbs["nodes"] if n["node_id"] in m.get("depends_on", [])]
        if blocked:
            print(f"      dang chan: {blocked}")
        print()
    return 0


def main():
    ap = argparse.ArgumentParser(description="Dua node tu waiting_human tro lai vong lap")
    ap.add_argument("node_id", nargs="?", help="node_id can resume")
    ap.add_argument("--note", help="BAT BUOC: nguoi da sua gi (lop Evolution doc lai)")
    ap.add_argument("--abandon", action="store_true", help="bo han node nay (waiting_human -> failed)")
    ap.add_argument("--by", default="human", help="ai thuc hien (mac dinh: human)")
    ap.add_argument("--list", action="store_true", help="liet ke node dang cho nguoi")
    args = ap.parse_args()

    wbs = load()
    if args.list or not args.node_id:
        return cmd_list(wbs)

    nodes = {n.get("node_id"): n for n in wbs.get("nodes", [])}
    node = nodes.get(args.node_id)
    if node is None:
        print(f"LOI: khong co node {args.node_id!r} trong wbs.json", file=sys.stderr)
        return 2

    st = node.get("status")
    if st not in ("waiting_human", "failed"):
        print(f"LOI: node {args.node_id} dang o status={st!r}. Tool nay chi dung cho "
              f"'waiting_human' hoac 'failed' — khong dung de doi trang thai binh thuong "
              f"(do la viec cua Orchestrator trong Event Loop).", file=sys.stderr)
        return 2
    if not args.note:
        print("LOI: --note la BAT BUOC. Ghi ro nguoi da sua gi — neu khong, lan sau "
              "khong ai biet vi sao node nay tung treo va da duoc cuu the nao.", file=sys.stderr)
        return 2

    g = node.setdefault("gate", {})
    g.setdefault("resume_history", []).append({
        "at": now(), "note": args.note, "by": args.by,
        "from_status": st, "fail_count_when_stuck": g.get("consecutive_fail", 0),
    })

    if args.abandon:
        node["status"] = "failed"
        node["finished_at"] = now()
        event, new_st = "abandon", "failed"
    else:
        # dependency co the da thay doi trong luc treo -> tinh lai thay vi mac dinh ready
        deps = node.get("depends_on", [])
        all_done = all(nodes.get(d, {}).get("status") == "done" for d in deps)
        node["status"] = "ready" if all_done else "blocked"
        node["started_at"] = None
        g["consecutive_fail"] = 0
        g["result"] = None
        g["last_error"] = None
        g["escalated_at"] = None
        event, new_st = "resume", node["status"]

    save(wbs)
    append_log({
        "ts": now(), "event": event, "node_id": node["node_id"],
        "task_id": node.get("story_id"), "role": node.get("role"),
        "from_status": st, "to_status": new_st, "note": args.note, "by": args.by,
    })

    print(f"OK: {node['node_id']}  {st} -> {new_st}")
    if event == "resume":
        print(f"     consecutive_fail da reset ve 0")
        if new_st == "blocked":
            pend = [d for d in node.get("depends_on", []) if nodes.get(d, {}).get("status") != "done"]
            print(f"     -> blocked (khong phai ready) vi con dependency chua done: {pend}")
        else:
            print(f"     -> ready: vong Event Loop tiep theo se dispatch lai")
    else:
        blocked = [m["node_id"] for m in wbs["nodes"] if node["node_id"] in m.get("depends_on", [])]
        if blocked:
            print(f"     CANH BAO: {len(blocked)} node se blocked VINH VIEN vi phu thuoc node vua bo: {blocked}")
            print(f"     -> phai xu ly rieng tung node do (resume/abandon), he thong khong tu cascade.")
    print(f"     da ghi event-log + resume_history (lan cuu thu {len(g['resume_history'])})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
