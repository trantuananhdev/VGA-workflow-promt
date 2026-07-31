#!/usr/bin/env python3
"""
kernel/tools/context_compile.py — Sinh boot context (kernel -> agent).

    python kernel/tools/context_compile.py <node_id>              # ghi kernel/boot/<node_id>.md
    python kernel/tools/context_compile.py <node_id> --stdout     # xem truoc, khong ghi
    python kernel/tools/context_compile.py <node_id> --explain    # in bang phan bo token theo nguon

Day la mat xich cuoi cua ha tang: no bien 2 thu tu "mo ta" thanh "thuc thi duoc":
  1. Chieu kernel->agent co contract that (kernel/contracts/boot-context.schema.json)
  2. Gate 0 dieu 8 (token budget) va dieu 9 (anchor ton tai) kiem duoc that

NGUYEN TAC: XAC DINH, KHONG DUNG LLM. Trich theo anchor-tag/story_id, khong tom tat.
Toi uu context xay ra LUC GHI (agent gan tag dung), khong phai luc doc (tom tat runtime).
Neu buoc nay tom tat thi moi bao dam ve "agent doc dung ban goc" bi mat.
"""
import argparse
import glob
import json
import math
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _atomic import write_atomic

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BOOT_DIR = os.path.join(ROOT, "kernel", "boot")
TOOL_VERSION = "context_compile.py v1"

ANCHOR_RE = re.compile(r"<!--\s*tier:2\s+role:([a-z0-9,\-]+)\s+story:([A-Za-z0-9\-]+)\s*-->")


def rel(*p):
    return os.path.join(ROOT, *p)


def die(msg, code=2):
    print(f"LOI: {msg}", file=sys.stderr)
    sys.exit(code)


def load_json(path, required=True):
    full = rel(*path.split("/"))
    if not os.path.exists(full):
        if required:
            die(f"thieu file bat buoc: {path}")
        return None
    try:
        with open(full, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        die(f"{path}: JSON khong parse duoc — {e}")


def strip_meta(d):
    return {k: v for k, v in d.items() if not k.startswith("_")}


# Ky tu khien 1 scalar YAML khong con la scalar thuong neu de tran.
_YAML_NEEDS_QUOTE = set(":#[]{}&*!|>'\"%@`,")


def yaml_scalar(v):
    """Tra ve dang YAML AN TOAN cua 1 gia tri vo huong.

    VI SAO CAN: render() truoc day noi thang f"{k}: {v}". `last_error` la VAN BAN TU DO do
    Orchestrator ghi tu log gate fail that (vd output cua `flutter analyze`), thuong NHIEU DONG.
    Ket qua da kiem: boot context co
        last_error: flutter analyze:
          3 errors in otp.dart
    lam validate.parse_frontmatter tra loi "dong khong phai 'key: value'" -> ma G2, va
    frontmatter trong prompt cua agent vo cau truc. Lop loi nay chi xay ra o duong RETRY —
    tuc dung luc moi thu da dang sai, va no bien 1 lan retry thanh 1 lan hong han.
    """
    s = str(v)
    if s == "":
        return '""'
    needs = ("\n" in s or "\r" in s or "\t" in s
             or s != s.strip()                              # dau/cuoi co khoang trang
             or s[0] in "-?:,[]{}#&*!|>'\"%@`"              # ky tu mo dau dac biet cua YAML
             or any(c in _YAML_NEEDS_QUOTE for c in s)
             or s.lower() in ("null", "true", "false", "~", "yes", "no", "on", "off"))
    if not needs:
        return s
    esc = (s.replace("\\", "\\\\").replace('"', '\\"')
            .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t"))
    return f'"{esc}"'


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ─────────────────────────── Dem token (uoc luong, khong dependency) ───────────────────────────
def est_tokens(text, divisor):
    """Uoc luong token. KHONG chinh xac tuyet doi — khong dung tokenizer that de giu stdlib-only.

    Chon divisor nho hon thuc te (mac dinh 3.0 ky tu/token) de UOC LUONG CAO HON thuc,
    tuc fail-safe: tha bao vuot ngan sach oan hon la de agent that su bi tran context.
    Tieng Viet co dau ton token hon tieng Anh nen divisor thap la co y.
    Muon doi: kernel/config/limits.json -> context.token_chars_per_token.
    """
    return math.ceil(len(text) / divisor)


# ─────────────────────────── Trich Tier 2 tu markdown (anchor-tag) ───────────────────────────
def slice_markdown(path, role, story_id):
    """Tra list (anchor_label, block_text). Trich tu tag den tag/heading cung cap tiep theo."""
    full = rel(*path.split("/"))
    if not os.path.exists(full):
        return [], f"khong ton tai"
    text = open(full, encoding="utf-8").read()
    out, foreign_story, foreign_role = [], False, False

    matches = list(ANCHOR_RE.finditer(text))
    for i, m in enumerate(matches):
        roles = [r for r in m.group(1).split(",") if r]
        story = m.group(2)
        if story != story_id:
            foreign_story = True
            continue
        if role not in roles:
            foreign_role = True
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        # Cat o heading BAT KY CAP (#, ##, ###...) — sang muc khac cua file thi het pham vi tag.
        # TRUOC DAY chi cat o cap 1 (r"\n#\s"), trong khi shared/architecture.md va
        # shared/system-spec.md khong he co heading cap 1 nao -> block cua anchor CUOI CUNG hut
        # toan bo phan con lai cua file. Hien tai chua vo chi vi tinh co co anchor thu hai theo
        # sau. Voi 1 architecture.md that (dai, anchor nam gan dau file) thi day chinh la cach
        # bundle no ngan sach — va thong bao loi luc do lai do cho "thiet ke tagging".
        block = re.split(r"\n#{1,6}\s", block)[0].strip()
        if block:
            out.append((f"{path}#{story}", block))

    if out:
        return out, None
    if foreign_role:
        return [], (f"co block cho story {story_id} nhung role {role!r} KHONG nam trong danh sach "
                    f"role: cua anchor-tag -> hoac tag thieu role, hoac agent nay khong can file nay")
    if foreign_story:
        return [], f"co anchor-tag nhung khong co block nao cho story {story_id}"
    return [], "khong co anchor-tag nao (file chua duoc gan tag tier:2)"


# ─────────────────────────── Trich Tier 2 tu JSON (loc theo story_id) ───────────────────────────
def slice_json_entries(path, role, story_id, list_key, default_roles):
    """JSON khong co comment nen loc theo field story_id cua tung entry."""
    data = load_json(path, required=False)
    if data is None:
        return [], "khong ton tai"
    entries = data.get(list_key)
    if not isinstance(entries, list):
        return [], f"thieu mang {list_key!r}"
    picked, missing_story = [], 0
    for e in entries:
        if not isinstance(e, dict):
            continue
        if not e.get("story_id"):
            missing_story += 1
            continue
        if e["story_id"] != story_id:
            continue
        if role not in (e.get("roles") or default_roles):
            continue
        picked.append(e)
    if missing_story:
        print(f"  CANH BAO: {path} co {missing_story} entry thieu story_id -> chung VO HINH "
              f"voi moi agent (context_compile khong the trich)", file=sys.stderr)
    if not picked:
        return [], f"khong co entry nao khop story {story_id} + role {role}"
    body = json.dumps({list_key: picked}, ensure_ascii=False, indent=2)
    return [(f"{path}#{story_id}", body)], None


# ─────────────────────────── Nguon Tier 2 ───────────────────────────
# KHONG co danh sach "role nay doc file nao" trong tool nay — CO Y.
#
# Quyen doc duoc khai o DUNG 1 NOI: field `role:` trong anchor-tag cua tung block
# (voi markdown), va field `roles` cua tung entry (voi JSON). Tool chi QUET va LOC.
#
# Vi sao: neu tool giu them 1 danh sach rieng thi co 2 nguon su that cho cung 1 cau hoi
# "role nay duoc doc gi" — va chung se lech. Da tung xay ra that: tag PRD.md cho phep
# `client` doc, nhung danh sach trong tool lai khong nap PRD -> client mat acceptance
# criteria ma khong ai bao loi. Day dung la lop loi da khien manifest.depends_on va
# process-table.json bi bo.
#
# He qua tot: them file moi vao shared/ KHONG can sua tool. Chi can gan anchor-tag.

# JSON khong co comment nen phai biet SHAPE cua tung file (mang nao chua entry).
# Day la kien thuc ve CAU TRUC, khong phai ve QUYEN — nen o day la dung cho.
JSON_SHAPES = [
    ("shared/contracts/api-contracts.json", "endpoints", ["cto", "dev-be", "client", "qa"]),
    ("shared/capabilities/client.json", "permissions", ["client", "ads", "qa", "devops"]),
    ("shared/contracts/domain-map.json", "stories", ["designer"]),
    # default_roles cua tech-stack MO RONG tu ["designer"] sang ca client/dev-be/devops/qa:
    # tu khi de bai quyet dinh tech stack, entry nay khong con chi de designer khoanh vung thu
    # vien UI — `client` doc no o BUOC 0 de biet nap platform pack nao (khong co thi no phai tu
    # doan stack, dung lop loi ma tang tech-stack sinh ra de chan). Van la default: entry co
    # field `roles` thi `roles` thang.
    ("shared/contracts/tech-stack.json", "entries", ["designer", "client", "dev-be", "devops", "qa"]),
]

# Khoa lat cat cho node KHONG thuoc 1 story (scope=project/release).
# TRUOC DAY nhung node nay nhan Tier 2 RONG hoan toan — anchor-tag chi co truc `story:`,
# nen client-shell/devops-infra/ads-setup/design-system deu khong nhan duoc gi tu shared/
# du AGENT.md cua chung khai la "doc anchor-tag slice cua architecture.md/system-spec.md".
# Voi design-system dieu do la chi mang: no phai suy ra design token ma khong co dau vao nao
# ve brand/doi tuong nguoi dung/app tham chieu -> se bia ra token. Cach sua nho nhat va dung
# nguyen tac (quyen doc van khai o anchor-tag, tool chi quet+loc): dung PROJ lam story key
# cho node scope=project/release. Khong co block nao gan story:PROJ thi ket qua y nhu truoc
# (rong) — nen thay doi nay tuong thich nguoc hoan toan.
PROJECT_STORY_KEY = "PROJ"


def gather_tier2(role, tier2_key):
    """Quet MOI nguon trong shared/, loc theo (role, tier2_key) tu anchor-tag. Tra (blocks, problems).

    tier2_key LUON la 1 khoa CU THE — story_id that (node scope=story) hoac PROJECT_STORY_KEY
    (node scope=project/release, xem build()). KHONG con nhanh "story_id is None" o day: trach
    nhiem tinh khoa thuoc ve build(), ham nay chi quet+loc theo dung 1 khoa duoc dua vao.
    """
    blocks, problems = [], []
    story_id = tier2_key

    # markdown: quet toan bo shared/, quyet dinh boi anchor-tag
    for full in sorted(glob.glob(rel("shared", "**", "*.md"), recursive=True)):
        path = os.path.relpath(full, ROOT).replace(os.sep, "/")
        b, e = slice_markdown(path, role, story_id)
        blocks.extend(b)
        if e and "khong co anchor-tag nao" not in e:
            problems.append((path, e))

    # json: quyet dinh boi field roles cua tung entry
    for path, key, default_roles in JSON_SHAPES:
        b, e = slice_json_entries(path, role, story_id, key, default_roles)
        blocks.extend(b)
        if e and "khong ton tai" not in e:
            problems.append((path, e))

    return blocks, problems


# ─────────────────────────── Quyen han (co dac tu dag.json) ───────────────────────────
def resolve_permissions(dag, node, role, phase, nodes=None):
    units = strip_meta(dag.get("units", {}))

    # SYNC NODE (§7d): node tam de 1 role co dia chi ma tra loi. Khong thuoc unit nao.
    # Quyen bi bo CHAT hon sync_allowed thong thuong: chi duoc tra loi dung ben da hoi,
    # va KHONG duoc handoff (khong duoc bat dau viec moi ma khong ai yeu cau).
    if node.get("kind") == "sync":
        asker = (nodes or {}).get(node.get("sync_for_node")) or {}
        if not asker:
            die(f"sync node {node.get('node_id')!r} co sync_for_node="
                f"{node.get('sync_for_node')!r} khong ton tai trong wbs.json")
        return None, None, [], [asker.get("role")] if asker.get("role") else []

    unit = next((u for u, d in units.items()
                 if d.get("role") == role and d.get("phase") == phase), None)
    if unit is None:
        die(f"khong tim thay unit trong dag.json cho (role={role}, phase={phase})")
    d = units[unit]
    # Build Mode dung `feeds`; track runtime duoc dung them duong tat `runtime_feeds`.
    feed_units = list(d.get("feeds", []))
    if node.get("track") == "runtime":
        feed_units += list(d.get("runtime_feeds", []))
    handoff = {units[f]["role"] for f in feed_units if f in units}
    # Duong TRA VE (do thi thu ba): qa gui bug_report nguoc ve unit da dung phan loi.
    handoff |= {units[f]["role"] for f in d.get("reject_feeds", []) if f in units}
    # __end__ = diem ket. Phai giu nguyen van trong danh sach: node la CAN mot dich hop le de
    # bao xong, neu khong thi gate cua no (doi "emit handoff") khong bao gio pass duoc.
    if "__end__" in d.get("feeds", []):
        handoff.add("__end__")
    sync = sorted(strip_meta(dag.get("sync_allowed", {})).get(role, []))
    return unit, d.get("gate"), sorted(handoff), sync


def resolve_skills(role):
    """Resolve explicit skill declarations without granting a skill from prose mentions."""
    own = []
    sd = rel("agents", role, "skills")
    if os.path.isdir(sd):
        own = sorted(s for s in os.listdir(sd) if os.path.isdir(os.path.join(sd, s)))
    shared = sorted(s for s in os.listdir(rel("skills"))
                    if os.path.isdir(rel("skills", s))) if os.path.isdir(rel("skills")) else []
    # Shared skills must be referenced by their full path.  A substring check let a
    # skill named `domain` leak to every role whose prose mentioned "domain".
    ap = rel("agents", role, "AGENT.md")
    txt = open(ap, encoding="utf-8").read() if os.path.exists(ap) else ""
    declared = set(re.findall(r"(?<![A-Za-z0-9_.-])skills/([A-Za-z0-9_.-]+)(?:/|\b)", txt))
    return own + [s for s in shared if s in declared]


# ─────────────────────────── Inbox ───────────────────────────
def _unquote(v):
    """Bo quote quanh 1 scalar YAML. PHAI giong validate.parse_frontmatter, neu khong 3 tool
    se khong dong y voi nhau ve message nao dang cho xu ly.

    Da tung lech that: context_compile va digest so chuoi THO nen `processed_at: 'null'` (co
    quote) bi doc la DA xu ly -> message bi loai khoi inbox va agent khong bao gio thay no,
    trong khi validate.py (co strip quote) van thay no dang cho.
    """
    return v.strip().strip("'\"")


def is_unprocessed(fm):
    """Co consume: chua duoc Orchestrator xu ly. 1 noi dinh nghia duy nhat."""
    return _unquote(str(fm.get("processed_at", "null"))) in ("null", "~", "")


def _read_all_messages():
    msgs = []
    for p in sorted(glob.glob(rel("kernel", "mailbox", "*.md"))):
        with open(p, encoding="utf-8", errors="replace") as f:
            text = f.read()
        if not text.startswith("---"):
            continue
        end = text.find("\n---", 3)
        if end == -1:
            continue
        fm = {}
        for line in text[3:end].splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = _unquote(v)
        msgs.append((fm, text[end + 4:].strip(), os.path.basename(p)))
    return msgs


def gather_inbox(node):
    """Message chua tieu thu THUOC VE dung node nay.

    LOC NGHIEM NGAT — day la ranh gioi isolation cua he thong: agent KHONG duoc thay
    message gui cho agent khac, cung khong duoc thay message cua story khac.
    Dieu kien:
      - chua tieu thu (processed_at == null)
      - to == role cua node
      - cung story (hoac 1 trong 2 khong co story -> node scope project/release)
      - rieng type=response: request goc PHAI xuat phat tu chinh node nay (match qua
        request_id), khong chi can to == role — vi 2 node cung role co the cung mo
        Sync Session mot luc.
    """
    role, story = node.get("role"), node.get("story_id")
    nid = node.get("node_id")
    all_msgs = _read_all_messages()
    # map request_id -> node_id cua request goc
    req_owner = {fm.get("request_id"): fm.get("node_id")
                 for fm, _, _ in all_msgs if fm.get("type") == "request" and fm.get("request_id")}

    # Unit xuoi dong cua node nay (theo dag.json feeds/reject_feeds): message hop le phai den
    # TU 1 trong cac unit thuong nguon. Dung de loc message cho node KHONG co story (xem duoi).
    out = []
    for fm, body, fname in all_msgs:
        if not is_unprocessed(fm):
            continue
        if fm.get("to") != role:
            continue

        if fm.get("type") == "response":
            # response chi thuoc ve dung node da mo request do
            if req_owner.get(fm.get("request_id")) != nid:
                continue
            out.append((fm, body, fname))
            continue

        mstory = fm.get("task_id")
        if story:
            if mstory and mstory != story:
                continue
        else:
            # Node scope=project/release (PROJ-client-shell, PROJ-design-system, REL-devops-release).
            # TRUOC DAY guard chi chay khi CA HAI ben co story, nen node khong co story nhan MOI
            # message chua tieu thu gui toi role do — tu MOI story. Cu the: handoff
            # US014-designer-screen -> client roi vao boot context cua PROJ-client-shell. Vi pham
            # dung docstring ngay tren ("agent KHONG duoc thay message cua story khac") va lam
            # phinh bundle chinh o nhung node co ngan sach chat nhat.
            # Node cap project chi duoc nhan message KHONG thuoc story nao.
            if mstory:
                continue
        out.append((fm, body, fname))
    return out


# ─────────────────────────── Build ───────────────────────────
def build(node_id, args):
    limits = load_json("kernel/config/limits.json") or {}
    divisor = ((limits.get("context") or {}).get("token_chars_per_token")) or 3.0

    wbs = load_json("kernel/memory/wbs.json")
    nodes = {n.get("node_id"): n for n in wbs.get("nodes", [])}
    node = nodes.get(node_id)
    if node is None:
        die(f"node {node_id!r} khong co trong kernel/memory/wbs.json. "
            f"Node phai duoc tao o PHA 0 TRUOC khi compile context (xem ORCHESTRATOR.md §7a).")

    role, phase = node.get("role"), node.get("phase")
    story_id = node.get("story_id")
    dag = load_json("kernel/contracts/dag.json")
    manifest = load_json(f"agents/{role}/manifest.json")

    unit, gate, handoff, sync = resolve_permissions(dag, node, role, phase, nodes)
    if gate != (node.get("gate") or {}).get("name"):
        die(f"node.gate.name={(node.get('gate') or {}).get('name')!r} khac dag.units[{unit}].gate={gate!r} "
            f"-> khong compile khi trang thai da lech (chay validate.py truoc)")

    attempt = ((node.get("gate") or {}).get("consecutive_fail") or 0) + 1
    last_error = (node.get("gate") or {}).get("last_error")
    if attempt > 1 and not last_error:
        die(f"attempt={attempt} (retry) nhung gate.last_error rong -> retry mu, agent se lam lai "
            f"y nhu lan truoc. Orchestrator phai ghi last_error khi Gate fail.")

    # tier2_key: KHAC voi story_id (field metadata giu nguyen None cho node scope=project,
    # ghi dung vao frontmatter boot context). Truoc day dung thang story_id lam khoa quet, nen
    # node scope=project luon co story_id=None -> guard "if story_id and not blocks" duoi day
    # KHONG BAO GIO chan, du blocks rong hoan toan (bug: design-system se nhan Tier 2 rong ma
    # khong ai bao — xem shared/lessons_learned.md). Tach rieng tier2_key va bo dieu kien
    # "if story_id" de guard ap dung DEU cho moi node, khong rieng node co story that.
    tier2_key = story_id if story_id is not None else PROJECT_STORY_KEY
    blocks, problems = gather_tier2(role, tier2_key)
    if not blocks:
        detail = "; ".join(f"{s}: {e}" for s, e in problems) or "khong ro"
        die(f"KHONG trich duoc Tier 2 nao cho (role={role}, tier2_key={tier2_key!r}).\n"
            f"     Chi tiet: {detail}\n"
            f"     Day la LOI TAG, khong phai 'story/project khong co noi dung' — agent se lam "
            f"viec mu neu dispatch tiep. Node scope=project/release -> kiem khoi anchor "
            f"'story:PROJ' co role {role!r} trong shared/architecture.md hoac shared/system-spec.md "
            f"chua (xem validate.py ma E9). Sua anchor-tag trong file nguon roi compile lai.")

    inbox = gather_inbox(node)
    inbox_ids = [fm.get("message_id") for fm, _, _ in inbox]

    # ── than bai
    tier0 = ""
    tp = rel("kernel", "memory", "today.md")
    if os.path.exists(tp):
        tier0 = open(tp, encoding="utf-8").read()
        tier0 = "\n".join(l for l in tier0.splitlines() if not l.startswith(">")).strip()

    tier1_parts = []
    rd = rel("agents", role, "rules")
    if os.path.isdir(rd):
        for f in sorted(glob.glob(os.path.join(rd, "*.md"))):
            tier1_parts.append(open(f, encoding="utf-8").read().strip())
    tier1 = "\n\n".join(tier1_parts) or "_(chưa có rules riêng cho role này)_"

    L = []
    L.append("## 0. Trạng thái hệ thống (Tier 0)\n")
    L.append(tier0 or "_(chưa có digest)_")
    L.append("\n## 1. Luật vai trò của bạn (Tier 1)\n")
    L.append(tier1)
    L.append("\n## 2. Việc cần làm\n")
    if inbox:
        for fm, body, fname in inbox:
            L.append(f"### Từ `{fm.get('from')}` — `{fm.get('message_id')}` ({fm.get('type')})\n")
            if fm.get("artifact_refs"):
                L.append(f"_artifact_refs: {fm.get('artifact_refs')}_\n")
            L.append(body)
            L.append("")
    else:
        L.append(f"_(không có message — bạn là node gốc của track `{node.get('track')}`)_")
    L.append(f"\n## 3. Dữ liệu nghiệp vụ liên quan (Tier 2)\n")
    if blocks:
        for label, block in blocks:
            L.append(f"### `{label}`\n")
            L.append(block)
            L.append("")
    else:
        L.append("_(node scope project/release — không có lát cắt theo story)_")
    if attempt > 1:
        L.append(f"\n## 4. Lần thử trước đã fail vì\n")
        L.append(f"```\n{last_error}\n```")
        L.append(f"\nĐây là lần thử **{attempt}**. Sửa ĐÚNG lỗi trên — không làm lại từ đầu.")
    body_text = "\n".join(L) + "\n"

    fm_fields = {
        "schema_version": 1,
        "node_id": node_id,
        "role": role,
        "phase": phase,
        "track": node.get("track"),
        "track_id": node.get("track_id"),
        "story_id": story_id,
        "gate": gate,
        "attempt": attempt,
        "last_error": last_error if attempt > 1 else None,
        "max_context_tokens": manifest.get("max_context_tokens"),
        "bundle_tokens": 0,
        "inbox": inbox_ids,
        "allowed_handoff_to": handoff,
        "allowed_sync_with": sync,
        "allowed_skills": resolve_skills(role),
        "tier2_sources": [lbl for lbl, _ in blocks],
        "generated_at": now_iso(),
        "compiled_by": TOOL_VERSION,
    }

    def render(fm_dict):
        lines = ["---"]
        for k, v in fm_dict.items():
            if v is None:
                lines.append(f"{k}: null")
            elif isinstance(v, list):
                lines.append(f"{k}: [{', '.join(yaml_scalar(x) for x in v)}]")
            elif isinstance(v, bool):
                lines.append(f"{k}: {'true' if v else 'false'}")
            elif isinstance(v, int):
                lines.append(f"{k}: {v}")
            else:
                lines.append(f"{k}: {yaml_scalar(v)}")
        lines.append("---\n")
        return "\n".join(lines) + body_text

    # dem token roi ghi lai (bundle_tokens nam trong chinh file nen phai tinh 2 vong)
    text = render(fm_fields)
    fm_fields["bundle_tokens"] = est_tokens(text, divisor)
    text = render(fm_fields)
    fm_fields["bundle_tokens"] = est_tokens(text, divisor)
    text = render(fm_fields)

    budget = manifest.get("max_context_tokens") or 0
    over = fm_fields["bundle_tokens"] > budget

    if args.explain or over:
        print(f"\nPhan bo token (uoc luong, {divisor} ky tu/token) — node {node_id}:")
        parts = [("Tier 0 (digest)", tier0), ("Tier 1 (rules)", tier1),
                 ("Tier 2 (nghiep vu)", "\n".join(b for _, b in blocks)),
                 ("Inbox (message)", "\n".join(b for _, b, _ in inbox))]
        for name, t in parts:
            print(f"  {name:22} {est_tokens(t, divisor):6} token  ({len(t)} ky tu)")
        print(f"  {'-'*22} {'-'*6}")
        print(f"  {'TONG':22} {fm_fields['bundle_tokens']:6} / {budget} token"
              f"{'   << VUOT NGAN SACH' if over else ''}")
        if blocks:
            print(f"\n  Chi tiet Tier 2:")
            for lbl, b in sorted(blocks, key=lambda x: -len(x[1])):
                print(f"    {est_tokens(b, divisor):6} token  {lbl}")
    if problems and args.explain:
        print(f"\n  Nguon KHONG trich duoc (co the binh thuong neu role khong can):")
        for s, e in problems:
            print(f"    - {s}: {e}")

    if over:
        die(f"bundle {fm_fields['bundle_tokens']} token > max_context_tokens {budget} cua role {role!r}.\n"
            f"     KHONG tu cat bot ngau nhien roi dispatch (Gate 0 dieu 8). Cach sua dung:\n"
            f"     - Tier 2 qua beo -> chia nho anchor-tag trong file nguon (viec cua cto/ba)\n"
            f"     - Tier 1 qua beo -> chuyen phan it dung sang agents/{role}/docs/ (Layer 1 on-demand)\n"
            f"     - Tier 0 qua beo -> digest.py dang sinh qua dai, xem limits.json context.tier0_max_lines")

    if args.stdout:
        print(text)
    else:
        out = os.path.join(BOOT_DIR, f"{node_id}.md")
        write_atomic(out, text)   # xem kernel/tools/_atomic.py
        print(f"Da ghi {os.path.relpath(out, ROOT)}  "
              f"({fm_fields['bundle_tokens']}/{budget} token, attempt {attempt}, "
              f"{len(blocks)} nguon Tier 2, {len(inbox_ids)} message)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Sinh boot context cho 1 node (kernel -> agent)")
    ap.add_argument("node_id")
    ap.add_argument("--stdout", action="store_true", help="in ra, khong ghi file")
    ap.add_argument("--explain", action="store_true", help="in bang phan bo token theo nguon")
    args = ap.parse_args()
    return build(args.node_id, args)


if __name__ == "__main__":
    sys.exit(main())
