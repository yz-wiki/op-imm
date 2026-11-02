#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建前剔除下载失败的插件，避免 make image 报 "package mentioned in index not found"。

做法：config/packages.yml 里 required=false 的 GitHub release 插件，如果最终
没有落到 packages/ 目录里，就把它的包名从 PACKAGES 里去掉（官方源一般也没有
这些包，留着只会让构建失败）。

用法：prune.py [packages 目录]
输出：/tmp/packages.txt（空格分隔的最终包列表）
"""
import glob
import json
import os
import sys

PLAN = "/tmp/plan.json"
OUT = "/tmp/packages.txt"


def main():
    pkgdir = sys.argv[1] if len(sys.argv) > 1 else "packages"
    if not os.path.exists(PLAN):
        sys.stderr.write("::error::缺少 %s\n" % PLAN)
        sys.exit(1)

    with open(PLAN, encoding="utf-8") as fh:
        plan = json.load(fh)

    pkg = plan["pkg"]
    packages = plan["packages"]

    def have(name):
        for pat in ("%s-*.%s" % (name, pkg), "%s_*.%s" % (name, pkg)):
            if glob.glob(os.path.join(pkgdir, pat)):
                return True
        return False

    drop = set()
    for r in plan.get("releases", []):
        if r.get("required"):
            continue
        if not have(r["package"]):
            drop.add(r["package"])
            print("  剔除（本地没有安装包）: %s" % r["package"])

    kept = [p for p in packages if p not in drop]
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(" ".join(kept))

    print("  最终包数: %d（剔除 %d）" % (len(kept), len(drop)))


if __name__ == "__main__":
    main()
