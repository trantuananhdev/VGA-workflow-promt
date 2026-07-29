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
import sys
import glob
import argparse
from collections import defaultdict
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FINDINGS = []          # (severity, code, message)
STATUSES = {"blocked", "ready", "running", "done", "waiting_human", "failed"}
TERMINAL_STUCK = {"waiting_human", "failed"}
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
            track_units = set()
            for m in nodes.values():
                if m.get("track_id") == n.get("track_id"):
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
                    and node.get("status") not in ("done", "failed", "ready"):
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
