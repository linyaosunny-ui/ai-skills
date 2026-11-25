#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_doc_period.py — 协作平台文档数据周期合规检查（确定性检查）

依据：《协作平台文档数据呈现标准 v2》（report-doc-standard-workflow/references/）
  §1 周期必须显眼（文档开头 + 各数据块）
  §2 周期全篇一致（跨周期对比须在开头声明）
本脚本只做数据周期检查；表格 / 图 / 重点标注的呈现审核见标准 §4-§5。

用法：
    python3 check_doc_period.py <文档路径> [--json] [--skip-non-data]
支持 .md / .html / .htm / .txt；HTML 会先去标签。

**适用范围**：带数据的文档（汇报 / 简报 / 专题分析 / 周报）。规范、流程、话术、清单类文档不必运行；
批量扫目录时加 `--skip-non-data` 跳过「无日期区间且无『数据』字样」的文件（默认不跳过，宁可多报不漏报）。

输出：逐项 Pass/Fail 明细 + 退出码（0=通过，1=不通过，2=文件不可读）
"""
import argparse
import json
import os
import re
import sys

DATE = r"(?:\d{4}\s*[-/年]\s*)?\d{1,2}\s*[-/月]\s*\d{1,2}\s*日?"
RANGE_SEP = r"(?:~|～|—|-|－|至|到)"
RANGE_RE = re.compile(rf"({DATE})\s*{RANGE_SEP}\s*({DATE})")
# 「数据周期：xxx」这类显式标注行
LABEL_RE = re.compile(r"(数据周期|统计周期|数据区间|统计区间|数据窗口|口径周期|数据截止)")
# 跨周期对比声明
COMPARE_RE = re.compile(r"(对比|比较|vs|VS|环比|同比)")
# 不含具体日期的相对时间
VAGUE_RE = re.compile(r"(近期|最新|最近|本月|上月|月初|月末|截至今日|截至目前|至今)")


def strip_html(text: str) -> str:
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return text


def norm_date(tok: str, default_year: int = 0):
    """把 '2026-08-01' / '8/1' / '8月1日' 归一为 (y, m, d)；缺年份用 default_year。"""
    tok = tok.strip().rstrip("日")
    nums = re.findall(r"\d+", tok)
    if len(nums) >= 3:
        return (int(nums[0]), int(nums[1]), int(nums[2]))
    if len(nums) == 2:
        return (default_year, int(nums[0]), int(nums[1]))
    return None


def load_lines(path: str):
    if not os.path.isfile(path):
        return None
    raw = open(path, "r", encoding="utf-8", errors="replace").read()
    if path.lower().endswith((".html", ".htm")):
        raw = strip_html(raw)
    lines = [ln.strip() for ln in raw.splitlines()]
    return [ln for ln in lines if ln]


def has_data_trace(lines):
    """是否含数据痕迹：出现日期区间，或出现「数据」字样。

    仅用于 --skip-non-data 批量场景；默认不跳过，宁可多报不漏报。
    """
    text = "\n".join(lines)
    return bool(RANGE_RE.search(text)) or ("数据" in text)


def check(path: str, skip_non_data: bool = False):
    lines = load_lines(path)
    if lines is None:
        return None

    if skip_non_data and not has_data_trace(lines):
        return {
            "path": path,
            "ok": True,
            "skipped": True,
            "results": [("S 适用范围", "SKIP", "无数据痕迹（无日期区间且无「数据」字样），跳过")],
            "periods": [],
        }

    head = lines[:15]
    head_text = "\n".join(head)
    full_text = "\n".join(lines)

    # 抽取所有区间
    ranges = []
    for ln in lines:
        for m in RANGE_RE.finditer(ln):
            a = norm_date(m.group(1))
            b = norm_date(m.group(2))
            if a and b:
                ranges.append({"line": ln[:120], "start": a, "end": b})

    # 归一化去重（忽略年份缺失）
    def key(r):
        return (r["start"][1], r["start"][2], r["end"][1], r["end"][2])

    periods = []
    seen = set()
    for r in ranges:
        k = key(r)
        if k not in seen:
            seen.add(k)
            periods.append(r)

    has_label = bool(LABEL_RE.search(full_text))
    head_has_period = bool(RANGE_RE.search(head_text)) or bool(LABEL_RE.search(head_text))
    head_has_compare = bool(COMPARE_RE.search(head_text))
    vague = sorted(set(VAGUE_RE.findall(full_text)))

    results = []
    ok = True

    # A. 是否标注了周期
    if not ranges and not has_label:
        results.append(("A 周期标注", "FAIL", "全文未发现任何数据周期（日期区间 / 「数据周期」标注）"))
        ok = False
    else:
        results.append(("A 周期标注", "PASS", f"发现 {len(ranges)} 处日期区间，去重后 {len(periods)} 个周期"))

    # B. 开头显眼位置是否有周期
    if head_has_period:
        results.append(("B 开头显眼标注", "PASS", "文档开头 15 行内出现周期或「数据周期」标注"))
    else:
        results.append(("B 开头显眼标注", "FAIL", "开头 15 行内未见周期标注（周期不能只出现在文末口径说明）"))
        ok = False

    # C. 周期是否一致
    if len(periods) <= 1:
        results.append(("C 周期一致性", "PASS", "全篇单一周期"))
    else:
        if head_has_compare:
            results.append(("C 周期一致性", "PASS", f"存在 {len(periods)} 个周期，但开头已声明对比关系（允许）"))
        else:
            desc = "；".join(
                f"{r['start'][1]}/{r['start'][2]}~{r['end'][1]}/{r['end'][2]}" for r in periods[:6]
            )
            results.append(("C 周期一致性", "FAIL", f"全篇出现 {len(periods)} 个不同周期（{desc}），开头未声明对比"))
            ok = False

    # D. 相对时间表述
    if vague:
        results.append(("D 相对时间", "FAIL", "出现不含具体日期的表述：" + "、".join(vague)))
        ok = False
    else:
        results.append(("D 相对时间", "PASS", "未发现「近期/最新/本月」类模糊表述"))

    return {"path": path, "ok": ok, "results": results, "periods": periods}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--skip-non-data",
        action="store_true",
        help="批量场景：无数据痕迹的文档跳过（默认不跳过，避免漏报）",
    )
    args = ap.parse_args()

    r = check(args.path, skip_non_data=args.skip_non_data)
    if r is None:
        print(f"Fail\t文件不可读：{args.path}")
        return 2

    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        tag = "Skip" if r.get("skipped") else ("Pass" if r["ok"] else "Fail")
        print(f"{tag}\t{r['path']}")
        for name, st, msg in r["results"]:
            print(f"  [{st}] {name}: {msg}")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
