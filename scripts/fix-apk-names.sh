#!/bin/bash
# =============================================================================
#  规范化 packages/ 目录下的 apk 文件名
# =============================================================================
#  apk（25.12+）要求包文件名严格是 <包名>-<版本>.apk，且版本号不能含下划线、
#  不能含多点号。上游 GitHub release 里的产物经常是：
#      bandix-0.12.12-r1_x86_64.apk          带架构后缀
#      luci-app-bandix-0.12.12-r5_all.apk    带 all 后缀
#      luci-i18n-bandix-zh-cn-26.300.03255.108369b-r5_all.apk
#                                          版本里混进了 git 提交号（点号分隔）
#  直接丢进 ImageBuilder 会被 apk 判为非法包名，表现为
#  "package mentioned in index not found"。这里统一修掉。
#
#  用法: fix-apk-names.sh [packages 目录]
# =============================================================================
set -euo pipefail

DIR="${1:-packages}"
if [ ! -d "$DIR" ]; then
  echo "  (目录 $DIR 不存在，跳过 apk 改名)"
  exit 0
fi

cd "$DIR"
shopt -s nullglob

changed=0
for f in *.apk; do
  base="${f%.apk}"
  orig="$base"

  # 1) 去掉上游附加的架构后缀
  case "$base" in
    *_x86_64) base="${base%_x86_64}" ;;
    *_all)    base="${base%_all}"    ;;
  esac

  # 2) 版本号里形如 26.300.03255.108369b 的 git 提交段，点号改波浪号
  #    apk 版本语法里 ~ 表示"低于"，正好符合提交号段的语义
  base="$(printf '%s' "$base" | sed -E \
    's/([0-9])\.([0-9a-f]{6,})([-.])/\1~\2\3/g; s/([0-9])\.([0-9a-f]{6,})$/\1~\2/')"

  if [ "$base" != "$orig" ]; then
    mv -f "$f" "$base.apk"
    echo "  rename  $f  ->  $base.apk"
    changed=1
  fi
done

if [ "$changed" -eq 0 ]; then
  echo "  apk 文件名无需调整"
fi
