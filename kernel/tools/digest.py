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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _atomic import load_json_or_die, write_atomic

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
WBS = os.path.join(ROOT, "kernel", "memory", "wbs.json")
OUT = os.path.join(ROOT, "kernel", "memory", "today.md")
MAILBOX = os.path.join(ROOT, "kernel", "mailbox")
LIMITS = os.path.join(ROOT, "kernel", "config", "limits.json")

# Moi status phai co cho trong digest. Neu them status moi vao validate.STATUSES ma quen o day
# thi node o status do BIEN MAT khoi today.md (by=defaultdict chi tra bucket rong) — tuc Tier 0
# noi doi voi MOI agent. KNOWN_STATUSES ton tai de main() doi chieu va bao thay vi im lang.
KNOWN_STATUSES = {"blocked", "ready", "running", "waiting_sync", "done",
                  "waiting_human", "awaiting_human_decision", "failed"}


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
                # strip quote de dong y voi validate.parse_frontmatter va context_compile:
                # truoc day 3 tool doc `processed_at: 'null'` theo 3 kieu khac nhau.
                fm[k.strip()] = v.strip().strip("'\"")
        if fm.get("processed_at", "null") in ("null", "~", ""):
            out.append(fm)
    return out


WAITING_SYNC = "waiting_sync"


def build(wbs):
    nodes = wbs.get("nodes", [])
    by = defaultdict(list)
    for n in nodes:
        by[n.get("status")].append(n)
    unknown = {n.get("status") for n in nodes} - KNOWN_STATUSES
    if unknown:
        print(f"CANH BAO: status {sorted(unknown)} chua co muc nao trong digest -> node o "
              f"status do BIEN MAT khoi today.md. Them muc vao digest.py (Tier 0 phai phu het).",
              file=sys.stderr)

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

    # Dang cho tra loi Sync Session — KHONG phai loi, va KHONG phai "dang chay".
    # Tach rieng vi 2 ly do: (a) node nay da nha slot concurrency nen doc gia khong duoc tuong
    # role do dang bi chiem cho; (b) neu gop vao "Dang chay" thi C28 (stale running) va nguoi
    # doc deu chan doan sai thanh "agent hang".
    if by[WAITING_SYNC]:
        L.append("## Dang cho tra loi Sync Session (khong phai loi, khong giu slot)")
        for n in by[WAITING_SYNC]:
            g = n.get("gate") or {}
            answering = [m for m in nodes if m.get("sync_for_node") == n.get("node_id")]
            L.append(f"- {label(n)} — cho `{g.get('sync_waiting_for')}`")
            if answering:
                who = ", ".join("`{}` ({})".format(m.get("node_id"), m.get("status"))
                                for m in answering)
                L.append(f"  - ben tra loi: {who}")
            else:
                L.append(f"  - ⚠ KHONG co sync node nao tra loi -> node nay treo mai. "
                         f"Xem validate.py ma `C41` (ORCHESTRATOR.md §7d)")
        L.append("")

    L.append("## San sang chay ngay (ready)")
    if by["ready"]:
        for n in by["ready"]:
            L.append(f"- {label(n)}")
    else:
        L.append("- (khong co) — neu day KHONG phai vi da xong het thi la dau hieu treo, xem Blocker")
    L.append("")

    # Cho NGUOI QUYET DINH — tach hoan toan khoi Blocker vi day KHONG phai loi.
    # Gop vao Blocker se lam today.md (Tier 0, nap cho MOI agent) bao "co 1 blocker"
    # cho mot buoc hoan toan binh thuong cua quy trinh.
    # Xem kernel/gates/gate7-design-system-lock.md.
    waiting_dec = by["awaiting_human_decision"]
    if waiting_dec:
        L.append("## Dang cho NGUOI QUYET DINH (khong phai loi)")
        for n in waiting_dec:
            g = n.get("gate") or {}
            blocks = [m["node_id"] for m in nodes if n["node_id"] in m.get("depends_on", [])]
            L.append(f"- {label(n)} — gate `{g.get('name')}`, hoi luc `{g.get('decision_requested_at')}`")
            if blocks:
                L.append(f"  - dang chan: {', '.join(f'`{b}`' for b in blocks)}")
            L.append(f"  - chon bang: `python kernel/tools/resume.py {n['node_id']} "
                     f"--decision <id> --note \"...\"`")
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
    if waiting_dec:
        L.append(f"- NGUOI can chon phuong an cho {len(waiting_dec)} node "
                 f"(mo shared/design/theme-preview.html) — de do thi nhanh design nam cho")
    if stuck:
        L.append(f"- Xu ly {len(stuck)} blocker — de do thi downstream nam blocked vo ich")
    if not (by["running"] or msgs or by["ready"] or stuck or waiting_dec):
        L.append("- Khong con viec nao chay duoc. Neu chua done het -> DAG co van de, chay validate.py")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Sinh Tier 0 digest tu wbs.json + mailbox")
    ap.add_argument("--stdout", action="store_true", help="in ra thay vi ghi file")
    args = ap.parse_args()

    # load_json_or_die: truoc day json.load khong bao try -> wbs.json hong thi buoc cuoi
    # Event Loop (ORCHESTRATOR.md §7b) chet bang traceback tho thay vi noi ro phai sua gi.
    wbs = load_json_or_die(WBS, "kernel/memory/wbs.json")

    text = build(wbs)

    # Nguong tier0_max_lines truoc day la CONFIG CHET: limits.json ghi ro "digest.py phai giu
    # duoi nguong nay" nhung digest.py khong he doc field do. today.md duoc nap vao MOI agent
    # nen no phinh to la thue danh len toan he thong, khong phai len 1 agent.
    cap = 0
    if os.path.exists(LIMITS):
        try:
            with open(LIMITS, encoding="utf-8") as f:
                cap = ((json.load(f).get("context") or {}).get("tier0_max_lines")) or 0
        except Exception:
            cap = 0
    n_lines = len(text.splitlines())
    if cap and n_lines > cap:
        print(f"CANH BAO: today.md {n_lines} dong > tier0_max_lines={cap} "
              f"(kernel/config/limits.json). Tier 0 nap vao MOI agent nen day la thue toan he "
              f"thong. Xem lai muc nao dang dai nhat — thuong la danh sach 'Da xong' hoac so "
              f"node blocked.", file=sys.stderr)

    if args.stdout:
        print(text)
    else:
        write_atomic(OUT, text)   # xem kernel/tools/_atomic.py
        print(f"Da ghi {os.path.relpath(OUT, ROOT)} ({n_lines} dong"
              f"{f', nguong {cap}' if cap else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
