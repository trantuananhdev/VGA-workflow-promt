#!/usr/bin/env python3
"""
kernel/tools/digest.py — Sinh kernel/memory/today.md tu wbs.json + mailbox.

    python kernel/tools/digest.py            # ghi kernel/memory/today.md
    python kernel/tools/digest.py --stdout   # in ra, khong ghi file

Vi sao PHAI sinh tu dong thay vi dien tay:
  today.md la TIER 0 — duoc nap vao boot context cua MOI agent. Neu no muc (dien tay,
  quen cap nhat) thi KHONG chi scheduler sai, ma moi agent nhan context sai.
  Va moi field trong no deu derived 100% tu wbs.json + mailbox:
     phase hien tai  = node status:running
     dang cho        = message processed_at == null
     blocker         = node waiting_human/failed + node blocked bi chan
     completed       = node done
     next            = node status:ready
  Dien tay du lieu derived la dung loai loi da khien process-table.json bi bo.
"""
import argparse
import glob
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
WBS = os.path.join(ROOT, "kernel", "memory", "wbs.json")
OUT = os.path.join(ROOT, "kernel", "memory", "today.md")
MAILBOX = os.path.join(ROOT, "kernel", "mailbox")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def unprocessed():
    """Message chua tieu thu — doc frontmatter toi thieu, khong dung thu vien YAML."""
    out = []
    for p in sorted(glob.glob(os.path.join(MAILBOX, "*.md"))):
        try:
            text = open(p, encoding="utf-8").read()
        except Exception:
            continue
        if not text.startswith("---"):
            continue
        end = text.find("\n---", 3)
        if end == -1:
            continue
        fm = {}
        for line in text[3:end].splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
        if fm.get("processed_at", "null") in ("null", "~", ""):
            out.append(fm)
    return out


def build(wbs):
    nodes = wbs.get("nodes", [])
    by = defaultdict(list)
    for n in nodes:
        by[n.get("status")].append(n)

    def label(n):
        u = n.get("phase") or n.get("role")
        return f"`{n.get('node_id')}` ({u})"

    L = []
    L.append("# today.md — Tier 0 digest")
    L.append("")
    L.append("> **FILE SINH TU DONG — DUNG SUA TAY.** Chay `python kernel/tools/digest.py` de cap nhat.")
    L.append("> Moi so lieu duoi day derived tu `kernel/memory/wbs.json` + `kernel/mailbox/`;")
    L.append("> sua tay se lech voi trang thai that va lam MOI agent nhan context sai (day la Tier 0).")
    L.append(f">")
    L.append(f"> Sinh luc: {now()}")
    L.append("")

    if not nodes:
        L.append("**Trang thai:** chua co node nao — chua co project nao duoc khoi tao.")
        L.append("")
        L.append("Bat dau bang `/new-idea` (xem `agents/po/commands/new-idea.md`): Orchestrator se tao")
        L.append("track `intake` va khoi tao `wbs.json`.")
        return "\n".join(L) + "\n"

    tracks = sorted({n.get("track_id") for n in nodes if n.get("track_id")})
    total, done = len(nodes), len(by["done"])
    L.append(f"**Project:** `{wbs.get('project_id') or '(chua dat)'}`  ·  "
             f"**Track dang mo:** {', '.join(f'`{t}`' for t in tracks)}")
    L.append(f"**Tien do:** {done}/{total} node done"
             f"{'  ·  ' + str(round(100*done/total)) + '%' if total else ''}")
    L.append("")

    L.append("## Dang chay")
    if by["running"]:
        for n in by["running"]:
            L.append(f"- {label(n)} — started_at `{n.get('started_at')}`")
    else:
        L.append("- (khong co node nao dang chay)")
    L.append("")

    L.append("## San sang chay ngay (ready)")
    if by["ready"]:
        for n in by["ready"]:
            L.append(f"- {label(n)}")
    else:
        L.append("- (khong co) — neu day KHONG phai vi da xong het thi la dau hieu treo, xem Blocker")
    L.append("")

    stuck = by["waiting_human"] + by["failed"]
    L.append("## Blocker")
    if stuck:
        for n in stuck:
            g = n.get("gate") or {}
            blocks = [m["node_id"] for m in nodes if n["node_id"] in m.get("depends_on", [])]
            L.append(f"- **{n.get('status').upper()}** {label(n)} — gate `{g.get('name')}`, "
                     f"fail {g.get('consecutive_fail')} lan")
            if g.get("last_error"):
                L.append(f"  - loi cuoi: {g['last_error']}")
            if blocks:
                L.append(f"  - dang chan: {', '.join(f'`{b}`' for b in blocks)}")
            if n.get("status") == "waiting_human":
                L.append(f"  - go bang: `python kernel/tools/resume.py {n['node_id']} --note \"...\"`")
    else:
        L.append("- (khong co)")
    L.append("")

    # blocked nhung du dieu kien = quen RECOMPUTE_READY (loi im lang)
    ns = {n.get("node_id"): n for n in nodes}
    should_ready = [n for n in by["blocked"]
                    if n.get("depends_on") and all(ns.get(d, {}).get("status") == "done"
                                                    for d in n["depends_on"])]
    if should_ready:
        L.append("## ⚠ CANH BAO: node du dieu kien nhung van blocked")
        L.append("")
        L.append("Day la dau hieu `RECOMPUTE_READY()` bi bo sot o PHA A — he thong dang **treo im lang**:")
        for n in should_ready:
            L.append(f"- {label(n)} — moi depends_on da done ma status van `blocked`")
        L.append("")
        L.append("Chay `python kernel/tools/validate.py` (ma `C12`) va sua truoc khi tiep tuc.")
        L.append("")

    msgs = unprocessed()
    L.append("## Message chua tieu thu (input cua PHA A)")
    if msgs:
        for m in msgs:
            L.append(f"- `{m.get('message_id')}` {m.get('type')}: "
                     f"`{m.get('from')}` -> `{m.get('to')}` (node `{m.get('node_id')}`)")
    else:
        L.append("- (khong co)")
    L.append("")

    L.append("## Da xong")
    if by["done"]:
        for n in by["done"][-8:]:
            L.append(f"- {label(n)} — finished_at `{n.get('finished_at')}`")
        if len(by["done"]) > 8:
            L.append(f"- ... va {len(by['done']) - 8} node done truoc do")
    else:
        L.append("- (chua co)")
    L.append("")

    L.append("## Buoc ke tiep")
    if by["running"]:
        L.append(f"- Cho {len(by['running'])} node dang chay tra message ve `kernel/mailbox/`")
    if msgs:
        L.append(f"- PHA A: tieu thu {len(msgs)} message dang cho")
    if by["ready"]:
        L.append(f"- PHA B: dispatch {len(by['ready'])} node ready (kiem concurrency truoc)")
    if stuck:
        L.append(f"- Xu ly {len(stuck)} blocker — de do thi downstream nam blocked vo ich")
    if not (by["running"] or msgs or by["ready"] or stuck):
        L.append("- Khong con viec nao chay duoc. Neu chua done het -> DAG co van de, chay validate.py")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Sinh Tier 0 digest tu wbs.json + mailbox")
    ap.add_argument("--stdout", action="store_true", help="in ra thay vi ghi file")
    args = ap.parse_args()

    if not os.path.exists(WBS):
        print("LOI: khong tim thay kernel/memory/wbs.json", file=sys.stderr)
        return 2
    with open(WBS, encoding="utf-8") as f:
        wbs = json.load(f)

    text = build(wbs)
    if args.stdout:
        print(text)
    else:
        with open(OUT, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Da ghi {os.path.relpath(OUT, ROOT)} ({len(text.splitlines())} dong)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
