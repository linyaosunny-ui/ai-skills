# -*- coding: utf-8 -*-
"""CDP 后台标签页公共模块

问题：Chrome 的 `/json/new` 会**强制激活**新建的标签页 —— 窗口被拉到最前、
标签切过去，用户打字会被打断。`POST /json/new` 在 Chrome 111+ 后也被移除。

方案：用 browser 级 WebSocket 调 CDP `Target.createTarget(background=True)`
建**后台**标签页，页面照常加载与取值，但**不抢焦点、不切标签、不弹窗**。

用法（替换原来的 `/json/new`）：
    from cdp_bg import new_bg_tab
    tab = new_bg_tab("https://example.com")   # 或指定 cdp_host
    ws = websocket.create_connection(tab["webSocketDebuggerUrl"], ...)

2026-11-04 新增（TWK072 首次使用后提取为公共模块，供 TWK040/050/053/054 等复用）。
"""
import json
import time
import urllib.parse
import urllib.request

import websocket

DEFAULT_CDP = "http://127.0.0.1:9222"


def _http_json(url, method="GET", timeout=15):
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8")
    try:
        return json.loads(raw)
    except Exception:
        return raw


def _browser_ws_url(cdp_host=DEFAULT_CDP):
    return _http_json(cdp_host + "/json/version")["webSocketDebuggerUrl"]


def create_bg_target(url, cdp_host=DEFAULT_CDP, timeout=30):
    """后台创建标签页，返回 targetId（不激活窗口）。

    失败返回 None。调用方拿 targetId 后可自行 attach，或轮询 /json/list
    找页面的 webSocketDebuggerUrl。
    """
    ws = websocket.create_connection(_browser_ws_url(cdp_host), timeout=timeout)
    try:
        ws.send(json.dumps({"id": 1, "method": "Target.createTarget",
                            "params": {"url": url, "background": True}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            ws.settimeout(max(1, deadline - time.time()))
            msg = json.loads(ws.recv())
            if msg.get("id") == 1:
                return (msg.get("result") or {}).get("targetId")
        return None
    finally:
        try:
            ws.close()
        except Exception:
            pass


def new_bg_tab(url, cdp_host=DEFAULT_CDP, expect_host=None, wait=1.0, retries=20,
               timeout=30):
    """后台建页并返回该页的 /json/list 条目（含 webSocketDebuggerUrl）。

    等价于原 `/json/new` 的返回值，但**不抢焦点** —— 只改这一处即可替换旧写法。

    expect_host: 用于在 /json/list 里定位新页签的 URL 子串（默认取 url 的 host）。
    """
    if expect_host is None:
        expect_host = urllib.parse.urlparse(url).netloc or url[:30]
    tid = create_bg_target(url, cdp_host=cdp_host, timeout=timeout)
    if not tid:
        return None
    for _ in range(retries):
        time.sleep(wait)
        try:
            pages = _http_json(cdp_host + "/json/list")
        except Exception:
            continue
        for t in pages if isinstance(pages, list) else []:
            if t.get("id") == tid or (t.get("type") == "page" and expect_host in t.get("url", "")):
                return t
    return None


# ---------------------------------------------------------------------------
# 焦点模拟（2026-11-04）
# BI 平台/BI 平台 等页面：处于后台时 document.visibilityState === 'hidden'，
# 页面不响应预览点击（结果区保留上一次查询的数字 → 取到过期数据）。
# 旧写法用 Page.bringToFront 解决，但那会把窗口拉到最前、抢用户焦点。
# 正确写法：Emulation.setFocusEmulationEnabled(true) —— 让页面「以为」自己在前台，
# 无需真的激活窗口。实测 hidden → visible。
# ---------------------------------------------------------------------------

FOCUS_EMULATION = {"method": "Emulation.setFocusEmulationEnabled", "params": {"enabled": True}}


def set_focus_emulation(call, enabled=True):
    """对某个会话开启/关闭焦点模拟，替代 Page.bringToFront（不抢屏）。

    call: 形如 call(method, params) 的回调（已绑定 session 或 page）。
    返回 True 表示成功（或已开启）；失败返回 False，调用方可自行决定是否回退。
    """
    try:
        r = call("Emulation.setFocusEmulationEnabled", {"enabled": bool(enabled)})
        return not (isinstance(r, dict) and r.get("error"))
    except Exception:
        return False
