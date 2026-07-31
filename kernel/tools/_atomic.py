#!/usr/bin/env python3
"""
kernel/tools/_atomic.py — Ghi file NGUYEN TU + doc JSON co bao loi tu te.

VI SAO CO FILE NAY: ca 3 tool (resume.py, digest.py, context_compile.py) truoc day deu ghi
bang `open(path, "w")` — ma "w" TRUNCATE file truoc khi ghi byte dau tien. Crash, het dia,
hay Ctrl-C dung luc do thi kernel/memory/wbs.json bi cat cut. Do la NGUON SU THAT DUY NHAT
cua scheduler va KHONG co backup (ORCHESTRATOR.md §2: "khoi phuc bang cach doc wbs.json").
Mat no la mat toan bo tien trinh, khong phai mat 1 file.

Nghich ly da ton tai truoc khi sua: resume.py:6 tu nhan la "mot lenh NGUYEN TU, khong the
lam nua voi", trong khi chinh no ghi khong nguyen tu.

CACH LAM: ghi ra <path>.tmp CUNG THU MUC roi os.replace(). os.replace la atomic o cap
filesystem tren ca POSIX va Windows (khac os.rename tren Windows: rename khong ghi de duoc).
Cung thu muc la BAT BUOC — replace qua ranh gioi filesystem khong con atomic.

Chi dung Python stdlib (ORCHESTRATOR.md §0: "kernel/tools/ chi dung Python stdlib").
"""
import json
import os
import sys

__all__ = ["write_atomic", "write_json_atomic", "append_line", "load_json_or_die", "read_text"]


def write_atomic(path, text, encoding="utf-8"):
    """Ghi text vao path mot cach nguyen tu. Tra path da ghi.

    Doc gia HOAC thay noi dung cu nguyen ven, HOAC thay noi dung moi nguyen ven —
    khong bao gio thay file cat cut giua duong.
    """
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    tmp = os.path.join(d, f".{os.path.basename(path)}.tmp")
    try:
        with open(tmp, "w", encoding=encoding, newline="\n") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())     # day xuong dia THAT truoc khi doi ten
        os.replace(tmp, path)        # atomic: doi ten hoac thanh cong hoan toan hoac khong gi ca
    except Exception:
        # don rac de lan sau khong nham .tmp la du lieu that
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        raise
    return path


def write_json_atomic(path, data, indent=2):
    """Ghi JSON nguyen tu, giu dinh dang giong cac file san co trong repo (indent 2 + newline cuoi)."""
    return write_atomic(path, json.dumps(data, ensure_ascii=False, indent=indent) + "\n")


def append_line(path, text, encoding="utf-8"):
    """Append 1 dong (dung cho event-log.jsonl).

    Append KHONG can tmp+replace: mode "a" khong truncate, va 1 dong ngan thi ghi trong 1
    lan write. Nhung van fsync de dong log khong bi mat khi may tat dot ngot — event-log la
    lop audit, mat dong cuoi la mat dung dau vet cua su co vua xay ra.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding=encoding, newline="\n") as f:
        f.write(text if text.endswith("\n") else text + "\n")
        f.flush()
        os.fsync(f.fileno())


def read_text(path, encoding="utf-8"):
    """Doc text, KHONG chet vi file khong phai UTF-8. Tra (text, loi_hay_None).

    errors='replace' co y: 1 file latin-1 lot vao repo truoc day lam validate.py chet bang
    UnicodeDecodeError va KHONG in finding nao — tuc Gate 0 va Gate 2 bien mat hoan toan,
    im lang. Doc duoc gan dung con hon khong doc duoc gi.
    """
    try:
        with open(path, encoding=encoding, errors="replace") as f:
            return f.read(), None
    except Exception as e:
        return None, str(e)


def load_json_or_die(path, what="file", code=2):
    """Doc JSON, thoat co thong bao ro rang neu thieu/hong — thay cho traceback tho.

    digest.py va resume.py truoc day json.load KHONG bao try: wbs.json hong thi nguoi dung
    nhan mot traceback Python thay vi mot cau noi ro phai sua gi.
    """
    if not os.path.exists(path):
        print(f"LOI: khong tim thay {what}: {path}", file=sys.stderr)
        sys.exit(code)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"LOI: {what} ({path}) khong phai JSON hop le — dong {e.lineno}, cot {e.colno}: "
              f"{e.msg}\n"
              f"     Neu day la wbs.json: KHONG sua tay de 'chua chay'. Kiem xem co file "
              f"'.wbs.json.tmp' con lai trong kernel/memory/ khong (dau hieu 1 lan ghi bi "
              f"dut giua duong) — neu co, doi chieu roi phuc hoi tu do.", file=sys.stderr)
        sys.exit(code)
    except Exception as e:
        print(f"LOI: khong doc duoc {what} ({path}) — {e}", file=sys.stderr)
        sys.exit(code)
