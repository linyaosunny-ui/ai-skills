#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
edit_tags.py — 安全改待办工具任务标签（读→合并→写回→校验）。

用法：
  python3 edit_tags.py --project <pid> --task <tid> --add "示例标签,1-工作"
  python3 edit_tags.py --project <pid> --task <tid> --remove "9_1-元标签"
  python3 edit_tags.py --project <pid> --task <tid> --set "1-工作,示例标签"   # 显式覆盖（危险，需 --force）
"""
import json, sys, argparse, urllib.request, pathlib

CONFIG = pathlib.Path.home() / ".config" / "dida-cli" / "config.json"
BASE = "https://api.dida365.com/open/v1"

def _req(method, path, body=None):
    cfg = json.load(open(CONFIG))
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method,
        headers={"Authorization": "Bearer " + cfg["access_token"],
                 "Content-Type": "application/json; charset=utf-8"})
    raw = urllib.request.urlopen(r, timeout=30).read().decode("utf-8")
    return json.loads(raw) if raw.strip() else {}

def get_task(pid, tid):
    # 先查未完成（project data）；查不到再查已完成（/task/completed，POST）。
    # 坑：/project/{id}/data 只返回未完成任务，已完成任务的标签改不了。
    try:
        d = _req("GET", f"/project/{pid}/data")
        for t in (d.get("tasks") or []):
            if t["id"] == tid:
                return t
    except Exception:
        pass
    import datetime
    frm = (datetime.datetime.utcnow() - datetime.timedelta(days=365)).strftime("%Y-%m-%dT00:00:00Z")
    to = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).strftime("%Y-%m-%dT23:59:59Z")
    try:
        done = _req("POST", "/task/completed", {"startDate": frm, "endDate": to})
        if isinstance(done, dict):
            done = done.get("tasks") or []
        for t in done:
            if t["id"] == tid:
                return t
    except Exception:
        pass
    raise SystemExit(f"未找到任务 {tid}（未完成/已完成都查过了）")

def update_tags(pid, tid, tags, title=None):
    body = {"id": tid, "projectId": pid, "tags": tags}
    if title is not None:
        body["title"] = title
    return _req("POST", f"/task/{tid}", body)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--add", default="")
    ap.add_argument("--remove", default="")
    ap.add_argument("--set", default="")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    t = get_task(a.project, a.task)
    cur = [x for x in (t.get("tags") or []) if x]
    print(f"任务：{t.get('title')}")
    print(f"现有标签：{cur}")

    if a.set:
        if not a.force:
            raise SystemExit("--set 是显式覆盖，必须加 --force（避免误删标签）")
        new = [x.strip() for x in a.set.split(",") if x.strip()]
    else:
        add = [x.strip() for x in a.add.split(",") if x.strip()]
        rm  = [x.strip() for x in a.remove.split(",") if x.strip()]
        new = [x for x in cur if x not in rm]
        for x in add:
            if x not in new:
                new.append(x)

    if new == cur:
        print("无变化，跳过写入。")
        return
    print(f"合并后   ：{new}")

    update_tags(a.project, a.task, new)

    # 回读校验
    t2 = get_task(a.project, a.task)
    got = [x for x in (t2.get("tags") or []) if x]
    ok = sorted(got) == sorted(new)
    print(f"写回校验 ：{got}  → {'✅ 通过' if ok else '❌ 不一致'}")
    # 四证核对：原标签不丢
    lost = [x for x in cur if x not in got and x not in (a.remove.split(',') if a.remove else [])]
    if lost:
        print(f"⚠️ 丢失原标签：{lost}（非预期删除）")
    sys.exit(0 if ok and not lost else 1)

if __name__ == "__main__":
    main()
