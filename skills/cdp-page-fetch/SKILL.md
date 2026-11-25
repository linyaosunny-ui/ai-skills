---
name: "cdp-page-fetch"
description: "裸 CDP（9222）+ Runtime.evaluate 在「已登录页面」里直接调内部接口取数，复用登录态、不依赖 API token 发放。含 iframe native fetch + JS 层硬超时两条铁律与排错对照表。触发词：CDP 取数、复用登录态取数、页面内调接口、9222、Runtime.evaluate、页面 fetch 挂死。"
---

# cdp-page-fetch — 裸 CDP 页面内取数（可靠版）

## 何时用

- 数据只在内网平台页面上，**没有开放 API、拿不到长期 token**，只能借用浏览器登录态
- 已有一个常驻登录的调试浏览器：`msedge --remote-debugging-port=9222 --user-data-dir=...`
- 需要按日期/维度**批量**拉接口数据（账单流水、任务清单、余额、报表统计）

**不适用**：① 有正式 API 的（优先 `dip-query-service` / `finebi-sql-query` / 内部数据平台）；② 需要点击、填表、翻页交互的 UI 流程（用 `chrome-automation` 的 DevTools MCP 或 `agent-browser`）。
本 skill 讲的是**直接对内网接口发 POST** 的那条路，比 UI 自动化快 1~2 个数量级。

## 铁律：页面内 HTTP 必须同时满足两个条件，缺一必挂

### ① 走「临时 iframe 的 native fetch」，不能用 `window.fetch`

平台页可能把 `window.fetch` 换成监控 SDK 的包装，**主上下文里 fetch 任何 URL 都挂死**（连 `data:` URL 都不返回）→ 表现为 CDP `Runtime.evaluate` 超时。临时 iframe 里的 native fetch 是干净的，用完即删。

### ② 每个请求必须带 JS 层硬超时（`AbortController`）

iframe fetch 也会**「网络层悬停」**——请求发出后服务端不响应，**promise 永不 settle**。此时 JS 侧若没超时兜底，就只能干等满 `Runtime.evaluate` 的 timeout 上限，并留下**孤儿 iframe**。

**判据**：页面主线程其实是健康的（`document.title`/`readyState` 0.01s 返回），只有那一个请求僵着 → 看到「evaluate 卡住但页面探活正常」就要想到这一条，别误判成页面卡死。

**跨 realm 细节**：`AbortController` 必须取自 **iframe 自己的 realm**（`new (f.contentWindow.AbortController)()`）；拿父页面的 controller 配 iframe 的 `fetch` 会过不了跨 realm 品牌校验。

## 可复制的 prelude

```js
const API = "<接口前缀，如 https://api-boss-public.example.com/xxx/api>";
const KEY = "<localStorage 里 token 的 key>";
function tk(){ const v = localStorage.getItem(KEY); if(!v) return null;
  try{ const j = JSON.parse(v); return 'Bearer ' + ((j.body && j.body.raw) ? j.body.raw : (j.body || j)); }
  catch(e){ return 'Bearer ' + v; } }
function post(p, b, ms){
  ms = ms || 20000;
  // 清掉上次卡死留下的孤儿 iframe（无 src + display:none 即我们自己的标记）
  document.querySelectorAll('iframe').forEach(function(f){
    if(!f.getAttribute('src') && getComputedStyle(f).display === 'none') f.remove(); });
  const f = document.createElement('iframe'); f.style.display='none'; document.body.appendChild(f);
  const W = f.contentWindow, ff = W.fetch.bind(W), ctl = new W.AbortController();
  let to = null;
  const guard = new Promise(function(_, rej){ to = setTimeout(function(){
      try{ ctl.abort(); }catch(e){} rej(new Error('TIMEOUT_' + ms + 'ms')); }, ms); });
  const req = ff(API + p, {method:'POST',
      headers:{'Content-Type':'application/json','Accept':'application/json', Authorization: tk()},
      body: JSON.stringify(b), signal: ctl.signal})
    .then(function(r){ return r.text().then(function(t){
      try{ return JSON.parse(t); }catch(e){ return {__raw: t.slice(0,300)}; } }); });
  req.catch(function(){});                       // 超时后 req 仍会 reject，挂空 handler 免报 unhandled
  return Promise.race([req, guard])
    .then(function(v){ clearTimeout(to); f.remove(); return v; })
    .catch(function(e){ clearTimeout(to); try{ f.remove(); }catch(_){}
      return {__fetch_err: String((e && e.message) || e).slice(0,200)}; });
}
```

调用方式（**不要忘了 `return`**，`awaitPromise` 才能拿到结果）：

```python
expr = "(function(){ " + PRELUDE + " return (async()=>{ /* await post(...) */ })() })()"
```

## Python 侧五条（都是踩过坑的）

1. **`ev()` 永远别抛 `SystemExit`**，用 `RuntimeError`。`SystemExit` 继承 `BaseException`，`except Exception` 抓不到 → 「单个组合失败」会升级成「整个进程终止」。
2. **CDP 读超时 + 一次重连重试**：`create_connection(..., timeout=15)` 后 `ws.settimeout(75)`，`recv()` 包在 try 里抛清晰错误；`call()` 捕获后**重建连接重试一次**。止损点从 290s 降到 75s。
3. **步骤级总时长预算**：给每步一个预算（如明细步 420s），到点就用**已落盘**的数据继续。否则一挂就撞满 orchestrator 的 `subprocess` 超时 → `TimeoutExpired` 直接判失败（还可能推一张假告警）。
4. **单个 evaluate 里串的请求数 ≤ 15 个**，多了就分块。一个 evaluate 里串 70 个请求（余额 + 23 账户 × 3 供应商），任何一次悬停都会把整批拖死；改成「每块 4 个单元（12 次请求）」后，单块卡死只损失那一块。
5. **token 每次调用前重读** `localStorage`（有效期可能只有几分钟，也可能变成十几小时；规则不变，别依赖具体值），剩余不足阈值就 `Page.reload` 刷新（reload 会杀死旧 ws，必须重连）。

## 取数落盘三条

- **边拉边落盘**：每成功一个 (日期, 供应商) 就合并写一次文件，单组合失败不清空已得数据。批量拉到最后一个组合才写盘 = 一断线全丢。
- **合并写，不要覆盖写**：后处理阶段把本轮结果**并入**已有文件；全失败时也不要写空文件。
- **配对型指标要加上游完整性闸门**：如「接通率 ρ = 接通数 / 下发数」，某日缺任一数据源就**整日不参与配对**并打 WARN，否则分母是全额、分子只有一家，指标会被静默压低（实测 0.634 → 0.514，派生量少算 24%）。

## 排错对照表

| 症状 | 根因 | 处置 |
|---|---|---|
| evaluate 挂满 290s / 600s 超时，页面探活正常 | 主上下文 `window.fetch` 被劫持 | 改 iframe native fetch（铁律①） |
| 改 iframe 后仍偶发挂满超时，`iframe_cnt` 多 1 | 请求网络层悬停，promise 不 settle | 加 JS 硬超时 + 清孤儿 iframe（铁律②） |
| 报 `TypeError: ... signal is not of type AbortSignal` | 用了父页面的 `AbortController` | 取 `f.contentWindow.AbortController` |
| 密集探测后突然大面积 `Failed to fetch` / 业务码 100004 | **临时频控**，不是接口劣化 | 放慢/重试即可自愈；别据此改架构 |
| 「页面报错但重试就好」 | 同上 | 关键步骤（取清单等）加 2~3 次重试 |
| 子步骤明明成功却走了降级分支 | 用 `out.startswith("{")` 判成功，但 stdout 前面还有进度行 | 从末行往前找 JSON；或要求「字典且含预期形态的键」 |

## 验收 / 回归（别只靠肉眼）

1. **悬停回归测试**：把 `API` 换成**不可路由地址**（如 `https://10.255.255.1/...`），调 `post(p, b, 3000)`；应在 3s 级返回 `{__fetch_err:'TIMEOUT_3000ms'}`，且事后 `document.querySelectorAll('iframe').length` 为 0。
   现成实现：`{WORKSPACE}/定时任务罗列/script_twk054/twk054_test_timeout.py`（改 `API` 后可直接复用）。
2. **页面健康探针**：一次性 evaluate 几个轻量表达式（`document.title` / `readyState` / `typeof window.fetch` / `iframe` 个数 / token 长度），0.0x 秒返回即说明「页面活着，问题在那个请求」。
3. **并发纪律**：同一浏览器页**同一时刻只允许一个会话驱动**。开跑前先看 `ps`/任务管理器里的 python 进程清单与目标步骤的日志，两个会话同跑会把彼此的落盘结果互相覆盖。

## 参考实现

`{WORKSPACE}/定时任务罗列/script_twk054/`（外呼平台取数：余额 / 任务 / 账单汇总 / 逐日明细 / 分战区花费，含全部上述加固）。同目录 `TWK054_外呼余额驱动下发量控制_任务描述.md` 的「本轮修掉的真问题」一节是这套规则的完整事故记录。

## 焦点抢夺专项修整（2026-11-04）

**背景**：CDP 复用浏览器时，若用 `/json/new` 建页或 `Page.bringToFront`，会把 Chrome 窗口
拉到最前、切走标签，用户在打字会被打断。

**两条红线**：

1. **建标签页** → 一律用后台建页（`cdp_bg.create_bg_target(url)` / `new_bg_tab(url)`），
   禁止 `/json/new`（Chrome 111+ 已移除该端点，且会抢焦点）。
2. **需要页面「在前台」才能响应**（BI 平台/BI 平台 预览点击等）→ 用
   `Emulation.setFocusEmulationEnabled(true)` 做**焦点模拟**，不要用
   `Page.bringToFront`（后者会真的把窗口拉到最前）。实测 `hidden → visible`。

**适用判定**：只有「页面因不可见而不响应交互」时才需要焦点模拟；纯取值/截图不需要。

**已修整文件**（均留回退开关，环境变量置 1 即恢复旧行为）：

| 文件 | 改动 | 回退开关 |
|---|---|---|
| `cdp-page-fetch/assets/cdp_bg.py` | 新增 `create_bg_target` / `new_bg_tab` / `set_focus_emulation` | — |
| `finebi-sql-query/scripts/finebi_batch_query.py` | 建页后台化 + `real_click` 焦点模拟 | `FINBI_FG=1` |
| `finebi-sql-query/scripts/finebi_sql_query.py` | `_bring_page_to_front` 焦点模拟 | `FINBI_FG=1` |
| `finebi-sql-query/scripts/finebi_dataset_update.py` | 建页后台化 + `front()` 焦点模拟 | `FINBI_FG=1` |
| `finebi-to-excel/scripts/finebi_to_excel.py` | `createTarget` 加 `background=True` | — |
| `rbtrace-query-to-md/scripts/workorder_query.py` | 建页后台化 + 焦点模拟 | — |
| `dip-permission-apply/scripts/dip_permission_apply.py` | 建页后台化 | — |
| `create-picture/scripts/doubao_web_image.py` | 建页后台化 + `_ensure_focus` 焦点模拟 | `DOUBAO_FG=1` |
| `定时任务罗列/script_twk040` `twk050` `twk053` `twk054` `twk072` | 见各任务文档 | `TWK054_FG_TAB=1` |

**验证**：小红书（后台建页取 44 条）、外呼平台（URL 正常加载）、BI 平台
（`hidden→visible`，页面标题正常）均实测未抢焦点。
