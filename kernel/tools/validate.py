#!/usr/bin/env python3
"""
kernel/tools/validate.py — Kiem tra tinh nhat quan cua CONTROL PLANE.

Muc dich: bien Gate 0 / Gate 2 tu "loi hua trong tai lieu" thanh kiem tra thuc thi duoc.
Chay duoc boi BAT KY AI tool nao (Cursor, Claude, ...) — chi dung Python stdlib, khong dependency.

    python kernel/tools/validate.py              # kiem tra trang thai repo hien tai
    python kernel/tools/validate.py --selftest   # + mo phong 3 track tu dag.json (kiem LUAT, khong can du lieu thuc)
    python kernel/tools/validate.py --json       # output JSON cho tool tu dong doc

Exit code: 0 = khong co ERROR (co the co WARN) | 1 = co ERROR
"""
import json
import os
import re
import sys
import glob
import argparse
from collections import defaultdict
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FINDINGS = []          # (severity, code, message)
STATUSES = {"blocked", "ready", "running", "done",
            "waiting_human", "awaiting_human_decision", "failed"}
TERMINAL_STUCK = {"waiting_human", "failed"}
# awaiting_human_decision KHONG nam trong TERMINAL_STUCK: no la buoc BINH THUONG cua quy trinh
# (nguoi chon phuong an theme o gate7), khong phai loi. Tron vao TERMINAL_STUCK se lam
# gate.consecutive_fail va C22 mat nghia. Xem kernel/gates/gate7-design-system-lock.md.
AWAITING_DECISION = "awaiting_human_decision"
MSG_TYPES = {"handoff", "request", "response"}


def add(sev, code, msg):
    FINDINGS.append((sev, code, msg))


def err(code, msg):
    add("ERROR", code, msg)


def warn(code, msg):
    add("WARN", code, msg)


def rel(*p):
    return os.path.join(ROOT, *p)


def load_json(path, code):
    """Doc JSON, bao ERROR neu thieu/hong. Tra None neu that bai."""
    full = rel(path)
    if not os.path.exists(full):
        err(code, f"thieu file bat buoc: {path}")
        return None
    try:
        with open(full, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        err(code, f"{path}: JSON khong parse duoc — {e}")
        return None


def strip_meta(d):
    """Bo cac key ghi chu (_comment, _note...) de kiem tra logic."""
    return {k: v for k, v in d.items() if not k.startswith("_")}


# ─────────────────────────── YAML frontmatter (khong dung thu vien) ───────────────────────────
def parse_frontmatter(path):
    """Tra (dict, error). Chi ho tro key: value phang — dung du cho message.schema.json.

    dict tra ve co them 2 key noi bo: __body_lines__, __body_chars__ (de kiem gioi han body).
    """
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        return None, f"khong doc duoc: {e}"
    if not text.startswith("---"):
        return None, "khong co YAML frontmatter (phai bat dau bang '---')"
    end = text.find("\n---", 3)
    if end == -1:
        return None, "frontmatter khong dong (thieu '---' ket thuc)"
    body = text[end + 4:]
    out = {"__body_lines__": len(body.splitlines()), "__body_chars__": len(body)}
    for line in text[3:end].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            return None, f"dong khong phai 'key: value': {line!r}"
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if v in ("null", "~", ""):
            out[k] = None
        elif v in ("true", "false"):
            out[k] = v == "true"
        elif v.lstrip("-").isdigit():
            out[k] = int(v)
        else:
            out[k] = v.strip("'\"")
    return out, None


# ─────────────────────────── A. Manifest ───────────────────────────
def check_manifests(schema, escalation):
    """agents/*/manifest.json dung schema, agent_id khop thu muc, notify key ton tai."""
    mans = {}
    if schema is None:
        return mans
    allowed = set(schema.get("properties", {}))
    required = set(schema.get("required", []))
    closed = schema.get("additionalProperties") is False
    channels = set((escalation or {}).get("channels", {}))

    for p in sorted(glob.glob(rel("agents", "*", "manifest.json"))):
        folder = os.path.basename(os.path.dirname(p))
        try:
            with open(p, encoding="utf-8") as f:
                m = json.load(f)
        except Exception as e:
            err("A1", f"agents/{folder}/manifest.json khong parse duoc — {e}")
            continue
        mans[folder] = m

        missing = required - set(m)
        if missing:
            err("A2", f"manifest {folder}: thieu field bat buoc {sorted(missing)}")
        if closed:
            # key bat dau bang '_' la ghi chu cho nguoi doc -> luon duoc phep
            extra = {k for k in m if k not in allowed and not k.startswith("_")}
            if extra:
                err("A3", f"manifest {folder}: field khong duoc phep {sorted(extra)} "
                           f"(schema dong — dependency/trigger phai khai o dag.json)")
        if folder != "_template" and m.get("agent_id") != folder:
            err("A4", f"manifest {folder}: agent_id={m.get('agent_id')!r} khac ten thu muc")

        tier = m.get("model_tier")
        enum = schema.get("properties", {}).get("model_tier", {}).get("enum")
        if enum and tier not in enum:
            err("A5", f"manifest {folder}: model_tier={tier!r} khong thuoc {enum}")
        if not isinstance(m.get("concurrency"), int) or m.get("concurrency", 0) < 1:
            err("A6", f"manifest {folder}: concurrency phai la int >= 1")
        if not isinstance(m.get("max_context_tokens"), int) or m.get("max_context_tokens", 0) < 500:
            err("A7", f"manifest {folder}: max_context_tokens phai la int >= 500")

        notify = (m.get("escalation") or {}).get("notify")
        if folder != "_template" and channels and notify not in channels:
            err("A8", f"manifest {folder}: escalation.notify={notify!r} khong co trong "
                       f"kernel/config/escalation.json channels {sorted(channels)}")
    return mans


# ─────────────────────────── B. dag.json ───────────────────────────
def unit_deps(units, u, include_conditional=True):
    d = list(units[u].get("depends_on", []))
    if include_conditional:
        d += [c["unit"] for c in units[u].get("conditional_depends_on", [])]
    return [x for x in d if x != "gate1"]


def check_dag(dag, mans):
    if dag is None:
        return {}
    units = strip_meta(dag.get("units", {}))
    agents = {a for a in mans if a != "_template"}
    gate_files = {os.path.basename(f).split("-")[0] for f in glob.glob(rel("kernel", "gates", "*.md"))}

    for u, d in units.items():
        if "core" in d:
            err("B1", f"dag unit {u}: khong duoc khai 'core' o day — core thuoc "
                       f"agents/<role>/manifest.json (bat/tat theo AGENT, khong theo phase)")
        role = d.get("role")
        if role not in agents:
            err("B2", f"dag unit {u}: role {role!r} khong co agents/{role}/")
        g = d.get("gate")
        if g and g not in gate_files:
            err("B3", f"dag unit {u}: gate {g!r} khong co file trong kernel/gates/")
        if d.get("scope") not in ("story", "project", "release"):
            err("B4", f"dag unit {u}: scope={d.get('scope')!r} khong hop le")

        for f in d.get("feeds", []):
            if f == "gate1":
                continue
            if f not in units:
                err("B5", f"dag {u}.feeds -> {f!r} khong phai unit")
            elif u not in unit_deps(units, f):
                err("B6", f"LECH CHIEU: {u}.feeds co {f!r} nhung {f}.depends_on thieu {u!r}")
        for f in d.get("runtime_feeds", []):
            if f not in units:
                err("B7", f"dag {u}.runtime_feeds -> {f!r} khong phai unit")
        for x in unit_deps(units, u):
            if x not in units:
                err("B8", f"dag {u}.depends_on -> {x!r} khong phai unit")
            elif u not in units[x].get("feeds", []):
                err("B9", f"LECH CHIEU: {u} depends_on {x!r} nhung {x}.feeds thieu {u!r}")

    # chu trinh
    color = {}

    def dfs(u, path):
        if color.get(u) == 1:
            err("B10", f"CHU TRINH trong dag: {' -> '.join(path + [u])}")
            return
        if color.get(u) == 2 or u not in units:
            return
        color[u] = 1
        for x in unit_deps(units, u):
            dfs(x, path + [u])
        color[u] = 2

    for u in units:
        dfs(u, [])

    # sync_allowed
    sync = strip_meta(dag.get("sync_allowed", {}))
    for a, partners in sync.items():
        if a not in agents:
            err("B11", f"sync_allowed key {a!r} khong phai agent")
        for p in partners:
            if p not in agents:
                err("B12", f"sync_allowed[{a}] -> {p!r} khong phai agent")
            elif a not in sync.get(p, []):
                err("B13", f"SYNC KHONG DOI XUNG: {a}->{p} co nhung {p}->{a} thieu "
                            f"(hoi duoc thi phai tra loi duoc)")
    for a in agents:
        if a not in sync:
            warn("B14", f"agent {a} khong co entry trong sync_allowed (khong mo Sync Session duoc)")
        if not any(d.get("role") == a for d in units.values()):
            err("B15", f"agent {a} khong co unit nao trong dag.json -> khong bao gio duoc dispatch")
    return units


# ─────────────────────────── Quy tac giao tap (dung chung wbs + selftest) ───────────────────────────
def expected_deps(units, unit, track_units, monetization):
    """depends_on ky vong = (depends_on + conditional thoa) \\ {gate1} GIAO {unit co node trong track}."""
    raw = [x for x in units[unit].get("depends_on", []) if x != "gate1"]
    for c in units[unit].get("conditional_depends_on", []):
        if c.get("only_if") == "story.Monetization == true" and monetization:
            raw.append(c["unit"])
        elif c.get("only_if") is None:
            raw.append(c["unit"])
    return sorted(set(raw) & set(track_units))


def downstream_closure(units, start):
    seen, stack = {start}, [start]
    while stack:
        for f in units[stack.pop()].get("feeds", []):
            if f != "gate1" and f in units and f not in seen:
                seen.add(f)
                stack.append(f)
    return sorted(seen)


# ─────────────────────────── C. wbs.json ───────────────────────────
def check_wbs(wbs, units, mans, profile, limits=None):
    if wbs is None or not units:
        return {}
    nodes_list = wbs.get("nodes", [])
    if not isinstance(nodes_list, list):
        err("C0", "wbs.json: 'nodes' phai la mang")
        return {}
    if not nodes_list:
        warn("C1", "wbs.json chua co node nao (repo template) — cac kiem tra trang thai bi bo qua. "
                   "Dung --selftest de kiem LUAT sinh track ma khong can du lieu thuc.")
        return {}

    nodes, seen_ids = {}, set()
    for n in nodes_list:
        nid = n.get("node_id")
        if not nid:
            err("C2", f"wbs node thieu node_id: {n}")
            continue
        if nid in seen_ids:
            err("C3", f"node_id TRUNG: {nid!r} — no la dia chi cua message, trung = routing sai")
        seen_ids.add(nid)
        nodes[nid] = n

    # map node -> unit
    by_unit = {}
    for u, d in units.items():
        by_unit[(d.get("role"), d.get("phase"))] = u

    active_caps = set((profile or {}).get("active_capability_agents", []))

    for nid, n in nodes.items():
        role, phase = n.get("role"), n.get("phase")
        unit = by_unit.get((role, phase))
        if unit is None:
            err("C4", f"node {nid}: (role={role!r}, phase={phase!r}) khong khop unit nao trong dag.json")
        if role not in mans:
            err("C5", f"node {nid}: role {role!r} khong co agents/{role}/manifest.json")
        if n.get("status") not in STATUSES:
            err("C6", f"node {nid}: status={n.get('status')!r} khong thuoc {sorted(STATUSES)}")
        if n.get("track") not in ("intake", "build", "runtime"):
            err("C7", f"node {nid}: track={n.get('track')!r} khong hop le")

        # dependency ton tai
        for dep in n.get("depends_on", []):
            if dep not in nodes:
                err("C8", f"node {nid}: depends_on -> {dep!r} KHONG TON TAI "
                           f"-> node nay blocked vinh vien (scheduler treo im lang)")

        # gate.name khop dag
        if unit:
            want = units[unit].get("gate")
            got = (n.get("gate") or {}).get("name")
            if want != got:
                err("C9", f"node {nid}: gate.name={got!r} nhung dag.units[{unit}].gate={want!r}")

        # C23-C25: gate nhieu ben ky (gate1)
        g = n.get("gate") or {}
        if g.get("name") == "gate1":
            req = g.get("required_signoffs")
            if req is None:
                err("C23", f"node {nid}: gate1 phai co gate.required_signoffs (vd [\"ba\",\"cto\"]) "
                            f"-> khong co thi khong the biet du chu ky chua")
            else:
                signed = [s.get("role") for s in g.get("signoffs", [])]
                dup = {r for r in signed if signed.count(r) > 1}
                if dup:
                    err("C24", f"node {nid}: signoffs co role ky nhieu lan {sorted(dup)} "
                                f"-> nghi van 1 ben ky thay ben kia")
                if n.get("status") == "done" and set(req) - set(signed):
                    err("C25", f"node {nid}: status=done nhung signoffs THIEU {sorted(set(req)-set(signed))} "
                                f"-> Gate 1 khong duoc pass khi chua du chu ky (1 ben khong duoc ky thay ben kia)")
                for s in g.get("signoffs", []):
                    if not s.get("message_id"):
                        err("C26", f"node {nid}: signoff cua {s.get('role')!r} thieu message_id "
                                    f"-> khong the doi chieu la chinh ben do ky")
        elif g.get("required_signoffs") or g.get("signoffs"):
            warn("C27", f"node {nid}: co signoffs nhung gate={g.get('name')!r} khong phai gate nhieu ben "
                        f"-> field du, kiem tra lai")

        # quy tac giao tap
        if unit:
            # PHAM VI "cung track" — KHONG phai cung track_id.
            # Track `build` co NHIEU track_id cung luc: PROJ (scope project), REL (scope release),
            # US014/US015... (scope story) — xem wbs.json._tracks. Node scope=story hoan toan
            # duoc phep depends_on node scope=project (US014-mobile-screen -> PROJ-mobile-shell,
            # US014-designer-screen -> PROJ-design-system). Neu gom peer theo track_id thi
            # PROJ-* bi coi la "khong co node trong track" -> giao tap loai no ra -> C10 bao sai
            # tren MOI node mobile-screen/designer-screen cua moi project thuc.
            # Rieng intake/runtime: moi track_id la 1 the hien DOC LAP (BUG042 vs BUG043 co the
            # co entry unit khac nhau) nen van phai gom theo track_id.
            if n.get("track") == "build":
                peers = [m for m in nodes.values() if m.get("track") == "build"]
            else:
                peers = [m for m in nodes.values() if m.get("track_id") == n.get("track_id")]
            track_units = set()
            for m in peers:
                tu = by_unit.get((m.get("role"), m.get("phase")))
                if tu:
                    track_units.add(tu)
            monet = any(c["unit"] in track_units for c in units[unit].get("conditional_depends_on", []))
            exp_units = expected_deps(units, unit, track_units, monet)
            got_units = sorted({by_unit.get((nodes[d].get("role"), nodes[d].get("phase")))
                                for d in n.get("depends_on", []) if d in nodes} - {None})
            if exp_units != got_units:
                err("C10", f"node {nid}: depends_on sai quy tac giao tap — ky vong unit {exp_units}, "
                            f"thuc te {got_units}")

        # nhat quan trang thai — dependency KHONG TON TAI cung tinh la "chua done"
        dep_ids = n.get("depends_on", [])
        deps = [nodes[d] for d in dep_ids if d in nodes]
        all_done = len(deps) == len(dep_ids) and all(d.get("status") == "done" for d in deps)
        if n.get("status") == "ready" and not all_done:
            err("C11", f"node {nid}: status=ready nhung con depends_on chua done "
                        f"-> se dispatch som khi input chua san sang")
        if n.get("status") == "blocked" and all_done and deps:
            err("C12", f"node {nid}: moi depends_on da done nhung van blocked "
                        f"-> RECOMPUTE_READY() bi bo sot (treo im lang)")
        if n.get("status") == "blocked" and not deps:
            err("C13", f"node {nid}: khong co depends_on nhung status=blocked -> phai la ready")

        # capability-agent khong duoc active
        if role in mans and mans[role].get("core") is False and role not in active_caps:
            err("C14", f"node {nid}: agent {role!r} co core:false nhung KHONG nam trong "
                        f"project-profile.active_capability_agents {sorted(active_caps)}")

        # build track khong duoc chua po/ba/cto
        if n.get("track") == "build" and unit in ("po", "ba", "cto"):
            err("C15", f"node {nid}: unit {unit!r} khong duoc xuat hien trong track 'build' "
                        f"(thuoc track 'intake') -> se spawn lai, chay vong")

        if n.get("track") == "build" and n.get("size") and not n.get("size_reasoning"):
            err("C16", f"node {nid}: co size={n.get('size')!r} nhung thieu size_reasoning")

    # chu trinh giua node
    color = {}

    def dfs(nid, path):
        if color.get(nid) == 1:
            err("C17", f"CHU TRINH trong wbs: {' -> '.join(path + [nid])}")
            return
        if color.get(nid) == 2 or nid not in nodes:
            return
        color[nid] = 1
        for d in nodes[nid].get("depends_on", []):
            dfs(d, path + [nid])
        color[nid] = 2

    for nid in nodes:
        dfs(nid, [])

    # capacity
    running = defaultdict(int)
    for n in nodes.values():
        if n.get("status") == "running":
            running[n.get("role")] += 1
    for role, cnt in running.items():
        cap = (mans.get(role) or {}).get("concurrency")
        if cap and cnt > cap:
            err("C18", f"role {role}: {cnt} node dang running > concurrency={cap} trong manifest")

    # moi track phai co duong chay
    tracks = defaultdict(list)
    for n in nodes.values():
        tracks[n.get("track_id")].append(n)
    for tid, ns in tracks.items():
        if all(x.get("status") == "blocked" for x in ns):
            err("C19", f"track {tid}: TOAN BO node deu blocked -> track nay khong bao gio khoi dong")

    # C20-C22: trang thai cho nguoi can thiep (waiting_human / failed)
    for nid, n in nodes.items():
        st = n.get("status")
        g = n.get("gate") or {}
        if st == "waiting_human":
            if not g.get("escalated_at"):
                err("C20", f"node {nid}: status=waiting_human nhung gate.escalated_at rong "
                            f"-> khong ro da escalate that chua, nguoi co the khong he duoc thong bao")
            downstream = [m for m in nodes.values() if nid in m.get("depends_on", [])]
            if downstream:
                warn("C21", f"node {nid} dang cho nguoi va CHAN {len(downstream)} node: "
                            f"{[m['node_id'] for m in downstream]} — chay "
                            f"`python kernel/tools/resume.py {nid} --note \"...\"` de go")
        # C31-C33: trang thai CHO NGUOI QUYET DINH (khong phai loi) — doi xung voi C20/C21
        if st == AWAITING_DECISION:
            if not g.get("decision_requested_at"):
                err("C31", f"node {nid}: status={AWAITING_DECISION} nhung gate.decision_requested_at "
                            f"rong -> khong ro nguoi co that su duoc hoi chua (doi xung voi C20). "
                            f"Xem kernel/gates/gate7-design-system-lock.md")
            if g.get("escalated_at"):
                err("C33", f"node {nid}: status={AWAITING_DECISION} nhung co gate.escalated_at "
                            f"-> dang tron 2 primitive. escalated_at CHI thuoc waiting_human (loi); "
                            f"cho nguoi quyet dinh la buoc binh thuong, dung decision_requested_at.")
            downstream = [m for m in nodes.values() if nid in m.get("depends_on", [])]
            if downstream:
                warn("C32", f"node {nid} dang cho NGUOI QUYET DINH va chan {len(downstream)} node: "
                            f"{[m['node_id'] for m in downstream]} — go bang "
                            f"`python kernel/tools/resume.py {nid} --decision <id> --note \"...\"`")
        elif g.get("decision_requested_at"):
            warn("C34", f"node {nid}: co gate.decision_requested_at nhung status={st!r} "
                        f"(khong phai {AWAITING_DECISION}) -> field cu chua duoc xoa luc resume, "
                        f"co the lam nguoi doc wbs.json tuong node dang cho quyet dinh")

        max_resume = ((limits or {}).get("node") or {}).get("max_resume_before_review", 3)
        if st in TERMINAL_STUCK and len(g.get("resume_history") or []) >= max_resume:
            warn("C22", f"node {nid} da duoc cuu {len(g['resume_history'])} lan ma van treo "
                        f"-> day khong phai loi ngau nhien, ghi vao shared/lessons_learned.md "
                        f"va sua rules/skill cua role {n.get('role')!r} (lop Evolution)")

    # C28: node running qua lau = agent hang/chet ma khong tra message.
    # Day la failure mode IM LANG thu ba (canh quen processed_at va quen RECOMPUTE_READY):
    # node giu 1 slot concurrency vinh vien va khong co gi tu bao.
    stale_h = ((limits or {}).get("node") or {}).get("stale_running_hours", 6)
    now = datetime.now(timezone.utc)
    for nid, n in nodes.items():
        if n.get("status") != "running":
            continue
        sa = n.get("started_at")
        if not sa:
            err("C29", f"node {nid}: status=running nhung started_at rong "
                        f"-> khong the phat hien node treo (khong co moc thoi gian de doi chieu)")
            continue
        try:
            t0 = datetime.fromisoformat(str(sa).replace("Z", "+00:00"))
            if t0.tzinfo is None:
                t0 = t0.replace(tzinfo=timezone.utc)
        except Exception:
            err("C29", f"node {nid}: started_at={sa!r} khong parse duoc (dung ISO8601, vd 2026-07-28T09:00:00Z)")
            continue
        hours = (now - t0).total_seconds() / 3600
        if hours > stale_h:
            err("C28", f"node {nid}: running {hours:.1f} gio > nguong {stale_h} gio "
                        f"(kernel/config/limits.json node.stale_running_hours) -> agent co the da hang/chet "
                        f"ma khong tra message; no dang giu 1 slot concurrency cua role {n.get('role')!r}. "
                        f"Xu ly: chuyen node -> waiting_human + escalate. TUYET DOI khong tu spawn lai "
                        f"(neu agent that su dang chay thi se co 2 instance lam cung 1 node).")

    # C30: message_refs phai duoc dien — no la dau vet message nao da cham node nay
    for nid, n in nodes.items():
        if n.get("status") in ("done", "running") and n.get("message_refs") == [] \
                and n.get("track") != "intake":
            warn("C30", f"node {nid}: status={n.get('status')!r} nhung message_refs rong "
                        f"-> khong truy vet duoc message nao da cham node. Orchestrator phai append "
                        f"message_id vao day o PHA A (xem ORCHESTRATOR.md §7b buoc 3).")
    return nodes


# ─────────────────────────── D. mailbox ───────────────────────────
def check_mailbox(msg_schema, nodes, units, dag, mans, limits):
    files = sorted(f for f in glob.glob(rel("kernel", "mailbox", "*.md")))
    if not files:
        warn("D1", "kernel/mailbox/ khong co message nao (repo template) — bo qua kiem tra message.")
        return
    lim = (limits or {}).get("message", {})
    BODY_MAX_LINES = lim.get("body_max_lines", 120)
    BODY_MAX_CHARS = lim.get("body_max_chars", 8000)
    required = set((msg_schema or {}).get("required", []))
    seen_ids = {}
    sync = strip_meta((dag or {}).get("sync_allowed", {}))
    by_unit = {(d.get("role"), d.get("phase")): u for u, d in units.items()}

    for path in files:
        name = os.path.basename(path)
        fm, e = parse_frontmatter(path)
        if e:
            err("D2", f"mailbox/{name}: {e}")
            continue
        missing = required - {k for k in fm if not k.startswith("__")}
        if missing:
            err("D3", f"mailbox/{name}: thieu field bat buoc {sorted(missing)}")

        # D14/D15: gioi han kich thuoc body — chong lam no context cua agent nhan
        bl, bc = fm.get("__body_lines__", 0), fm.get("__body_chars__", 0)
        if bl > BODY_MAX_LINES or bc > BODY_MAX_CHARS:
            err("D14", f"mailbox/{name}: body {bl} dong / {bc} ky tu, vuot gioi han "
                       f"{BODY_MAX_LINES} dong / {BODY_MAX_CHARS} ky tu -> se lam no "
                       f"max_context_tokens cua agent nhan ma Gate 0 khong chan duoc. "
                       f"Chuyen log dai ra file va tro qua artifact_refs, body chi giu doan quyet dinh.")

        # D15: artifact_refs phai tro tro file ton tai that
        for ref in str(fm.get("artifact_refs") or "").strip("[]").split(","):
            ref = ref.strip().strip("'\"")
            if ref and not os.path.exists(rel(*ref.split("/"))):
                err("D15", f"mailbox/{name}: artifact_refs -> {ref!r} khong ton tai "
                           f"-> bang chung Gate doi chieu vao file khong co")
        t = fm.get("type")
        if t not in MSG_TYPES:
            err("D4", f"mailbox/{name}: type={t!r} khong thuoc {sorted(MSG_TYPES)}")
        if t == "request" and not all(k in fm for k in ("request_id", "turn", "max_turns")):
            err("D5", f"mailbox/{name}: type=request phai co request_id + turn + max_turns")
        if t == "response" and not all(k in fm for k in ("request_id", "turn")):
            err("D6", f"mailbox/{name}: type=response phai co request_id + turn")
        if isinstance(fm.get("turn"), int) and isinstance(fm.get("max_turns"), int) \
                and fm["turn"] > fm["max_turns"]:
            err("D7", f"mailbox/{name}: turn={fm['turn']} > max_turns={fm['max_turns']} "
                       f"-> phai escalate, khong duoc dispatch")

        # D16/D17: cap phat message_id — phai duy nhat VA suy ra tu node_id
        mid = fm.get("message_id")
        nid = fm.get("node_id")
        if mid:
            if mid in seen_ids:
                err("D16", f"mailbox/{name}: message_id={mid!r} TRUNG voi {seen_ids[mid]} "
                           f"-> message_id la dinh danh duy nhat (va la ten file), trung = mat message")
            seen_ids[mid] = name
            if nid and not mid.startswith(f"msg-{nid}-"):
                err("D17", f"mailbox/{name}: message_id={mid!r} khong theo quy uoc "
                           f"'msg-<node_id>-<n>' (phai bat dau 'msg-{nid}-'). Quy uoc nay lam "
                           f"message_id duy nhat TU DONG: 1 node chi co 1 agent instance ghi, "
                           f"nen danh so trong pham vi node la khong the trung. Danh so tu do "
                           f"(msg-0031) thi 2 agent song song se chon cung so.")

        node = nodes.get(nid) if nodes else None
        if nodes and nid not in nodes:
            err("D8", f"mailbox/{name}: node_id={nid!r} khong ton tai trong wbs.json -> message vo dia chi")
        elif node:
            if fm.get("from") != node.get("role"):
                err("D9", f"mailbox/{name}: from={fm.get('from')!r} khac role cua node "
                           f"({node.get('role')!r}) -> mao danh node cua agent khac")
            unit = by_unit.get((node.get("role"), node.get("phase")))
            to = fm.get("to")
            if t == "handoff" and unit:
                ok = {units[f].get("role") for f in units[unit].get("feeds", []) if f in units}
                ok |= {units[f].get("role") for f in units[unit].get("runtime_feeds", []) if f in units}
                if to not in ok:
                    err("D10", f"mailbox/{name}: handoff to={to!r} khong nam trong feeds/runtime_feeds "
                                f"cua unit {unit} ({sorted(ok)})")
            if t in ("request", "response"):
                allowed = sync.get(fm.get("from"), [])
                if to not in allowed:
                    err("D11", f"mailbox/{name}: sync to={to!r} khong nam trong "
                                f"sync_allowed[{fm.get('from')}]={allowed}")

            # LECH BOOKKEEPING — day la loi runtime LLM de mac nhat
            if fm.get("processed_at") is None and node.get("status") == "done" and t == "handoff":
                err("D12", f"mailbox/{name}: processed_at=null nhung node {nid} da done "
                            f"-> se bi tieu thu LAI moi vong (loop vo han)")
            if fm.get("processed_at") is not None and t == "handoff" \
                    and node.get("status") not in ("done", "failed", "ready", AWAITING_DECISION):
                warn("D13", f"mailbox/{name}: da processed_at nhung node {nid} van "
                            f"{node.get('status')!r} — kiem tra lai buoc cap nhat trang thai")


# ─────────────────────────── E. tham chieu cheo ───────────────────────────
def check_crossrefs(mans, profile):
    agents = {a for a in mans if a != "_template"}
    shared_skills = set(os.listdir(rel("skills"))) if os.path.isdir(rel("skills")) else set()

    for d in glob.glob(rel("**", "skills", "*"), recursive=True):
        if os.path.isdir(d) and not os.path.exists(os.path.join(d, "SKILL.md")):
            err("E1", f"{os.path.relpath(d, ROOT)}: thu muc skill khong co SKILL.md -> vo hinh voi moi agent")

    for a in sorted(agents):
        ap = rel("agents", a, "AGENT.md")
        if not os.path.exists(ap):
            err("E2", f"agents/{a}/ thieu AGENT.md")
            continue
        txt = open(ap, encoding="utf-8").read()
        sd = rel("agents", a, "skills")
        if os.path.isdir(sd):
            for s in os.listdir(sd):
                if s not in txt:
                    err("E3", f"agents/{a}: skill {s!r} co tren dia nhung AGENT.md khong cho phep goi")
        if not os.path.exists(rel("agents", a, "manifest.json")):
            err("E4", f"agents/{a}/ thieu manifest.json")

    # capability-agent trong project-profile phai co core:false
    for a in (profile or {}).get("active_capability_agents", []):
        if a not in agents:
            err("E5", f"project-profile.active_capability_agents chua {a!r} — khong phai agent")
        elif mans[a].get("core") is not False:
            err("E6", f"project-profile kich hoat {a!r} nhung manifest cua no core={mans[a].get('core')!r} "
                       f"(chi capability-agent core:false moi duoc liet ke)")

    # tham chieu da bi go bo
    dead = {
        "process-table.json": "da bo (moi field derived tu wbs.json)",
        "applies_to_project_types": "da bo (repo don loai project)",
        "agents/dev-fe": "da bo (gop vao agents/mobile 2 phase)",
    }
    for f in glob.glob(rel("**", "*.md"), recursive=True) + glob.glob(rel("**", "*.json"), recursive=True):
        if os.sep + "tools" + os.sep in f:
            continue
        txt = open(f, encoding="utf-8").read()
        for pat, why in dead.items():
            if pat in txt and not any(k in txt for k in ("da bi bo", "đã bị bỏ", "đã bỏ", "KHONG khai", "không còn")):
                warn("E7", f"{os.path.relpath(f, ROOT)}: con nhac {pat!r} ({why}) — kiem tra xem la "
                            f"ghi chu lich su hay tham chieu that")

    # anchor-tag role phai la agent that
    import re as _re
    for f in glob.glob(rel("shared", "**", "*.md"), recursive=True):
        txt = open(f, encoding="utf-8").read()
        for m in _re.finditer(r"<!--\s*tier:2\s+role:([a-z0-9,\-]+)", txt):
            for r in m.group(1).split(","):
                if r and r not in agents:
                    err("E8", f"{os.path.relpath(f, ROOT)}: anchor-tag role {r!r} khong phai agent "
                               f"-> context_compile se khong bao gio trich duoc cho role nay")


# ─────────────────────────── H. Tien de Gate 1 cho nhanh Design (E9-E12) ───────────────────────────
_PROJ_ANCHOR_RE = re.compile(r"<!--\s*tier:2\s+role:([a-z0-9,\-]+)\s+story:([A-Za-z0-9\-]+)\s*-->")


def check_design_prereqs():
    """Cuong che 2 dieu kien MOI trong kernel/gates/gate1-ba-cto-signoff.md (them cung dot voi
    nhanh Design/domain — xem shared/lessons_learned.md).

    Truoc day node scope=project (design-system, mobile-shell...) nhan Tier2 RONG ma khong ai
    bao (guard trong context_compile.py chi ap dung cho node co story_id that). Da vsua guard
    do, nhung sua o dispatch-time la QUA MUON — story dau tien da mat 1 vong design-system chay
    roi moi lo. Kiem o day (luc Gate 1, truoc generate_wbs) la re hon nhieu: BA/CTO thay ngay
    thieu gi ma chua tao node nao ca.
    """
    prd = rel("shared", "PRD.md")
    if not os.path.exists(prd):
        return
    txt = open(prd, encoding="utf-8").read()
    stories, has_proj_designer = set(), False
    for m in _PROJ_ANCHOR_RE.finditer(txt):
        roles, story = m.group(1).split(","), m.group(2)
        if story == "PROJ":
            has_proj_designer = has_proj_designer or "designer" in roles
            continue
        if story == "US-000":
            continue  # vi du mau trong template, khong phai story that
        stories.add(story)

    if not has_proj_designer:
        err("E9", "shared/PRD.md: chua co khoi anchor 'story:PROJ' voi role 'designer' -> "
                   "design-system se nhan Tier 2 rong va TU BIA design intent (doi tuong nguoi "
                   "dung/tong mau/app tham chieu neu clone). BA phai viet TRUOC khi Gate 1 pass "
                   "lan dau (agents/ba/AGENT.md muc B). context_compile.py se chan dispatch neu "
                   "thieu, nhung bat o day re hon nhieu (truoc khi co node nao duoc tao).")

    if not stories:
        return  # chua co story that -> khong con gi de doi chieu voi domain-map.json

    dm_path = rel("shared", "contracts", "domain-map.json")
    dm_stories = None
    if os.path.exists(dm_path):
        try:
            dm = json.load(open(dm_path, encoding="utf-8"))
            dm_stories = {s.get("story_id") for s in dm.get("stories", [])
                          if isinstance(s, dict) and s.get("story_id")
                          and s.get("story_id") != "US-000"}
        except Exception as e:
            err("E11", f"shared/contracts/domain-map.json: JSON khong parse duoc — {e}")
    else:
        err("E11", "shared/contracts/domain-map.json: khong ton tai -> "
                    "agents/ba/skills/classify_domain/ chua chay lan nao")

    if dm_stories is not None:
        missing = stories - dm_stories
        if missing:
            err("E10", f"story {sorted(missing)} co trong shared/PRD.md nhung KHONG co entry "
                        f"trong shared/contracts/domain-map.json -> designer-screen cua story do "
                        f"se khong biet nap domain skill nao, se tu doan thay vi dung tri thuc "
                        f"domain that. Chay agents/ba/skills/classify_domain/ (xem SKILL.md) "
                        f"truoc khi Gate 1 pass.")

    ts_path = rel("shared", "contracts", "tech-stack.json")
    if not os.path.exists(ts_path):
        err("E12", "shared/contracts/tech-stack.json: khong ton tai -> design-system se khong "
                    "biet khoanh vung tim thu vien UI theo platform nao khi chay skill "
                    "component_discovery. cto phai ghi file nay TRUOC khi Gate 1 pass "
                    "(agents/cto/AGENT.md muc Output hop le).")
    else:
        try:
            ts = json.load(open(ts_path, encoding="utf-8"))
            proj = next((e for e in ts.get("entries", [])
                         if isinstance(e, dict) and e.get("story_id") == "PROJ"), None)
            if proj is None:
                err("E12", "shared/contracts/tech-stack.json: khong co entry story_id='PROJ' -> "
                            "design-system se nhan Tier 2 rong cho tech stack.")
            elif not (proj.get("platform") and proj.get("ui_framework") and proj.get("language")):
                err("E12", "shared/contracts/tech-stack.json: entry 'PROJ' thieu platform/"
                            "ui_framework/language -> khong du de khoanh vung tim thu vien UI.")
        except Exception as e:
            err("E12", f"shared/contracts/tech-stack.json: JSON khong parse duoc — {e}")


# ─────────── I. Screen layout: tung component kiem rieng (E13-E22) ───────────
# Cuong che kernel/contracts/screen-layout.schema.json o phan JSON Schema KHONG bieu dien duoc:
# rang buoc LIEN entry (ref co ton tai that khong, parent co tao vong khong) va static design
# metrics (dung 1 primary moi state, so co chu / so mau / nhip spacing).
#
# VI SAO O DAY: truoc day Gate 5 chi kiem DEM o muc man hinh + tinh hop le cua token ref.
# Khong co gi kiem tung COMPONENT ben trong -> do la cho sinh "bug vat": field null khong ai
# xu ly, nut bam dan toi state khong ton tai, input khong validation, text dai lam vo bo cuc.
# Ca 2 lop loi nay (logic + hien thi) lo ra o Gate 4 (QA) hoac o nguoi dung that, trong khi
# chung kiem duoc ngay o tang du lieu — TRUOC khi mobile-screen sinh 1 dong code nao.
#
# NHOM E22 (kich thuoc man hinh) them sau, cung ly do nhung o muc KHOI thay vi muc text:
# truoc do ca hop dong khong co 1 field nao ve be rong/huong/co chu — lever duy nhat la
# string tu do `group` — nen "vo o may 320dp", "cat chu o co chu 200%", "ban phim che nut
# Gui", "bar dinh nam duoi gesture bar" la lop loi DUY NHAT trong nhom hien thi ma khong ma
# nao bat duoc. Bac/huong bat buoc doc tu tokens.json -> responsive_contract (quyet dinh cua
# PROJECT theo system-spec.md), tran co dinh doc tu limits.json -> responsive.
#
# NGUYEN TAC do luong: metric duoc SUY RA tu style that cua tung component, KHONG tin
# design_metrics_declared. Field declared chi dung de doi chieu: khai lech voi thuc te nghia la
# agent bao "da do" ma khong do -> dung lop loi ma Gate 7 dieu 3 da chan cho contrast.

_CONTROL_TYPES = {"button", "icon_button", "input", "select", "toggle", "slider",
                  "checkbox", "radio", "search_field"}
_INPUT_TYPES = {"input", "select", "search_field"}
_TEXT_TYPES = {"text", "badge"}
_OVERLAY_TYPES = {"sheet", "dialog", "snackbar", "tooltip", "menu"}
_ACTION_NEEDS_TARGET = {"navigate", "submit", "retry"}

# Nhom E22 (kich thuoc man hinh). Khoi CHUA + type nhay kich thuoc PHAI khai `responsive`:
# do la 2 loai component quyet dinh bo cuc co vo hay khong khi be rong doi.
_CONTAINER_TYPES = {"section", "card", "list", "grid", "row", "column"}
_SIZE_SENSITIVE_TYPES = {"image", "chart", "media_player"}
_HORIZONTAL_AXES = {"horizontal", "grid"}
_TIER_ORDER = ["compact_small", "compact", "medium", "expanded"]


def _responsive_contract():
    """responsive_contract trong tokens.json, hoac None neu chua co / chua khoa.

    Tra None thi cac check phu thuoc quyet dinh CUA PROJECT (bac nao bat buoc, huong nao
    bat buoc) bi bo qua — dung cach ham check_screen_layouts da xu ly repo template o I1.
    Cac check KHONG phu thuoc project (wrap_behavior, degrade_order, min_height_dp quanh
    text, pinned + safe_area) van chay binh thuong.
    """
    p = rel("shared", "design", "tokens.json")
    if not os.path.exists(p):
        return None
    try:
        rc = json.load(open(p, encoding="utf-8")).get("responsive_contract")
    except Exception:
        return None  # loi parse tokens.json da duoc bao o cho khac
    return rc if isinstance(rc, dict) else None


def _children_map(comps):
    """parent_id -> [component_id con], theo dung thu tu xuat hien."""
    kids = {}
    for c in comps:
        if isinstance(c, dict) and c.get("component_id"):
            kids.setdefault(c.get("parent"), []).append(c["component_id"])
    return kids


def _holds_text(cid, comps_by_id, kids):
    """Khoi nay co chua component type text/badge (truc tiep hoac qua con) khong.

    Dung de chan `min_height_dp` khac null quanh text: khoa chieu cao quanh text = chu bi
    cat ngay khi nguoi dung bat co chu he thong 200%. Duyet co gioi han depth de an toan
    voi vong parent (vong da duoc bao rieng o E15).
    """
    stack, seen = list(kids.get(cid, [])), set()
    while stack:
        k = stack.pop()
        if k in seen:
            continue
        seen.add(k)
        if (comps_by_id.get(k) or {}).get("type") in _TEXT_TYPES:
            return True
        stack.extend(kids.get(k, []))
    return False


def _registry_categories():
    """Tap category da khai trong component-registry (core + per-story). Rong neu chua co file."""
    cats = set()
    core = rel("shared", "design", "component-registry.core.json")
    if os.path.exists(core):
        try:
            for e in (json.load(open(core, encoding="utf-8")).get("core_components") or []):
                if isinstance(e, dict) and e.get("category"):
                    cats.add(e["category"])
        except Exception:
            pass  # loi parse registry da duoc bao o cho khac, khong bao trung
    d = rel("shared", "design", "component-registry")
    if os.path.isdir(d):
        for f in glob.glob(os.path.join(d, "*.json")):
            try:
                data = json.load(open(f, encoding="utf-8"))
                entries = data if isinstance(data, list) else (data.get("components") or [])
                for e in entries:
                    if isinstance(e, dict) and e.get("category"):
                        cats.add(e["category"])
            except Exception:
                pass
    return cats


def _parent_cycle(comps):
    """Tra component_id dau tien nam trong 1 vong parent, hoac None."""
    parent = {c["component_id"]: c.get("parent") for c in comps if c.get("component_id")}
    for start in parent:
        seen, cur = set(), start
        while cur is not None:
            if cur in seen:
                return start
            seen.add(cur)
            cur = parent.get(cur)
            if cur is not None and cur not in parent:
                break  # parent tro ra ngoai -> da bao o E14, khong tinh la vong
    return None


def check_screen_layouts(limits):
    d = rel("shared", "design", "screens")
    files = sorted(glob.glob(os.path.join(d, "*.json"))) if os.path.isdir(d) else []
    if not files:
        warn("I1", "shared/design/screens/ khong co layout nao — binh thuong voi repo template "
                   "(designer-screen chua chay). Kiem tra tung component se bo qua.")
        return

    dl = ((limits or {}).get("design") or {})
    max_type = dl.get("max_distinct_type_sizes_per_screen", 6)
    max_color = dl.get("max_distinct_colors_per_screen", 8)
    max_root = dl.get("max_root_level_components", 9)
    max_span = dl.get("max_spacing_scale_span", 4)
    scale_order = dl.get("spacing_scale_order") or ["xs", "sm", "md", "lg", "xl", "xxl"]
    max_primary = dl.get("max_primary_emphasis_per_state", 1)
    rl = ((limits or {}).get("responsive") or {})
    max_kids_no_degrade = rl.get("max_children_without_degrade_order", 3)
    max_cols_compact = rl.get("max_columns_compact", 2)
    max_pinned = rl.get("max_pinned_regions_per_state", 2)
    need_font_scale = rl.get("required_font_scale", 2.0)
    contract = _responsive_contract()
    req_tiers = list((contract or {}).get("required_tiers") or [])
    req_orients = list((contract or {}).get("target_orientations") or [])
    known_tiers = set(((contract or {}).get("breakpoints_dp") or {}).keys()) or set(_TIER_ORDER)
    registry_cats = _registry_categories()

    for path in files:
        name = os.path.basename(path)
        try:
            layout = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            err("E13", f"shared/design/screens/{name}: JSON khong parse duoc — {e}")
            continue
        if not isinstance(layout, dict):
            err("E13", f"shared/design/screens/{name}: goc phai la object")
            continue

        # Key la o goc: schema co additionalProperties:false nen key ngoai danh sach nay la VI PHAM
        # HOP DONG. Kiem o day vi validator khong chay JSON Schema — thieu no thi 1 file ghi
        # 'data_bindings' phang o goc (cach viet CU, truoc khi binding chuyen vao tung component)
        # se lot im lang: vua sai schema vua khong ai bao.
        allowed_root = {"schema_version", "screen_id", "states", "components", "ad_slots",
                        "design_metrics_declared", "responsive_declared"}
        unknown = {k for k in layout if not k.startswith("_")} - allowed_root
        if unknown:
            err("E13", f"shared/design/screens/{name}: key la o goc {sorted(unknown)} — schema "
                       f"khong cho phep (additionalProperties:false). Binding nam TRONG tung "
                       f"component (components[].binds[]), khong phai mang 'data_bindings' phang.")

        expect_id = os.path.splitext(name)[0]
        if layout.get("screen_id") != expect_id:
            err("E13", f"shared/design/screens/{name}: screen_id={layout.get('screen_id')!r} khong "
                       f"khop ten file (phai la {expect_id!r}) -> mobile-screen se lay sai story")

        states = layout.get("states")
        comps = layout.get("components")
        if not isinstance(states, list) or not states:
            err("E13", f"shared/design/screens/{name}: thieu mang 'states' khong rong")
            continue
        if not isinstance(comps, list) or not comps:
            err("E13", f"shared/design/screens/{name}: thieu mang 'components' khong rong")
            continue

        state_ids, dup_states = set(), set()
        for s in states:
            if not isinstance(s, dict) or not s.get("state_id"):
                err("E13", f"shared/design/screens/{name}: co entry states thieu state_id")
                continue
            if s["state_id"] in state_ids:
                dup_states.add(s["state_id"])
            state_ids.add(s["state_id"])
        if dup_states:
            err("E13", f"shared/design/screens/{name}: state_id trung {sorted(dup_states)}")

        comp_ids, dup_comps = set(), set()
        for c in comps:
            if not isinstance(c, dict) or not c.get("component_id"):
                err("E13", f"shared/design/screens/{name}: co entry components thieu component_id")
                continue
            if c["component_id"] in comp_ids:
                dup_comps.add(c["component_id"])
            comp_ids.add(c["component_id"])
        if dup_comps:
            err("E13", f"shared/design/screens/{name}: component_id trung {sorted(dup_comps)} "
                       f"-> parent/target tro tinh khong xac dinh")

        # state loi phai co duong ra (JSON Schema da co, kiem lai vi validator khong chay schema)
        for s in states:
            if not isinstance(s, dict):
                continue
            kind = s.get("kind")
            if kind and kind != "success" and not s.get("entered_when"):
                err("E16", f"shared/design/screens/{name}: state {s.get('state_id')!r} kind={kind} "
                           f"thieu 'entered_when' -> dev phai tu doan khi nao state nay xay ra")
            if kind in ("error", "offline", "permission_denied", "session_expired") \
                    and not s.get("recovery_action"):
                err("E16", f"shared/design/screens/{name}: state {s.get('state_id')!r} kind={kind} "
                           f"thieu 'recovery_action' -> state loi khong co duong ra la bug UX")

        type_keys, color_keys, spacing_keys = set(), set(), set()
        primary_per_state = {sid: 0 for sid in state_ids}
        root_count = 0
        comps_by_id = {c["component_id"]: c for c in comps
                       if isinstance(c, dict) and c.get("component_id")}
        kids = _children_map(comps)
        pinned_per_state = {sid: 0 for sid in state_ids}
        has_input = any(isinstance(c, dict) and c.get("type") in _INPUT_TYPES for c in comps)

        for c in comps:
            if not isinstance(c, dict):
                continue
            cid = c.get("component_id", "?")
            ctype = c.get("type")
            where = f"shared/design/screens/{name}: component {cid!r}"

            # --- tham chieu lien entry (lop loi LOGIC) ---
            ais = c.get("appears_in_states")
            if not isinstance(ais, list) or not ais:
                err("E14", f"{where} thieu 'appears_in_states' -> khong state nao render no "
                           f"(component chet)")
            else:
                for sid in ais:
                    if sid not in state_ids:
                        err("E14", f"{where} appears_in_states tro toi state {sid!r} KHONG ton tai")
                    elif c.get("emphasis") == "primary":
                        primary_per_state[sid] = primary_per_state.get(sid, 0) + 1

            if c.get("parent") is None:
                root_count += 1
            elif c["parent"] not in comp_ids:
                err("E14", f"{where} parent={c['parent']!r} KHONG ton tai")
            elif c["parent"] == cid:
                err("E15", f"{where} co parent tro vao chinh no")

            rref = c.get("registry_ref")
            if rref and registry_cats and rref not in registry_cats:
                err("E14", f"{where} registry_ref={rref!r} khong co trong component-registry "
                           f"-> mobile-screen se cai 1 dependency khong ai chon")

            it = c.get("interaction")
            if ctype in _CONTROL_TYPES and not isinstance(it, dict):
                err("E16", f"{where} type={ctype} nhung thieu 'interaction' -> khong biet bam vao "
                           f"thi xay ra gi")
            if isinstance(it, dict):
                act = it.get("action")
                if act in _ACTION_NEEDS_TARGET and not (it.get("target_state") or it.get("target_screen")):
                    err("E16", f"{where} action={act!r} nhung khong co target_state/target_screen "
                               f"-> hanh dong tro vao hu khong")
                ts = it.get("target_state")
                if ts and ts not in state_ids:
                    err("E14", f"{where} target_state={ts!r} KHONG ton tai trong states")
                if ctype in _INPUT_TYPES:
                    vals = it.get("validation")
                    if not isinstance(vals, list) or not vals:
                        err("E16", f"{where} type={ctype} nhung khong co 'validation' -> input rac "
                                   f"di thang xuong backend")
                    else:
                        for v in vals:
                            es = v.get("error_state") if isinstance(v, dict) else None
                            if es and es not in state_ids:
                                err("E14", f"{where} validation.error_state={es!r} KHONG ton tai")
                if "disabled_when" not in it:
                    err("E16", f"{where} thieu 'disabled_when' (dat null neu LUON bam duoc) "
                               f"-> khong khai tuong minh la nguon loi 'bam duoc luc khong nen bam'")

            # --- lop loi HIEN THI ---
            for b in (c.get("binds") or []):
                if not isinstance(b, dict):
                    continue
                if not b.get("on_null"):
                    err("E17", f"{where} bind field={b.get('field')!r} thieu 'on_null' -> field rong "
                               f"se ra o trang / chu 'null' truoc mat nguoi dung")
                if b.get("on_null") == "fallback_text" and not b.get("fallback_text"):
                    err("E17", f"{where} bind field={b.get('field')!r} on_null=fallback_text nhung "
                               f"khong co noi dung fallback_text")

            if ctype in _TEXT_TYPES and not isinstance(c.get("text_overflow"), dict):
                err("E17", f"{where} type={ctype} thieu 'text_overflow' -> noi dung dai se lam vo "
                           f"bo cuc, mock data ten ngan khong bao gio phat hien ra")

            # --- lop loi KICH THUOC MAN HINH (E22) ---
            # Cung vai tro text_overflow dong cho text, nhung o muc KHOI: mock data tren may
            # 393dp khong bao gio lo ra 'row nay tran ngang o 320dp' hay 'khoi nay cat chu o
            # co chu 200%'. Do la lop loi duy nhat trong nhom hien thi ma truoc day khong ma
            # nao bat duoc, du no kiem duoc hoan toan o tang du lieu.
            resp = c.get("responsive")
            n_kids = len(kids.get(cid, []))
            if ctype in _CONTAINER_TYPES or ctype in _SIZE_SENSITIVE_TYPES or n_kids:
                if not isinstance(resp, dict):
                    err("E22", f"{where} type={ctype} ({n_kids} con) thieu 'responsive' -> khong "
                               f"biet be rong doi thi khoi nay wrap/co/bo cai gi, layout se vo o "
                               f"may hep hoac o co chu he thong 200%")
                    resp = None
            if isinstance(resp, dict):
                axis = resp.get("axis")
                wrap = resp.get("wrap_behavior")
                cols = resp.get("columns")

                if axis in _HORIZONTAL_AXES and n_kids > 1 and wrap == "none":
                    err("E22", f"{where} axis={axis} co {n_kids} con nhung wrap_behavior='none' "
                               f"-> khang dinh khong bao gio het cho, thuc te tran ngang o "
                               f"{rl.get('min_supported_width_dp', 320)}dp. Chon wrap / "
                               f"scroll_horizontal / stack_vertical / shrink")

                if axis in _HORIZONTAL_AXES and not isinstance(cols, dict):
                    err("E22", f"{where} axis={axis} nhung khong khai 'columns' theo bac -> "
                               f"mobile-screen tu doan so cot, moi story doan mot kieu")
                elif isinstance(cols, dict):
                    bad_tier = {k for k in cols if not k.startswith("_")} - known_tiers
                    if bad_tier:
                        err("E22", f"{where} columns co bac la {sorted(bad_tier)} -> khong ton tai "
                                   f"trong tokens.json -> responsive_contract.breakpoints_dp")
                    for t in req_tiers:
                        if cols.get(t) is None:
                            err("E22", f"{where} columns thieu bac bat buoc {t!r} (theo "
                                       f"responsive_contract.required_tiers) -> bac nay khong ai "
                                       f"quyet dinh so cot")
                    seq = [(t, cols.get(t)) for t in _TIER_ORDER
                           if isinstance(cols.get(t), int)]
                    for (t1, v1), (t2, v2) in zip(seq, seq[1:]):
                        if v2 < v1:
                            err("E22", f"{where} columns {t1}={v1} nhung {t2}={v2} -> man RONG hon "
                                       f"lai IT cot hon, khong don dieu; gan nhu chac chan khai "
                                       f"nguoc bac")
                    for t in ("compact_small", "compact"):
                        v = cols.get(t)
                        if isinstance(v, int) and v > max_cols_compact:
                            err("E22", f"{where} columns.{t}={v} vuot tran {max_cols_compact} cho "
                                       f"bac < 600dp -> moi cot con qua hep de chua noi dung that")

                degrade = resp.get("degrade_order") or []
                if not isinstance(degrade, list):
                    err("E22", f"{where} 'degrade_order' phai la mang component_id")
                else:
                    for did in degrade:
                        if did not in comp_ids:
                            err("E22", f"{where} degrade_order tro toi {did!r} KHONG ton tai")
                        elif (comps_by_id.get(did) or {}).get("parent") != cid:
                            err("E22", f"{where} degrade_order tro toi {did!r} nhung do khong phai "
                                       f"CON cua khoi nay -> khong the bo mot thu khoi khac so huu")
                    if n_kids > max_kids_no_degrade and not degrade:
                        err("E22", f"{where} co {n_kids} con (tran {max_kids_no_degrade}) nhung "
                                   f"'degrade_order' rong -> khi het cho mobile-screen tu chon cai "
                                   f"gi bi cat, va no se cat DU LIEU truoc khi cat NHAN")

                if resp.get("sizing") == "aspect_ratio" and not resp.get("aspect_ratio"):
                    err("E22", f"{where} sizing=aspect_ratio nhung thieu 'aspect_ratio' -> anh/"
                               f"video bi bop meo hoac bi bake letterbox vao khung noi dung")

                if resp.get("min_height_dp") is not None and (
                        ctype in _TEXT_TYPES or _holds_text(cid, comps_by_id, kids)):
                    err("E22", f"{where} min_height_dp={resp['min_height_dp']} nhung khoi nay chua "
                               f"text/badge -> khoa chieu cao quanh text la cat chu ngay khi nguoi "
                               f"dung bat co chu he thong {need_font_scale}x (dat null)")

                if resp.get("pinned") is True:
                    if resp.get("safe_area") in (None, "none"):
                        err("E22", f"{where} pinned=true nhung safe_area='none' -> bar dinh bien "
                                   f"nam duoi notch/gesture bar, nguoi dung bam khong trung")
                    for sid in (ais if isinstance(ais, list) else []):
                        if sid in pinned_per_state:
                            pinned_per_state[sid] += 1

            a11y = c.get("a11y")
            if ctype in _CONTROL_TYPES:
                if not isinstance(a11y, dict) or a11y.get("min_tap_target_ok") is not True:
                    err("E16", f"{where} type={ctype} thieu a11y.min_tap_target_ok=true "
                               f"(nguong o tokens.json -> a11y_contract)")
            if ctype == "icon_button" and not (isinstance(a11y, dict) and a11y.get("label")):
                err("E16", f"{where} icon_button khong co a11y.label -> o trong voi screen reader")

            if c.get("order") is None and ctype not in _OVERLAY_TYPES:
                err("E16", f"{where} thieu 'order' (chi overlay duoc phep null) -> thu tu doc "
                           f"khong xac dinh, moi lan sinh code co the ra 1 thu tu khac")

            # --- token ref + thu thap metric tu style THAT ---
            style = c.get("style") or {}
            if not isinstance(style, dict):
                err("E18", f"{where} 'style' phai la object")
                continue
            for k, v in style.items():
                if not isinstance(v, str) or not v.startswith("token:"):
                    err("E18", f"{where} style.{k} = {v!r} khong phai tham chieu 'token:<nhom>.<key>' "
                               f"-> hard-code, Gate 5 dieu 5")
                    continue
                ref = v[len("token:"):]
                if ref.startswith("typography."):
                    type_keys.add(ref)
                elif ref.startswith("color."):
                    color_keys.add(ref)
                elif ref.startswith("spacing."):
                    spacing_keys.add(ref.split(".", 1)[1])

        # Nguong la TRAN (<=), khong phai dang thuc: 0 primary hop le voi man danh sach/so sanh
        # (nang 1 card len la pha chuc nang so sanh — xem limits.json _primary_why_not_exactly_one).
        for sid, n in primary_per_state.items():
            if n > max_primary:
                err("E19", f"shared/design/screens/{name}: state {sid!r} co {n} component "
                           f"emphasis=primary (toi da {max_primary}) -> nhieu CTA tranh tieu diem, "
                           f"nguoi dung khong biet nen bam cai nao")

        if len(type_keys) > max_type:
            err("E20", f"shared/design/screens/{name}: dung {len(type_keys)} co chu khac nhau "
                       f"(nguong {max_type}) -> nhieu typographic: {sorted(type_keys)}")
        if len(color_keys) > max_color:
            err("E20", f"shared/design/screens/{name}: dung {len(color_keys)} token mau khac nhau "
                       f"(nguong {max_color}) -> bang mau khong nhat quan: {sorted(color_keys)}")
        if root_count > max_root:
            err("E20", f"shared/design/screens/{name}: {root_count} component o goc (parent=null, "
                       f"nguong {max_root}) -> man hinh khong co cau truc phan cap")

        idx = [scale_order.index(k) for k in spacing_keys if k in scale_order]
        if idx and (max(idx) - min(idx)) > max_span:
            err("E20", f"shared/design/screens/{name}: spacing dung {sorted(spacing_keys)} trai "
                       f"{max(idx) - min(idx)} bac tren scale (nguong {max_span}) -> mat nhip")

        # --- E22 o muc MAN HINH: da nghi cho nhung bac/huong/co chu nao ---
        # Cung nguyen tac design_metrics_declared: khai bang SO de doi chieu duoc, khong phai
        # cau "da responsive". Bac/huong bat buoc la quyet dinh CUA PROJECT (system-spec.md ->
        # design-system -> responsive_contract), khong phai hang so trong validator.
        for sid, n in pinned_per_state.items():
            if n > max_pinned:
                err("E22", f"shared/design/screens/{name}: state {sid!r} co {n} vung pinned (tran "
                           f"{max_pinned}) -> phan noi dung cuon duoc con lai qua nho, o landscape "
                           f"thi gan nhu khong con gi")

        rd = layout.get("responsive_declared")
        if not isinstance(rd, dict):
            err("E22", f"shared/design/screens/{name}: thieu 'responsive_declared' -> khong biet "
                       f"layout nay da duoc nghi cho bac kich thuoc / huong / co chu nao")
        else:
            tiers = rd.get("tiers_covered") or []
            bad_tier = set(tiers) - known_tiers
            if bad_tier:
                err("E22", f"shared/design/screens/{name}: responsive_declared.tiers_covered co bac "
                           f"la {sorted(bad_tier)} -> khong ton tai trong responsive_contract."
                           f"breakpoints_dp")
            missing = [t for t in req_tiers if t not in tiers]
            if missing:
                err("E22", f"shared/design/screens/{name}: tiers_covered thieu bac bat buoc "
                           f"{missing} (responsive_contract.required_tiers) -> man hinh nay chua "
                           f"duoc nghi cho kich thuoc ma project cam ket ho tro")
            missing_o = [o for o in req_orients if o not in (rd.get("orientations") or [])]
            if missing_o:
                err("E22", f"shared/design/screens/{name}: orientations thieu {missing_o} "
                           f"(responsive_contract.target_orientations)")
            fs = rd.get("font_scale_verified")
            if not isinstance(fs, (int, float)) or fs < need_font_scale:
                err("E22", f"shared/design/screens/{name}: font_scale_verified={fs!r} < nguong "
                           f"{need_font_scale} -> co chu he thong 200% la muc nguoi dung dat duoc "
                           f"that, khong phai truong hop bien")
            if rd.get("keyboard_avoidance") == "not_applicable" and has_input:
                err("E22", f"shared/design/screens/{name}: keyboard_avoidance='not_applicable' "
                           f"nhung man co input/select/search_field -> ban phim se che dung cai nut "
                           f"Gui va khong test nao bat duoc")

        decl = layout.get("design_metrics_declared")
        if isinstance(decl, dict):
            for field, actual in (("distinct_type_sizes", len(type_keys)),
                                  ("distinct_colors", len(color_keys)),
                                  ("root_level_component_count", root_count)):
                if decl.get(field) is not None and decl[field] != actual:
                    err("E20", f"shared/design/screens/{name}: design_metrics_declared.{field}="
                               f"{decl[field]} nhung thuc te dem duoc {actual} -> agent bao 'da do' "
                               f"ma khong do that")

        for a in (layout.get("ad_slots") or []):
            if not isinstance(a, dict):
                continue
            bad = [s.get("state_id") for s in states
                   if isinstance(s, dict) and s.get("kind") in ("error", "loading")
                   and s.get("state_id") in (a.get("appears_in_states") or [])]
            if bad:
                err("E21", f"shared/design/screens/{name}: ad_slot {a.get('slot_id')!r} hien o state "
                           f"{bad} (kind error/loading) -> chen quang cao len man loi/dang tai")
            if a.get("region") == "inline" and not a.get("after_component_id"):
                err("E21", f"shared/design/screens/{name}: ad_slot {a.get('slot_id')!r} region=inline "
                           f"nhung khong co after_component_id -> khong biet chen sau cai gi")


# ─────────────────────────── F. Single-writer invariant ───────────────────────────
def check_ownership(ownership, units, mans):
    """Cuong che kernel/contracts/data-ownership.json: moi file du lieu co DUNG 1 unit ghi.

    Day la co che chong race condition khi concurrency > 1 — khong co 2 writer thi
    khong the tranh chap, khong can lock.
    """
    if ownership is None:
        return
    owners = strip_meta(ownership.get("owners", {}))
    if not owners:
        err("F0", "data-ownership.json: khong co entry 'owners' nao")
        return

    SPECIAL = {"__kernel__", "__human__", "__generated__"}
    for path, owner in owners.items():
        full = rel(*path.split("/"))
        is_dir = path.endswith("/")

        # duong dan phai ton tai (thu muc co the chua rong -> WARN)
        if is_dir:
            if not os.path.isdir(full.rstrip(os.sep)):
                warn("F1", f"data-ownership: thu muc {path!r} chua ton tai (owner={owner})")
        elif not os.path.exists(full):
            err("F1", f"data-ownership: file {path!r} khong ton tai (owner={owner}) "
                       f"-> bang so huu tro vao file da bi xoa/doi ten")

        if owner in SPECIAL:
            continue
        if owner not in units:
            err("F2", f"data-ownership: owner {owner!r} cua {path!r} khong phai unit trong dag.json "
                       f"(dung ten UNIT, vd 'mobile-shell', khong dung role 'mobile')")
            continue

        # QUY TAC RACE: unit scope=story + file don + role concurrency>1 = 2 instance ghi cung file
        role = units[owner].get("role")
        scope = units[owner].get("scope")
        conc = (mans.get(role) or {}).get("concurrency", 1)
        if scope == "story" and not is_dir and conc and conc > 1:
            err("F3", f"RACE: {path!r} la file don, owner={owner} co scope=story, "
                       f"va role {role!r} co concurrency={conc} -> {conc} instance (2 story khac nhau) "
                       f"se ghi cung file va de mat du lieu cua nhau. Sua: doi thanh thu muc per-story "
                       f"('{path.rsplit('/', 1)[0]}/<STORY_ID>...'), HOAC dat concurrency=1 cho {role}.")

    # phat hien file trong shared/ chua duoc khai chu so huu
    for f in glob.glob(rel("shared", "**", "*"), recursive=True):
        if os.path.isdir(f):
            continue
        p = os.path.relpath(f, ROOT).replace(os.sep, "/")
        if p in owners:
            continue
        if any(p.startswith(d) for d in owners if d.endswith("/")):
            continue
        warn("F4", f"{p}: khong khai trong data-ownership.json -> khong biet ai duoc ghi, "
                    f"co the bi 2 agent ghi dong thoi ma khong ai phat hien")

    # unit ghi >1 file don la OK; nhung 1 file co >1 owner thi JSON da khong cho phep (key trung)
    # -> kiem chieu nguoc: co unit nao duoc khai la owner cua ca file va thu muc cha khong
    dirs = [d for d in owners if d.endswith("/")]
    for path in owners:
        for d in dirs:
            if path != d and path.startswith(d) and owners[path] != owners[d]:
                err("F5", f"XUNG DOT SO HUU: {path!r} (owner={owners[path]}) nam trong "
                           f"{d!r} (owner={owners[d]}) -> 2 unit deu co quyen ghi cung vung")

    # F6: agents/<role>/memory/ phai la MOT FILE MOI NODE, khong dung 1 file chung
    node_ids = set()
    try:
        w = json.load(open(rel("kernel", "memory", "wbs.json"), encoding="utf-8"))
        node_ids = {n.get("node_id") for n in w.get("nodes", [])}
    except Exception:
        pass
    ALLOW = {"README.md", ".gitkeep", "epics.json"}
    for f in glob.glob(rel("agents", "*", "memory", "*")):
        if os.path.isdir(f):
            continue
        base = os.path.basename(f)
        role = f.split(os.sep)[-3]
        if base in ALLOW:
            continue
        stem = os.path.splitext(base)[0]
        conc = (mans.get(role) or {}).get("concurrency", 1)
        if node_ids and stem not in node_ids:
            err("F6", f"agents/{role}/memory/{base}: ten file khong phai node_id nao trong wbs.json "
                       f"-> pham quy uoc 'mot file moi node'. Xem agents/{role}/memory/README.md")
        elif not node_ids and conc > 1:
            err("F6", f"agents/{role}/memory/{base}: role nay co concurrency={conc} nhung file "
                       f"khong dat ten theo node_id -> {conc} instance se ghi cung file, mat du lieu. "
                       f"Doi thanh <node_id>.md")


# ─────────────────────────── G. Boot context (kernel -> agent) ───────────────────────────
def check_boot(boot_schema, nodes, units, mans, dag):
    """Kiem kernel/boot/<node_id>.md — chieu kernel->agent, doi xung voi nhom D (agent->kernel)."""
    files = sorted(glob.glob(rel("kernel", "boot", "*.md")))
    if not files:
        warn("G1", "kernel/boot/ khong co boot context nao — binh thuong voi repo template. "
                   "Sinh bang: python kernel/tools/context_compile.py <node_id>")
        return
    required = set((boot_schema or {}).get("required", []))
    by_unit = {(d.get("role"), d.get("phase")): u for u, d in units.items()}
    sync = strip_meta((dag or {}).get("sync_allowed", {}))

    for path in files:
        name = os.path.basename(path)
        fm, e = parse_frontmatter(path)
        if e:
            err("G2", f"boot/{name}: {e}")
            continue
        missing = required - {k for k in fm if not k.startswith("__")}
        if missing:
            err("G3", f"boot/{name}: thieu field bat buoc {sorted(missing)}")

        nid = fm.get("node_id")
        if nodes and nid not in nodes:
            err("G4", f"boot/{name}: node_id={nid!r} khong co trong wbs.json "
                       f"-> boot context cua node da bi xoa, agent se lam viec mu")
            continue
        if os.path.splitext(name)[0] != str(nid):
            err("G5", f"boot/{name}: ten file khac node_id={nid!r} -> pham quy uoc "
                       f"'mot file moi node', de doc lan boot context cua node khac")
        node = nodes.get(nid) if nodes else None

        # ngan sach token — day la Gate 0 dieu 8
        bt, mx = fm.get("bundle_tokens"), fm.get("max_context_tokens")
        if isinstance(bt, int) and isinstance(mx, int):
            if bt > mx:
                err("G6", f"boot/{name}: bundle_tokens={bt} > max_context_tokens={mx} "
                           f"-> KHONG duoc dispatch (Gate 0 dieu 8). Chay context_compile.py --explain "
                           f"de biet nguon nao phinh to; KHONG tu cat bot roi dispatch.")
            elif bt > mx * 0.9:
                warn("G7", f"boot/{name}: bundle_tokens={bt} da dung {bt*100//mx}% ngan sach "
                           f"({mx}) -> story phuc tap hon mot chut la vuot. Xem lai anchor-tag.")
        if isinstance(mx, int) and node and mans.get(node.get("role")):
            want = mans[node["role"]].get("max_context_tokens")
            if want != mx:
                err("G8", f"boot/{name}: max_context_tokens={mx} khac manifest cua role "
                           f"{node.get('role')!r} ({want}) -> boot context sinh tu manifest cu")

        # retry phai co last_error
        att = fm.get("attempt")
        if isinstance(att, int) and att > 1 and not fm.get("last_error"):
            err("G9", f"boot/{name}: attempt={att} (retry) nhung last_error rong "
                       f"-> retry mu, agent lam lai y nhu lan truoc")
        if node and isinstance(att, int):
            want_att = ((node.get("gate") or {}).get("consecutive_fail") or 0) + 1
            if att != want_att:
                warn("G10", f"boot/{name}: attempt={att} nhung wbs.json cho thay {want_att} "
                            f"-> boot context sinh tu trang thai cu, compile lai truoc khi dispatch")

        # Tier 2 rong voi node scope=story = LOI TAG
        if node and node.get("story_id") and fm.get("tier2_sources") in ([], None, ""):
            err("G11", f"boot/{name}: tier2_sources rong nhung node co story_id="
                        f"{node.get('story_id')!r} -> LOI TAG (khong phai 'story khong co noi dung'). "
                        f"Agent se lam viec ma khong co du lieu nghiep vu nao.")

        # quyen han phai khop dag.json (kernel co dac cho agent — lech la agent bi chan oan/duoc qua quyen)
        if node:
            unit = by_unit.get((node.get("role"), node.get("phase")))
            if unit:
                want_h = sorted({units[f]["role"] for f in units[unit].get("feeds", []) if f in units}
                                | {units[f]["role"] for f in units[unit].get("runtime_feeds", []) if f in units})
                got_h = str(fm.get("allowed_handoff_to") or "").strip("[]")
                got_h = sorted(x.strip() for x in got_h.split(",") if x.strip())
                if got_h != want_h:
                    err("G12", f"boot/{name}: allowed_handoff_to={got_h} khac dag.json ({want_h}) "
                                f"-> agent se bi Gate 0 chan oan, hoac duoc qua quyen")
                want_s = sorted(sync.get(node.get("role"), []))
                got_s = str(fm.get("allowed_sync_with") or "").strip("[]")
                got_s = sorted(x.strip() for x in got_s.split(",") if x.strip())
                if got_s != want_s:
                    err("G13", f"boot/{name}: allowed_sync_with={got_s} khac dag.json ({want_s})")

        # boot context cho node da xong = rac, de lai se gay nham
        if node and node.get("status") in ("done", "failed"):
            warn("G14", f"boot/{name}: node da {node.get('status')!r} nhung boot context van con "
                        f"-> file cu, xoa hoac bo qua khi debug")

        # body phai co dung cac muc theo contract
        try:
            body = open(path, encoding="utf-8").read().split("\n---", 1)[1]
        except Exception:
            body = ""
        for h in ["## 0. ", "## 1. ", "## 2. ", "## 3. "]:
            if h not in body:
                err("G15", f"boot/{name}: body thieu muc {h.strip()!r} "
                            f"-> agent prompt tham chieu theo so muc nen khong duoc thieu/doi so")
        if isinstance(att, int) and att > 1 and "## 4. " not in body:
            err("G16", f"boot/{name}: attempt={att} nhung body thieu muc '## 4.' (loi lan truoc)")


# ─────────────────────────── SELFTEST: mo phong 3 track ───────────────────────────
def selftest(units, mans):
    print("\n--- SELFTEST: mo phong sinh track tu dag.json (kiem LUAT, khong can du lieu thuc) ---")
    agents = {a for a in mans if a != "_template"}
    core_units = [u for u, d in units.items() if mans.get(d["role"], {}).get("core") is True]
    cap_units = [u for u, d in units.items() if mans.get(d["role"], {}).get("core") is False]

    def show(label, track_units, monet=False, expect=None):
        graph = {u: expected_deps(units, u, track_units, monet) for u in track_units}
        ready = [u for u, d in graph.items() if not d]
        print(f"  {label}")
        for u in sorted(graph):
            print(f"      {u:16} depends_on={graph[u]}")
        if not ready:
            err("S1", f"selftest[{label}]: KHONG co unit nao ready -> track khong the khoi dong")
        else:
            print(f"      -> ready ngay: {ready}")
        if expect:
            for u, exp in expect.items():
                if graph.get(u) != exp:
                    err("S2", f"selftest[{label}]: {u}.depends_on ky vong {exp}, duoc {graph.get(u)}")
        return graph

    show("track intake", ["po", "ba", "cto"],
         expect={"po": [], "ba": ["po"], "cto": ["ba"]})

    build_units = [u for u in core_units if u not in ("po", "ba", "cto")]
    show("track build (khong ads)", build_units,
         expect={"qa": ["dev-be", "mobile-screen"]})

    show("track build (+ads, Monetization:true)", build_units + cap_units, monet=True,
         expect={"qa": ["ads-placement", "dev-be", "mobile-screen"],
                 "ads-placement": ["ads-setup", "mobile-screen"]})

    for entry in ("mobile-screen", "dev-be"):
        cl = [u for u in downstream_closure(units, entry) if not units[u].get("only_if")]
        show(f"track runtime (entry={entry})", cl, expect={entry: []})

    for a in sorted(agents):
        if not any(units[u]["role"] == a for u in units):
            err("S3", f"selftest: agent {a} khong xuat hien trong bat ky track nao")


# ─────────────────────────── main ───────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Kiem tra tinh nhat quan control plane cua OS prompt")
    ap.add_argument("--selftest", action="store_true", help="mo phong sinh 3 track tu dag.json")
    ap.add_argument("--json", action="store_true", help="output JSON cho tool tu dong doc")
    args = ap.parse_args()

    schema = load_json("kernel/contracts/agent-manifest.schema.json", "A0")
    msg_schema = load_json("kernel/contracts/message.schema.json", "D0")
    dag = load_json("kernel/contracts/dag.json", "B0")
    wbs = load_json("kernel/memory/wbs.json", "C0")
    profile = load_json("kernel/memory/project-profile.json", "P0")
    escalation = load_json("kernel/config/escalation.json", "A0b")
    ownership = load_json("kernel/contracts/data-ownership.json", "F0b")
    limits = load_json("kernel/config/limits.json", "L0")
    boot_schema = load_json("kernel/contracts/boot-context.schema.json", "G0")

    mans = check_manifests(schema, escalation)
    units = check_dag(dag, mans)
    nodes = check_wbs(wbs, units, mans, profile, limits) if units else {}
    if units:
        check_mailbox(msg_schema, nodes, units, dag, mans, limits)
        check_ownership(ownership, units, mans)
        check_boot(boot_schema, nodes, units, mans, dag)
    check_crossrefs(mans, profile)
    check_design_prereqs()
    check_screen_layouts(limits)
    if args.selftest and units:
        selftest(units, mans)

    errors = [f for f in FINDINGS if f[0] == "ERROR"]
    warns = [f for f in FINDINGS if f[0] == "WARN"]

    if args.json:
        print(json.dumps({
            "ok": not errors,
            "errors": [{"code": c, "message": m} for _, c, m in errors],
            "warnings": [{"code": c, "message": m} for _, c, m in warns],
        }, ensure_ascii=False, indent=2))
        return 1 if errors else 0

    print("\n" + "=" * 72)
    if errors:
        print(f"ERROR ({len(errors)}) — control plane KHONG nhat quan, phai sua truoc khi chay:")
        for _, c, m in errors:
            print(f"  [{c}] {m}")
    if warns:
        print(f"\nWARN ({len(warns)}) — khong chan, nhung nen xem:")
        for _, c, m in warns:
            print(f"  [{c}] {m}")
    if not errors and not warns:
        print("OK — control plane nhat quan, khong canh bao.")
    elif not errors:
        print("\nOK — khong co ERROR.")
    print("=" * 72)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
