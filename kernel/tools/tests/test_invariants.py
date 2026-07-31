#!/usr/bin/env python3
"""
kernel/tools/tests/test_invariants.py — Chung minh validator BAT duoc nhung gi no tuyen bo.

    python kernel/tools/tests/test_invariants.py       # exit 0 = moi lo van con bit

VI SAO CAN FILE NAY: `validate.py --selftest` kiem tinh nhat quan cua repo HIEN TAI — no khong
tra loi duoc cau hoi "neu ai do lam sai thi validator co bao khong?". Va cau tra loi tung la
KHONG cho nhieu invariant duoc tuyen bo ro trong tai lieu:
  - node consecutive_fail:99 + status:ready + after_fail:3  -> 0 finding (nguyen tac bat bien #4)
  - awaiting_human_decision + consecutive_fail:5            -> 0 finding (du ORCHESTRATOR.md:140
                                                              goi ten dung ma C33)
  - quen processed_at o duong RETRY                         -> 0 finding (dung loop vo han ma
                                                              D12 sinh ra de chan)
Moi ca duoi day nap state GIA roi doi chieu ma ky vong CO / KHONG CO. Chay lai sau MOI lan sua
kernel: neu 1 ca chuyen tu PASS sang FAIL thi mot lo vua bi mo lai.

Goi truc tiep check_wbs/check_mailbox nen khong cham wbs.json. Rieng check_mailbox doc thu muc
that nen co ghi 1 file tam kernel/mailbox/_regress.md va xoa trong `finally`.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "kernel", "tools"))
import validate as V

dag = V.load_json("kernel/contracts/dag.json", "B0")
mans = V.check_manifests(V.load_json("kernel/contracts/agent-manifest.schema.json", "A0"),
                         V.load_json("kernel/config/escalation.json", "A0b"))
units = V.check_dag(dag, mans)
limits = V.load_json("kernel/config/limits.json", "L0")
msg_schema = V.load_json("kernel/contracts/message.schema.json", "D0")
profile = {"active_capability_agents": ["ads"]}
V.FINDINGS.clear()

PASS, FAIL = [], []


def node(nid, role, phase, status, **kw):
    n = {"node_id": nid, "track": "build", "track_id": nid.split("-")[0],
         "story_id": None, "role": role, "phase": phase, "depends_on": [],
         "status": status, "message_refs": [], "started_at": None, "finished_at": None,
         "gate": {"name": None, "result": None, "consecutive_fail": 0, "last_error": None,
                  "escalated_at": None, "resume_history": []}}
    for k, v in kw.items():
        if k == "gate":
            n["gate"].update(v)
        else:
            n[k] = v
    return n


def run_wbs(nodes):
    V.FINDINGS.clear()
    V.check_wbs({"nodes": nodes}, units, mans, profile, limits,
                {"delivery_targets": ["mobile_native", "backend_service"]})
    return {c for _, c, _ in V.FINDINGS}


def run_mail(nodes, fm, body="x"):
    """Ghi 1 message tam vao mailbox that roi chay check_mailbox, sau do xoa."""
    V.FINDINGS.clear()
    mb = os.path.join(REPO, "kernel", "mailbox", "_regress.md")
    lines = ["---"] + [f"{k}: {'null' if v is None else v}" for k, v in fm.items()] + ["---", body]
    with open(mb, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    try:
        V.check_mailbox(msg_schema, {n["node_id"]: n for n in nodes}, units, dag, mans, limits)
    finally:
        os.remove(mb)
    return {c for _, c, _ in V.FINDINGS}


def run_mails(nodes, envelopes):
    """Like run_mail, but supports request/response evidence checks."""
    V.FINDINGS.clear()
    paths = []
    try:
        for i, fm in enumerate(envelopes):
            p = os.path.join(REPO, "kernel", "mailbox", f"_regress-{i}.md")
            lines = ["---"] + [f"{k}: {'null' if v is None else v}" for k, v in fm.items()] + ["---", "x"]
            with open(p, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            paths.append(p)
        V.check_mailbox(msg_schema, {n["node_id"]: n for n in nodes}, units, dag, mans, limits)
    finally:
        for p in paths:
            if os.path.exists(p):
                os.remove(p)
    return {c for _, c, _ in V.FINDINGS}


def expect(label, codes, must_have=(), must_not=()):
    ok = True
    for c in must_have:
        if c not in codes:
            FAIL.append(f"{label}: THIEU ma ky vong {c}  (co: {sorted(codes)})")
            ok = False
    for c in must_not:
        if c in codes:
            FAIL.append(f"{label}: KHONG duoc co ma {c}  (co: {sorted(codes)})")
            ok = False
    if ok:
        PASS.append(label)


# ─────────── 1. node la bao xong ve __end__ (truoc day MOI handoff bi D10 chan) ───────────
n_infra = node("PROJ-devops-infra", "devops", "devops-infra", "done",
               gate={"name": "gate3", "result": "pass"}, message_refs=["msg-PROJ-devops-infra-1"])
codes = run_mail([n_infra], {
    "message_id": "msg-PROJ-devops-infra-1", "type": "handoff", "node_id": "PROJ-devops-infra",
    "task_id": "PROJ", "from": "devops", "to": "__end__", "status": "resolved",
    "processed_at": "2026-07-31T10:00:00Z", "schema_version": 1, "gate_ref": "gate3"})
expect("1. devops-infra handoff to __end__", codes, must_not=("D10",))

# node KHONG khai __end__ thi khong duoc dung no de tron viec bao cho ben xuoi dong
n_dev = node("US014-dev-be", "dev-be", None, "done", story_id="US-014", track_id="US014",
             gate={"name": "gate3", "result": "pass"})
codes = run_mail([n_dev], {
    "message_id": "msg-US014-dev-be-1", "type": "handoff", "node_id": "US014-dev-be",
    "task_id": "US-014", "from": "dev-be", "to": "__end__", "status": "resolved",
    "processed_at": "2026-07-31T10:00:00Z", "schema_version": 1})
expect("1b. dev-be KHONG duoc lam dung __end__", codes, must_have=("D10",))

# ─────────── 2. qa tra bug ve dev (duong reject_feeds) ───────────
n_qa = node("US014-qa", "qa", None, "blocked", story_id="US-014", track_id="US014",
            gate={"name": "gate4"}, message_refs=["msg-US014-qa-1"])
codes = run_mail([n_qa], {
    "message_id": "msg-US014-qa-1", "type": "handoff", "node_id": "US014-qa",
    "task_id": "US-014", "from": "qa", "to": "client", "status": "rejected",
    "processed_at": "2026-07-31T10:00:00Z", "schema_version": 1, "event": "bug_report"})
expect("2. qa -> client (reject_feeds)", codes, must_not=("D10",))

codes = run_mail([n_qa], {
    "message_id": "msg-US014-qa-1", "type": "handoff", "node_id": "US014-qa",
    "task_id": "US-014", "from": "qa", "to": "client", "status": "rejected",
    "processed_at": "2026-07-31T10:00:00Z", "schema_version": 1})
expect("2b. duong tra ve thieu 'event' bi chan", codes, must_have=("D10b",))

# ─────────── 3. sync node go duoc deadlock waiting_sync ───────────
ask = node("US014-designer-screen", "designer", "designer-screen", "waiting_sync",
           story_id="US-014", track_id="US014", gate={"name": "gate5",
           "sync_waiting_for": "req-US014-designer-screen-1"},
           depends_on=["PROJ-design-system", "US014-designer-screen"])
ask["depends_on"] = []
syn = node("US014-designer-screen-sync-1", "ba", None, "ready", story_id="US-014",
           track_id="US014", kind="sync", sync_for_node="US014-designer-screen",
           sync_request_id="req-US014-designer-screen-1")
codes = run_wbs([ask, syn])
expect("3. waiting_sync + sync node", codes, must_not=("C6", "C41", "C15", "C4", "C40"))

# thieu sync node -> phai bao (truoc day treo im lang toi khi C28 chan doan SAI la 'agent hang')
codes = run_wbs([ask])
expect("3b. waiting_sync ma khong ai tra loi", codes, must_have=("C41",))

# ─────────── 4. invariant #4: quen escalate (truoc day 0 finding) ───────────
n = node("US014-client-screen", "client", "client-screen", "ready", story_id="US-014",
         track_id="US014", gate={"name": "gate3", "consecutive_fail": 99,
                                 "last_error": "lint fail"})
codes = run_wbs([n])
expect("4. consecutive_fail=99 + ready", codes, must_have=("C42",))

n = node("US014-client-screen", "client", "client-screen", "waiting_human", story_id="US-014",
         track_id="US014", gate={"name": "gate3", "consecutive_fail": 0,
                                 "escalated_at": "2026-07-31T10:00:00Z"})
codes = run_wbs([n])
expect("4b. waiting_human ma bo dem = 0", codes, must_have=("C43",))

# ─────────── 5. awaiting_human_decision khong duoc mang nghia LOI ───────────
n = node("PROJ-design-system", "designer", "design-system", "awaiting_human_decision",
         gate={"name": "gate7", "decision_requested_at": "2026-07-31T10:00:00Z",
               "consecutive_fail": 5})
codes = run_wbs([n])
expect("5. awaiting_human_decision + consecutive_fail=5", codes, must_have=("C33",))

n = node("US014-qa", "qa", None, "awaiting_human_decision", story_id="US-014", track_id="US014",
         gate={"name": "gate4", "decision_requested_at": "2026-07-31T10:00:00Z"})
codes = run_wbs([n])
expect("5b. awaiting_human_decision o gate KHAC gate7", codes, must_have=("C44",))

# ─────────── 6. processed_at: duong RETRY truoc day vo hinh ───────────
n = node("US014-dev-be", "dev-be", None, "ready", story_id="US-014", track_id="US014",
         gate={"name": "gate3", "consecutive_fail": 1, "last_error": "test fail"},
         message_refs=["msg-US014-dev-be-1"])
codes = run_mail([n], {
    "message_id": "msg-US014-dev-be-1", "type": "handoff", "node_id": "US014-dev-be",
    "task_id": "US-014", "from": "dev-be", "to": "qa", "status": "pending",
    "processed_at": None, "schema_version": 1})
expect("6. quen processed_at o duong retry", codes, must_have=("D12",))

# ─────────── 7. enum status/schema_version cua message ───────────
codes = run_mail([n_dev], {
    "message_id": "msg-US014-dev-be-1", "type": "handoff", "node_id": "US014-dev-be",
    "task_id": "US-014", "from": "dev-be", "to": "qa", "status": "khong-co-trong-enum",
    "processed_at": "2026-07-31T10:00:00Z", "schema_version": 7})
expect("7. status/schema_version sai enum", codes, must_have=("D4b", "D4c"))

# ─────────── 8. sync node khong duoc bat dau viec moi ───────────
codes = run_mail([syn], {
    "message_id": "msg-US014-designer-screen-sync-1-1", "type": "handoff",
    "node_id": "US014-designer-screen-sync-1", "task_id": "US-014", "from": "ba",
    "to": "cto", "status": "resolved", "processed_at": "2026-07-31T10:00:00Z",
    "schema_version": 1})
expect("8. sync node emit handoff bi chan", codes, must_have=("D10",))

# ─────────── 9. response phai ke thua max_turns cua request ───────────
requester = node("US014-client-screen", "client", "client-screen", "waiting_sync",
                 story_id="US-014", track_id="US014", gate={"name": "gate3"})
codes = run_mails([requester], [
    {"message_id": "msg-US014-client-screen-1", "type": "request", "node_id": "US014-client-screen",
     "task_id": "US-014", "from": "client", "to": "cto", "status": "pending", "processed_at": None,
     "schema_version": 1, "request_id": "req-1", "turn": 1, "max_turns": 2},
    {"message_id": "msg-US014-client-screen-2", "type": "response", "node_id": "US014-client-screen",
     "task_id": "US-014", "from": "client", "to": "cto", "status": "pending", "processed_at": None,
     "schema_version": 1, "request_id": "req-1", "turn": 3},
])
expect("9. response vuot max_turns cua request", codes, must_have=("D7b",))

# ─────────── 10. signoff phai tro message that cua dung role ───────────
gate1 = node("INTAKE001-cto", "cto", None, "done", track="intake", track_id="INTAKE001",
             gate={"name": "gate1", "required_signoffs": ["ba", "cto"],
                   "signoffs": [{"role": "ba", "message_id": "msg-INTAKE001-cto-1"}]})
codes = run_mail([gate1], {
    "message_id": "msg-INTAKE001-cto-1", "type": "handoff", "node_id": "INTAKE001-cto",
    "task_id": "INTAKE001", "from": "cto", "to": "__end__", "status": "resolved",
    "processed_at": "2026-07-31T10:00:00Z", "schema_version": 1})
expect("10. signoff mao danh bi chan", codes, must_have=("C26",))

print("\n".join(f"  PASS  {p}" for p in PASS))
if FAIL:
    print("\n" + "\n".join(f"  FAIL  {f}" for f in FAIL))
print(f"\n{len(PASS)} pass / {len(FAIL)} fail")
sys.exit(1 if FAIL else 0)
