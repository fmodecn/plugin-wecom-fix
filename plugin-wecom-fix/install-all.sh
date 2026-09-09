#!/bin/bash
# install-all.sh — 全集群 agent-node 容器批量安装 wecom-fix 补丁
# 用法: bash install-all.sh [容器名...]
# 缺省遍历 R730 上全部 fmode agent-node* 容器
set -u
CONTAINERS="${*:-agent-node agent-node-tuye agent-node-xinting}"
REPO_URL="https://git.fmode.cn/fmode/plugin-wecom-fix.git"
FIX_DIR="/tmp/plugin-wecom-fix"
REPO_LOCAL="$(cd "$(dirname "$0")" && pwd)"

# 打包本地补丁目录(免 git 依赖: 直接 tar 投递)
TARBALL="/tmp/wecom-fix.tar.gz"
tar -czf "$TARBALL" -C "$REPO_LOCAL" patch.py README.md 2>/dev/null || { echo "打包失败"; exit 1; }
B64=$(base64 -w0 "$TARBALL")

for C in $CONTAINERS; do
  echo "=== $C ==="
  # 投递补丁
  docker exec "$C" bash -c "echo $B64 | base64 -d > /tmp/wecom-fix.tar.gz && mkdir -p $FIX_DIR && tar -xzf /tmp/wecom-fix.tar.gz -C $FIX_DIR" || { echo "  投递失败"; continue; }
  # 预检+应用
  docker exec "$C" python3 "$FIX_DIR/patch.py" --check 2>&1 | tail -2
  docker exec "$C" python3 "$FIX_DIR/patch.py" --apply 2>&1 | tail -2
  # 重启 gateway(独立 shell, supervisor 自动拉起)
  docker exec "$C" bash -c "pkill -f gateway.run; echo restarted" 2>&1 | tail -1
  echo ""
done
echo "全部完成。逐容器验证: python3 $FIX_DIR/patch.py --check"
