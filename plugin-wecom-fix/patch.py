#!/usr/bin/env python3
"""
fmode/plugin-wecom-fix/patch.py — WeCom 官方插件通用补丁 (v1, 2026-09-09)
修复官方 hermes wecom 插件四项接收缺陷:
  F1 入站媒体下载上限错配(出站20MB被用于入站, 大视频收不到) → INBOUND_MAX_BYTES=512MB
  F2 长文件名 [Errno 36] 写盘失败丢消息(CJK 标题 260+ 字符) → cache 截断 200 字节
  F3 视频消息无提取分支(单发/mixed/quote 三路径静默丢弃) → 三处补 video
  F4 chatrecord 合并转发不识别(空消息→模型道歉) + 批量图片CDN限流丢失(无重试无间隔)
     → chatrecord 文本提取 + 下载重试3次退避 + 每3张媒体0.3s间隔
用法: python3 patch.py [--check|--apply|--rollback]
幂等: 已应用的补丁自动跳过; --check 只报告; --rollback 用 .bak 还原
"""
import sys, shutil, py_compile
from pathlib import Path

MARK = "# FMODE-WECOM-FIX"
ADAPTER = "/opt/hermes/plugins/platforms/wecom/adapter.py"
BASE = "/opt/hermes/gateway/platforms/base.py"
VERSION = "1.0.0"

def _read(p): return Path(p).read_text(encoding="utf-8")

def _write(p, t):
    Path(p).write_text(t, encoding="utf-8")
    py_compile.compile(p, doraise=True)

def _bak(p):
    bak = p + ".fmode-fix-bak"
    if not Path(bak).exists():
        shutil.copy2(p, bak)

# ---------------- F1: INBOUND_MAX_BYTES ----------------
def f1(t):
    if "INBOUND_MAX_BYTES" in t: return t, "skip"
    old = "ABSOLUTE_MAX_BYTES = FILE_MAX_BYTES"
    new = (old + "\n# FMODE-WECOM-FIX F1: inbound media cap (outbound 20MB cap must not gate inbound)\nINBOUND_MAX_BYTES = 512 * 1024 * 1024")
    t = t.replace(old, new, 1)
    # 两处入站下载改用新上限
    t = t.replace("self._download_remote_bytes(url, max_bytes=ABSOLUTE_MAX_BYTES)",
                  "self._download_remote_bytes(url, max_bytes=INBOUND_MAX_BYTES)")
    return t, "applied"

# ---------------- F2: 文件名截断 ----------------
def f2(t):
    if "max_name_bytes" in t: return t, "skip"
    old = '''    safe_name = safe_name.replace("\\x00", "").strip()
    if not safe_name or safe_name in {".", ".."}:
        safe_name = "document"
    cached_name = f"doc_{uuid.uuid4().hex[:12]}_{safe_name}"'''
    new = '''    safe_name = safe_name.replace("\\x00", "").strip()
    if not safe_name or safe_name in {".", ".."}:
        safe_name = "document"
    # FMODE-WECOM-FIX F2: filename component <=255 BYTES; truncate at UTF-8 boundary
    max_name_bytes = 200
    raw_bytes = safe_name.encode("utf-8")
    if len(raw_bytes) > max_name_bytes:
        truncated = raw_bytes[:max_name_bytes]
        while truncated:
            try:
                safe_name = truncated.decode("utf-8") + "…"
                break
            except UnicodeDecodeError:
                truncated = truncated[:-1]
        else:
            safe_name = "document"
    cached_name = f"doc_{uuid.uuid4().hex[:12]}_{safe_name}"'''
    if old not in t: return t, "MISS"
    return t.replace(old, new, 1), "applied"

# ---------------- F3: video 三路径 ----------------
def f3(t):
    if 'msgtype == "video"' in t: return t, "skip"
    c = 0
    o1 = '''                if item_type == "image" and isinstance(item.get("image"), dict):
                    refs.append(("image", item["image"]))'''
    n1 = o1 + '''
                if item_type == "video" and isinstance(item.get("video"), dict):
                    refs.append(("video", item["video"]))  # FMODE-WECOM-FIX F3'''
    if o1 in t: t = t.replace(o1, n1, 1); c += 1
    o2 = '''            if isinstance(body.get("image"), dict):
                refs.append(("image", body["image"]))'''
    n2 = o2 + '''
            if msgtype == "video" and isinstance(body.get("video"), dict):
                refs.append(("video", body["video"]))  # FMODE-WECOM-FIX F3'''
    if o2 in t: t = t.replace(o2, n2, 1); c += 1
    o3 = '''        elif quote_type == "file" and isinstance(quote.get("file"), dict):
            refs.append(("file", quote["file"]))'''
    n3 = '''        elif quote_type == "video" and isinstance(quote.get("video"), dict):
            refs.append(("video", quote["video"]))  # FMODE-WECOM-FIX F3
''' + o3
    if o3 in t: t = t.replace(o3, n3, 1); c += 1
    return t, f"applied({c}/3)" if c == 3 else f"PARTIAL({c}/3)"

# ---------------- F4: chatrecord + 重试 + 限流间隔 ----------------
def f4(t):
    out = []
    if 'elif msgtype == "chatrecord":' not in t:
        anchor = '''                    if content:
                        text_parts.append(content)
        else:'''
        rep = '''                    if content:
                        text_parts.append(content)
        elif msgtype == "chatrecord":
            # FMODE-WECOM-FIX F4: merged-forward record — extract title + sub-items
            cr = body.get("chatrecord") if isinstance(body.get("chatrecord"), dict) else {}
            _ti = str(cr.get("title") or "").strip()
            if _ti: text_parts.append(f"[合并转发] {_ti}")
            _its = cr.get("record_items") or cr.get("item") or cr.get("messages") or []
            if isinstance(_its, list):
                for _i, _s in enumerate(_its[:50], 1):
                    if not isinstance(_s, dict): continue
                    _st = str(_s.get("msgtype") or "").lower()
                    _nk = str(_s.get("nickname") or "").strip()
                    _px = f"{_i}. {_nk}:" if _nk else f"{_i}."
                    if _st == "text":
                        _b = _s.get("text") if isinstance(_s.get("text"), dict) else {}
                        _c = str(_b.get("content") or "").strip()
                        if _c: text_parts.append(f"{_px} {_c[:500]}")
                    elif _st in ("image", "video", "file", "voice"):
                        _lb = {"image": "[图片]", "video": "[视频]", "file": "[文件]", "voice": "[语音]"}[_st]
                        _b = _s.get(_st) if isinstance(_s.get(_st), dict) else {}
                        _fn = str(_b.get("filename") or _b.get("name") or "").strip()
                        text_parts.append(f"{_px} {_lb}{(' ' + _fn) if _fn else ''}")
        else:'''
        if anchor in t:
            t = t.replace(anchor, rep, 1); out.append("chatrecord")
    if "for attempt in range(3)" not in t:
        oldB = '''        try:
            raw, headers = await self._download_remote_bytes(url, max_bytes=INBOUND_MAX_BYTES)
        except Exception as exc:
            logger.debug("[%s] Failed to download %s from %s: %s", self.name, kind, url, exc)
            return None'''
        newB = '''        raw = headers = None
        last_exc = None
        for attempt in range(3):  # FMODE-WECOM-FIX F4: retry w/ CDN throttle backoff
            try:
                if attempt:
                    import asyncio as _aio
                    await _aio.sleep(0.5 * attempt * 1.5)
                raw, headers = await self._download_remote_bytes(url, max_bytes=INBOUND_MAX_BYTES)
                break
            except Exception as exc:
                last_exc = exc
                logger.debug("[%s] Download attempt %d failed for %s: %s", self.name, attempt + 1, kind, exc)
        if raw is None:
            logger.warning("[%s] Failed to download %s after retries from %s: %s", self.name, kind, url, last_exc)
            return None'''
        if oldB in t:
            t = t.replace(oldB, newB, 1); out.append("retry")
    if "_ref_idx" not in t:
        oldC = '''        for kind, ref in refs:
            cached = await self._cache_media(kind, ref)'''
        newC = '''        for _ref_idx, (kind, ref) in enumerate(refs):  # FMODE-WECOM-FIX F4
            if _ref_idx and _ref_idx % 3 == 0:
                import asyncio as _aio
                await _aio.sleep(0.3)  # CDN throttle guard for batch media
            cached = await self._cache_media(kind, ref)'''
        if oldC in t:
            t = t.replace(oldC, newC, 1); out.append("throttle")
    return t, "+".join(out) if out else "skip"

FIXES = {"F1": f1, "F2": f2, "F3": f3, "F4": f4}

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--apply"
    adapter = _read(ADAPTER)
    base = _read(BASE)
    report = {}
    if mode in ("--apply", "--check"):
        work = {"adapter": adapter, "base": base}
        for fid, fn in FIXES.items():
            for fname in ("adapter", "base"):
                if (fid in ("F1", "F3", "F4") and fname == "adapter") or (fid == "F2" and fname == "base"):
                    new, status = fn(work[fname])
                    if mode == "--apply" and status not in ("skip",):
                        if status != "MISS":
                            _bak(ADAPTER if fname == "adapter" else BASE)
                        work[fname] = new
                    report[f"{fname}:{fid}"] = status
        if mode == "--apply":
            _write(ADAPTER, work["adapter"]); _write(BASE, work["base"])
            print(f"[fmode-wecom-fix v{VERSION}] applied: {report}")
        else:
            print(f"[fmode-wecom-fix v{VERSION}] check: {report}")
    elif mode == "--rollback":
        for p in (ADAPTER, BASE):
            bak = p + ".fmode-fix-bak"
            if Path(bak).exists():
                shutil.copy2(bak, p); print(f"rolled back: {p}")
    print(f"done mode={mode}")

if __name__ == "__main__":
    main()
