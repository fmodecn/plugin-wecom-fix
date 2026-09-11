# plugin-wecom-fix · 企微官方插件通用补丁包

> 修复 Hermes 官方 wecom 插件的四项接收缺陷（2026-09-09 淬炼自真实翻车：55 分钟视频收不到/合并转发被拒/批量图片丢失/长文件名 Errno 36）
> 适用：所有装有官方 wecom 插件的 agent-node 容器（全集群数字生命）

## 修复清单

| # | 缺陷 | 症状 | 修复 |
|---|---|---|---|
| F1 | 入站下载上限错配 | 用户发大视频（>20MB）收不到 | 新增 `INBOUND_MAX_BYTES=512MB`，出站 20MB 上限不再误伤入站 |
| F2 | 长文件名写盘失败 | 长中文标题文件转发丢消息（Errno 36） | 缓存文件名 200 字节 UTF-8 安全截断 |
| F3 | 视频消息无提取分支 | 单发/组合/引用视频全部静默丢弃 | 三路径补 video 提取 |
| F4 | 合并转发不识别+批量图片丢失 | 转发合并消息收到空消息（模型道歉"不支持此类消息"）；10+ 张图片只到 2-3 张 | chatrecord 文本提取（标题+逐条子消息）；下载重试 3 次+CDN 限流退避+每 3 张 0.3s 间隔 |

## 安装（存量数字生命）

```bash
# 1. 拉仓库
git clone https://git.fmode.cn/fmode/plugin-wecom-fix.git /tmp/plugin-wecom-fix
# 2. 预检
python3 /tmp/plugin-wecom-fix/patch.py --check
# 3. 应用（自动备份 .fmode-fix-bak）
python3 /tmp/plugin-wecom-fix/patch.py --apply
# 4. 重启 gateway 加载
docker exec <容器> bash -c "pkill -f gateway.run"   # supervisor 自动拉起
# 5. 验证
python3 /tmp/plugin-wecom-fix/patch.py --check   # 全部 skip=已生效
```

## 批量安装（全集群）

```bash
bash install-all.sh   # 遍历 R730 全部 agent-node 容器执行 1-5 步（见脚本）
```

## 新数字生命初始化自动打补丁

初始化 SOP（life-init-standard）在**步骤"插件装配"后**追加：

```bash
git clone https://git.fmode.cn/fmode/plugin-wecom-fix.git /tmp/plugin-wecom-fix && \
python3 /tmp/plugin-wecom-fix/patch.py --apply && \
rm -rf /tmp/plugin-wecom-fix
```

- `patch.py` 幂等（已应用自动 skip），初始化时重复执行无副作用
- 官方插件升级后补丁如失效：`--check` 会重新报 applied，重跑 `--apply` 即可

## 回滚

```bash
python3 patch.py --rollback   # 用 .fmode-fix-bak 还原两个原文件
```

## 验证清单（打完补丁必测）

1. 发一个 >20MB 视频 → 能收到并缓存
2. 转发一条合并消息 → 能复述内容（不是"不支持此类消息"）
3. 连续转发 10+ 张图片 → 全数到达
4. 转发长中文标题文件（60+ 字）→ 正常落盘

## 凭据

**本补丁包无凭据依赖**——不读不写任何 token/密钥/凭据文件，仅修改 Hermes 官方 wecom 插件源码中的消息处理逻辑。
