#!/usr/bin/env python3
"""
kernel/tools/resume.py — Duong quay lai duy nhat sau escalation.

Node o `waiting_human` khong tu thoat ra duoc. Tool nay la CACH DUY NHAT dua no tro lai
vong lap — va la mot lenh NGUYEN TU, khong the lam nua voi.

    python kernel/tools/resume.py US014-client-screen --note "sua STACK BINDING lint sang flutter analyze"
    python kernel/tools/resume.py US014-client-screen --abandon --note "story bi huy, PO da xac nhan"
    python kernel/tools/resume.py --list          # liet ke moi node dang cho nguoi

CO 2 LOAI "CHO NGUOI", tool nay phuc vu ca hai nhung KHONG tron chung:
  (a) waiting_human            = gate fail het luot retry  -> LOI. Dung --note.
  (b) awaiting_human_decision  = buoc binh thuong, nguoi phai QUYET DINH tham my (gate7)
                               -> dung --decision <id> --note. Khong tang consecutive_fail.

    python kernel/tools/resume.py PROJ-design-system --decision B-bold --note "khach muon CTA noi"
    python kernel/tools/resume.py PROJ-design-system --note "ca 3 qua lanh, lam lai tong am"
      ^ khong co --decision o node dang cho quyet dinh = TU CHOI het phuong an = fail thuc su

Vi sao khong sua tay wbs.json: sua tay rat de quen reset gate.consecutive_fail, node se
escalate lai NGAY lan fail tiep theo — con nguoi tuong da xu ly xong nhung he thong thi khong.
Tool nay lam dung 4 viec cung luc: doi status, reset bo dem, ghi resume_history, append event-log.
Voi --decision no lam them viec thu 5: ghi shared/design/theme-choice.json (owner __human__).
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _atomic import append_line, load_json_or_die, write_json_atomic

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
WBS = os.path.join(ROOT, "kernel", "memory", "wbs.json")
LOG = os.path.join(ROOT, "kernel", "memory", "event-log.jsonl")
LIMITS = os.path.join(ROOT, "kernel", "config", "limits.json")
THEME_CHOICE = os.path.join(ROOT, "shared", "design", "theme-choice.json")
TOKENS = os.path.join(ROOT, "shared", "design", "tokens.json")
AWAITING_DECISION = "awaiting_human_decision"


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load():
    return load_json_or_die(WBS, "kernel/memory/wbs.json")


def save(wbs):
    # NGUYEN TU: xem kernel/tools/_atomic.py. Truoc day dung open(...,"w") -> truncate truoc
    # khi ghi, nen crash giua luc ghi lam MAT nguon su that duy nhat cua scheduler.
    write_json_atomic(WBS, wbs)


def append_log(entry):
    append_line(LOG, json.dumps(entry, ensure_ascii=False))


def write_theme_choice(theme_id, note, by):
    """Ghi lua chon tham my cua NGUOI vao shared/design/theme-choice.json (owner __human__).

    Tool kernel ghi thay nguoi — cung co che resume.py ghi wbs.json (owner __kernel__).
    Agent `design-system` chi DOC file nay roi khoa tokens.json theo dung lua chon; neu de
    agent tu ghi lua chon thi khong con moc nao kiem duoc la nguoi da that su chon (gate7 lai
    thanh 'agent tu nhan xong la xong').
    """
    if not os.path.exists(THEME_CHOICE):
        print(f"LOI: khong tim thay {os.path.relpath(THEME_CHOICE, ROOT)} — "
              f"unit design-system chua chay lan nao?", file=sys.stderr)
        return False

    # Gate 7 dieu 1 doi chosen_theme PHAI ton tai trong tokens.json .themes. Truoc day tool
    # ghi BAT KY chuoi nao duoc truyen vao va khong tool nao doi chieu (validate.py chi doc
    # tokens.json -> responsive_contract). Mot loi go ('B-bold' vs 'b-bold') khoa mot theme
    # KHONG TON TAI, va no chi lo ra o buoc dung mau — sau khi ca nhanh design da di tiep.
    themes = None
    if os.path.exists(TOKENS):
        try:
            with open(TOKENS, encoding="utf-8") as f:
                t = json.load(f)
            raw = t.get("themes")
            if isinstance(raw, dict):
                themes = [k for k in raw if not k.startswith("_")]
            elif isinstance(raw, list):
                themes = [x.get("theme_id") if isinstance(x, dict) else x for x in raw]
        except Exception as e:
            print(f"CANH BAO: khong doc duoc {os.path.relpath(TOKENS, ROOT)} ({e}) -> "
                  f"KHONG doi chieu duoc theme_id. Kiem tay truoc khi tin.", file=sys.stderr)
    if themes is not None:
        if not themes:
            print(f"LOI: {os.path.relpath(TOKENS, ROOT)} khong co phuong an theme nao -> "
                  f"design-system chua dung du phuong an, khong co gi de chon.", file=sys.stderr)
            return False
        if theme_id not in themes:
            print(f"LOI: theme_id={theme_id!r} KHONG co trong "
                  f"{os.path.relpath(TOKENS, ROOT)} .themes. Cac phuong an that: {sorted(themes)}\n"
                  f"     Gate 7 dieu 1 doi chosen_theme tro vao 1 phuong an ton tai — ghi ten sai "
                  f"se khoa mot theme khong co, va loi chi lo ra sau khi ca nhanh design da di tiep.",
                  file=sys.stderr)
            return False

    with open(THEME_CHOICE, encoding="utf-8") as f:
        tc = json.load(f)
    prev = tc.get("chosen_theme")
    if prev:
        tc.setdefault("history", []).append({
            "chosen_theme": prev, "decided_at": tc.get("decided_at"),
            "decided_by": tc.get("decided_by"), "note": tc.get("note"),
        })
    tc["chosen_theme"] = theme_id
    tc["decided_at"] = now()
    tc["decided_by"] = by
    tc["note"] = note
    write_json_atomic(THEME_CHOICE, tc)
    print(f"     da ghi shared/design/theme-choice.json  chosen_theme={theme_id!r}")
    return True


def cmd_list(wbs):
    stuck = [n for n in wbs.get("nodes", [])
             if n.get("status") in ("waiting_human", "failed", AWAITING_DECISION)]
    if not stuck:
        print("Khong co node nao dang cho nguoi can thiep.")
        return 0
    print(f"{len(stuck)} node dang cho nguoi:\n")
    for n in stuck:
        g = n.get("gate") or {}
        print(f"  {n['node_id']}  [{n.get('status')}]  role={n.get('role')} track={n.get('track')}")
        if n.get("status") == AWAITING_DECISION:
            print(f"      gate={g.get('name')}  CHO QUYET DINH (khong phai loi)  "
                  f"hoi luc={g.get('decision_requested_at')}")
            print(f"      -> xem shared/design/theme-preview.html roi chay:")
            print(f"         python kernel/tools/resume.py {n['node_id']} --decision <id> --note \"...\"")
            continue
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
    ap.add_argument("--decision", help="CHI cho node awaiting_human_decision: id phuong an nguoi chon "
                                       "(vd theme_id trong shared/design/tokens.json .themes)")
    ap.add_argument("--by", default="human", help="ai thuc hien (mac dinh: human)")
    ap.add_argument("--list", action="store_true", help="liet ke node dang cho nguoi")
    ap.add_argument("--requeue", action="store_true",
                    help="CHI cho node running da qua stale_running_hours: giai phong slot "
                         "concurrency cua agent da chet, dua node ve ready/blocked")
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
    if args.requeue:
        # DUONG RA KHOI `running` — truoc day KHONG TON TAI.
        # limits.json node.stale_action mo ta ro phai lam gi, nhung khong tool nao doc field do;
        # C28 chi BAO; va chinh resume.py tu choi node running. Ket qua: agent chet -> node giu
        # 1 slot concurrency VINH VIEN, va cach duy nhat la sua tay wbs.json — dung viec ma
        # resume.py ton tai de cam.
        if st != "running":
            print(f"LOI: --requeue chi dung cho node status='running' (node nay dang {st!r}).",
                  file=sys.stderr)
            return 2
        stale_h = 6
        if os.path.exists(LIMITS):
            try:
                with open(LIMITS, encoding="utf-8") as f:
                    stale_h = ((json.load(f).get("node") or {}).get("stale_running_hours")) or 6
            except Exception:
                pass
        sa = node.get("started_at")
        age_h = None
        if sa:
            try:
                t0 = datetime.fromisoformat(str(sa).replace("Z", "+00:00"))
                if t0.tzinfo is None:
                    t0 = t0.replace(tzinfo=timezone.utc)
                age_h = (datetime.now(timezone.utc) - t0).total_seconds() / 3600
            except Exception:
                pass
        if age_h is not None and age_h < stale_h:
            print(f"LOI: node {args.node_id} moi running {age_h:.1f} gio, chua qua nguong "
                  f"stale_running_hours={stale_h}. KHONG requeue: neu agent van dang chay that "
                  f"ma dua node ve ready thi vong sau se spawn instance THU HAI cung lam 1 node "
                  f"(xem kernel/config/limits.json node.stale_action).", file=sys.stderr)
            return 2
        if not args.note:
            print("LOI: --note la BAT BUOC (ghi ro vi sao tin la agent da chet).", file=sys.stderr)
            return 2

        g = node.setdefault("gate", {})
        g.setdefault("resume_history", []).append({
            "at": now(), "note": args.note, "by": args.by, "decision": None,
            "from_status": st, "fail_count_when_stuck": g.get("consecutive_fail", 0),
            "requeue_after_hours": round(age_h, 1) if age_h is not None else None,
        })
        deps = node.get("depends_on", [])
        all_done = all(nodes.get(d, {}).get("status") == "done" for d in deps)
        node["status"] = "ready" if all_done else "blocked"
        node["started_at"] = None
        # KHONG reset consecutive_fail: agent chet KHONG phai "nguoi da sua xong loi".
        # Reset o day se xoa mat lich su fail va node co the retry vo han ma khong bao gio escalate.
        g["last_error"] = f"stale: running {age_h:.1f}h > {stale_h}h, agent khong tra message"
        save(wbs)
        append_log({"ts": now(), "event": "requeue", "node_id": node["node_id"],
                    "task_id": node.get("story_id"), "role": node.get("role"),
                    "from_status": st, "to_status": node["status"],
                    "note": args.note, "by": args.by, "decision": None})
        print(f"OK: {node['node_id']}  running -> {node['status']}  (da giai phong 1 slot "
              f"concurrency cua role {node.get('role')!r})")
        print(f"     consecutive_fail GIU NGUYEN ({g.get('consecutive_fail', 0)}) — agent chet "
              f"khong phai la 'da sua xong loi'")
        print(f"     CANH BAO: chi dung khi CHAC agent da chet. Neu no van dang chay thi gio "
              f"se co 2 instance cung lam node nay.")
        return 0

    if st not in ("waiting_human", "failed", AWAITING_DECISION):
        print(f"LOI: node {args.node_id} dang o status={st!r}. Tool nay chi dung cho "
              f"'waiting_human', 'failed' hoac '{AWAITING_DECISION}' — khong dung de doi "
              f"trang thai binh thuong (do la viec cua Orchestrator trong Event Loop).\n"
              f"     Node treo o 'running' qua {'nguong stale' if st == 'running' else 'lau'}: "
              f"dung --requeue --note \"...\".", file=sys.stderr)
        return 2
    if not args.note:
        print("LOI: --note la BAT BUOC. Ghi ro nguoi da sua gi (hoac vi sao chon phuong an do) — "
              "neu khong, lan sau khong ai biet vi sao node nay tung treo va da duoc cuu the nao.",
              file=sys.stderr)
        return 2
    if args.decision and st != AWAITING_DECISION:
        print(f"LOI: --decision chi dung cho node o status={AWAITING_DECISION!r}, "
              f"node nay dang {st!r}. Node fail thi sua nguyen nhan roi resume bang --note.",
              file=sys.stderr)
        return 2
    if args.decision and args.abandon:
        print("LOI: --decision va --abandon loai tru nhau.", file=sys.stderr)
        return 2

    g = node.setdefault("gate", {})
    g.setdefault("resume_history", []).append({
        "at": now(), "note": args.note, "by": args.by, "decision": args.decision,
        "from_status": st, "fail_count_when_stuck": g.get("consecutive_fail", 0),
    })

    if args.decision:
        # QUYET DINH cua nguoi — KHONG phai cuu 1 node loi.
        # Khong cham consecutive_fail: attempt van la 1 nen context_compile khong doi last_error
        # (xem G9). Node chay lai chi de KHOA token theo lua chon, khong phai lam lai tu dau.
        if not write_theme_choice(args.decision, args.note, args.by):
            return 2
        deps = node.get("depends_on", [])
        all_done = all(nodes.get(d, {}).get("status") == "done" for d in deps)
        node["status"] = "ready" if all_done else "blocked"
        node["started_at"] = None
        g["decision"] = args.decision
        g["decision_requested_at"] = None      # xoa de C34 khong canh bao field cu
        g["result"] = None
        event, new_st = "decision", node["status"]
    elif args.abandon:
        node["status"] = "failed"
        node["finished_at"] = now()
        # Xoa co cho-quyet-dinh: bo han 1 node dang awaiting_human_decision ma de lai field nay
        # thi C34 canh bao MAI MAI (2 nhanh kia da xoa, nhanh nay thi quen).
        g["decision_requested_at"] = None
        event, new_st = "abandon", "failed"
    else:
        # dependency co the da thay doi trong luc treo -> tinh lai thay vi mac dinh ready
        deps = node.get("depends_on", [])
        all_done = all(nodes.get(d, {}).get("status") == "done" for d in deps)
        node["status"] = "ready" if all_done else "blocked"
        node["started_at"] = None
        g["result"] = None
        if st == AWAITING_DECISION:
            # Nguoi da xem het phuong an va TU CHOI ca -> day la fail THUC SU cua gate7,
            # khac han voi cuu 1 node dang treo vi loi ky thuat. Vi vay TANG bo dem
            # (het luot thi node -> waiting_human that su, va do la dung: agent khong
            # tu nghi ra duoc phuong an nguoi chap nhan sau N lan thi can nguoi vao sau hon).
            g["consecutive_fail"] = g.get("consecutive_fail", 0) + 1
            g["last_error"] = f"nguoi tu choi moi phuong an: {args.note}"
            g["decision_requested_at"] = None
            event, new_st = "reject", node["status"]
        else:
            g["consecutive_fail"] = 0
            g["last_error"] = None
            g["escalated_at"] = None
            event, new_st = "resume", node["status"]

    save(wbs)
    append_log({
        "ts": now(), "event": event, "node_id": node["node_id"],
        "task_id": node.get("story_id"), "role": node.get("role"),
        "from_status": st, "to_status": new_st, "note": args.note, "by": args.by,
        "decision": args.decision,
    })

    print(f"OK: {node['node_id']}  {st} -> {new_st}")
    if event == "decision":
        print(f"     quyet dinh cua nguoi: {args.decision!r} — consecutive_fail GIU NGUYEN "
              f"({g.get('consecutive_fail', 0)}), day khong phai retry sau loi")
        print(f"     -> {new_st}: node chay lai chi de khoa token theo lua chon nay, roi gate7 kiem lai")
    elif event == "reject":
        print(f"     nguoi tu choi moi phuong an -> tinh la gate fail thuc su, "
              f"consecutive_fail = {g.get('consecutive_fail')}")
        print(f"     -> {new_st}: agent dung lai bo phuong an moi theo --note")
    elif event == "resume":
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
