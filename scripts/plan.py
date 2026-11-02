#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 config/packages.yml 解析成构建计划 /tmp/plan.json。

输入环境变量：
    PKG       apk | ipk          —— 当前版本的包管理格式
    BRANCH    openwrt-25.12 等   —— 用于替换 feed 地址里的 {branch}
    PROFILE   flash 大小标签（仅记录，不影响解析）

分组开关（缺省 true）：ENABLE_PROXY / ENABLE_MONITOR / ENABLE_DOCKER

输出 /tmp/plan.json：
    {
      "pkg": "ipk",
      "branch": "openwrt-24.10",
      "packages": ["curl", ...],          # 最终 PACKAGES 列表（含 -xxx 移除项）
      "feeds": [{"name","url","key"}],    # 只含当前包格式可用的源
      "releases": [{"package","repo","tag","required"}]  # 只含本次真正要装的
    }
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONF = os.path.join(ROOT, "config", "packages.yml")
OUT = "/tmp/plan.json"


def die(msg):
    sys.stderr.write("::error::%s\n" % msg)
    sys.exit(1)


def flag(name, default="true"):
    return str(os.environ.get(name, default)).strip().lower() in ("1", "true", "yes", "on")


try:
    import yaml
except ImportError:
    die("缺少 PyYAML，请先执行 pip3 install pyyaml")


def main():
    if not os.path.exists(CONF):
        die("找不到配置文件 %s" % CONF)

    with open(CONF, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}

    pkg = os.environ.get("PKG", "ipk").strip()
    branch = os.environ.get("BRANCH", "openwrt-24.10").strip()
    if pkg not in ("apk", "ipk"):
        die("PKG 只能是 apk 或 ipk，收到 %r" % pkg)

    # ---- 1. 收集包名 --------------------------------------------------------
    packages = []

    def add(items):
        for it in items or []:
            name = str(it).strip()
            if name:
                packages.append(name)

    add(cfg.get("base"))

    groups = cfg.get("groups") or {}
    enabled_groups = []
    for gname, items in groups.items():
        if flag("ENABLE_" + str(gname).upper().replace("-", "_")):
            add(items)
            enabled_groups.append(gname)

    add(cfg.get("extra"))

    # 去重但保持顺序（"-pkg" 和 "pkg" 视为不同字符串，保持原样）
    seen, ordered = set(), []
    for p in packages:
        if p not in seen:
            seen.add(p)
            ordered.append(p)
    packages = ordered

    # ---- 2. feeds -----------------------------------------------------------
    feeds = []
    for f in cfg.get("feeds") or []:
        if not isinstance(f, dict):
            continue
        name = str(f.get("name") or "").strip()
        url = f.get("apk") if pkg == "apk" else f.get("ipk")
        key = f.get("apk_key") if pkg == "apk" else f.get("ipk_key")
        if not url:
            continue  # 这个源在当前包格式下不启用
        feeds.append({
            "name": name or url,
            "url": str(url).replace("{branch}", branch),
            "key": str(key or "").replace("{branch}", branch),
        })

    # ---- 3. GitHub release 插件 --------------------------------------------
    wanted = set(p for p in packages if not p.startswith("-"))
    releases = []
    for r in cfg.get("github_releases") or []:
        if not isinstance(r, dict):
            continue
        name = str(r.get("package") or "").strip()
        if not name or name not in wanted:
            continue
        releases.append({
            "package": name,
            "repo": str(r.get("repo") or "").strip(),
            "tag": str(r.get("tag") or "latest").strip(),
            "required": bool(r.get("required", False)),
        })

    plan = {
        "pkg": pkg,
        "branch": branch,
        "groups": enabled_groups,
        "packages": packages,
        "feeds": feeds,
        "releases": releases,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, ensure_ascii=False, indent=2)

    print("包格式      : %s" % pkg)
    print("分支        : %s" % branch)
    print("启用分组    : %s" % (", ".join(enabled_groups) or "(无)"))
    print("包总数      : %d" % len(packages))
    print("第三方源    : %s" % (", ".join(f["name"] for f in feeds) or "(无)"))
    print("release 插件: %s" % (", ".join(r["package"] for r in releases) or "(无)"))
    print("PACKAGES    : %s" % " ".join(packages))


if __name__ == "__main__":
    main()
