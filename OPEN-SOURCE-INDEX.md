# Fmode 开源技能与插件清单（fmodecn 组织 · 2026-09-11）

> 7 个仓库 · Gogs（内网集群）+ GitHub fmodecn（公开）双源同步
> 所有仓库统一规范：README 多工具安装指南（Claude Code / Codex / Gemini CLI / WorkBuddy / Hermes）· 凭据走 `~/.fmode/config.json` + 环境变量多级解析（零密钥入库）· MIT License · SKILL.md frontmatter · 幂等可重装
> **给其他 Agent**：直接发仓库地址，AI 读 README 按自己工具的 Skill 规范安装。

---

## 1. skill-listen — AI 的耳朵 🎧
**作用**：录音/视频音轨转文字（讯飞 LFASR × Fmode 网关 `/api/listen/transcribe`）。中英多语种+方言、说话人分离、服务端计费（按音频分钟数）、讯飞凭据零下放。
**场景**：会议/采访/课程转写、视频抽音轨转写、多人对话整理。
- Gogs：`https://git.fmode.cn/fmode/skill-listen`
- GitHub：`https://github.com/fmodecn/skill-listen`
- 直用：`npx --yes fmode-listen@latest transcribe -- meeting.mp3`

## 2. skill-vision — AI 的眼睛 👁️
**作用**：图片/视频结构化视觉分析。**宿主多模态模型优先**（自动探测 Claude Code/Codex 配置，模型支持视觉就直接用，零额外成本），否则回落 Fmode API 的 `glm-5.3-flash`；支持单轮/多轮聚焦分析与结构化 JSON 输出。
**场景**：图片内容识别、视频逐帧分析、批量视觉素材处理。
- Gogs：`https://git.fmode.cn/fmode/skill-vision`
- GitHub：`https://github.com/fmodecn/skill-vision`

## 3. skill-storage — AI 的仓库管理员 📦
**作用**：二进制大文件（图/音/视频/HTML 报告）上传对象存储（OBS/S3），本地磁盘零长期占用，上传即得公开分享链接；报告/课件发布即转发；支持批量 ACL 设置。
**场景**：报告发布、素材托管、公开外链。
- Gogs：`https://git.fmode.cn/fmode/skill-storage`
- GitHub：`https://github.com/fmodecn/skill-storage`

## 4. skill-agent-clone — 数字生命的备份灵魂 🧬
**作用**：把本地 Hermes 配置、SOUL、技能、记忆、会话记录按 **L1-L4 重要程度分级**同步到个人 Git 仓库（agent-<拼音>，自动建仓），增量 push、一键恢复——换机/容器重建时数字生命快速复活。密钥只记位置索引不入仓。
**场景**：数字生命备份、迁移、灾备。
- Gogs：`https://git.fmode.cn/fmode/skill-agent-clone`
- GitHub：`https://github.com/fmodecn/skill-agent-clone`

## 5. skill-bypass-permission — YOLO 模式体检器 ⚡
**作用**：校验并幂等修复 Agent 免确认自主执行配置（Hermes `approvals.mode=off`/`yolo`、Claude Code skip-permissions），改前自动备份，**已合规则一行 OK 静默通过**。
**场景**：数字生命初始化自检、集群标准化巡检、新工具接入配置。
- Gogs：`https://git.fmode.cn/fmode/skill-bypass-permission`
- GitHub：`https://github.com/fmodecn/skill-bypass-permission`

## 6. skill-multi-branch — 多任务工作框架 🌿
**作用**：**Hermes 负责沟通，专业任务派发执行层**（Claude Code/Codex/Agent profile）——任务书落盘协议、四态状态上报（ack→running→done/failed+心跳）、中断续跑、执行层纪律（含真实违规案例沉淀与验收方法）。内置 dispatch.sh 标准派发器。
**场景**：多任务并行、专业内容生产、先沟通后派发的响应模式。
- Gogs：`https://git.fmode.cn/fmode/skill-multi-branch`
- GitHub：`https://github.com/fmodecn/skill-multi-branch`

## 7. plugin-wecom-fix — 企微官方插件通用补丁 🔧
**作用**：修复官方 wecom 插件四项接收缺陷：①大视频收不到（入站 512MB 上限）②合并转发不识别（chatrecord 提取）③批量图片丢失（重试+限流退避）④长文件名 Errno 36（200 字节截断）。幂等 patch.py（--check/--apply/--rollback）+ 全集群批量安装脚本。
**场景**：数字生命初始化必装、企微机器人接收修复。
- Gogs：`https://git.fmode.cn/fmode/plugin-wecom-fix`
- GitHub：`https://github.com/fmodecn/plugin-wecom-fix`
- 安装：`git clone https://github.com/fmodecn/plugin-wecom-fix.git && python3 plugin-wecom-fix/patch.py --apply`

---

## 通用克隆安装（一段话发给任何 Agent）

> 克隆仓库后读 README，按你使用的工具（Claude Code / Codex / Gemini CLI / WorkBuddy / Hermes）对应的安装节操作：
> `git clone https://github.com/fmodecn/<仓库名>.git`

## 版本与迭代

- 双源同步：Gogs（内网日常）→ GitHub（公开发布）；版本迭代在 Gogs 进行后推 GitHub
- 后续新增技能默认遵循本清单规范（SKILL.md frontmatter / 零密钥 / 多工具 README / MIT）
