# 六开源技能凭据链审计与修复任务书（用户钦点：sessionToken 自举）

## 背景（用户指出的架构级问题）
技能凭据可能依赖"读环境变量或 ~/.fmode/config.json 里的具体密钥"，但**最原始的凭据只有一个：FMODE Studio 用户登录后的 sessionToken**（存在 .fmode 配置里）。OBS 密钥、API key 等下游凭据**都应该用 sessionToken 动态获取**，不是用户预先配好的。

**权威凭据流**（fmode-studio/docs/obs-cdn/02-架构与路径划分.md §5.2 + 04-API设计.md）：
```
sessionToken → POST https://server.fmode.cn/api/storage/credentials
             → STS 临时凭证 {AK, SK, SecurityToken}（作用域限定用户 prefix，短时）
             → 客户端直传 OBS
```
另有：POST /api/storage/download-url（预签名 GET 临时下载）

## 审计范围（6 仓，逐一检查凭据获取逻辑）
1. **skill-storage**（★最严重）：uploader.mjs 只会找 obsutil 配置/bucket 名——**完全没有 sessionToken→STS 签发链**。必须补：
   - `resolveStorageConfig()` 第 0 级优先：读 `~/.fmode/config.json` 或 FMODE_SESSION_TOKEN 的 sessionToken
   - 用 sessionToken POST /api/storage/credentials 换 STS
   - STS 写入临时 obsutil 配置（或用 aws-cli/签名直传）完成上传，**STS 不落盘不进日志**
   - 保留原有 4 级作为回落（自建 OBS/已有 obsutil config 的用户）
2. **skill-agent-clone**：clone-runner 用 git token push——检查 sessionToken 能否换 git token（Gogs admin API 或 fmode API），能则补自举，不能则文档写明"git token 需要一次性初始化"并给初始化命令
3. **skill-listen / skill-vision**：检查 fmode token 解析链是否覆盖 sessionToken 源（.fmode config 的 sessionToken 字段）——listen/vision 用的 fmodeApiToken 若与 sessionToken 不同，需补"用 sessionToken 换 API token"的说明或逻辑
4. **skill-bypass-permission / skill-multi-branch**：无外部凭据依赖——确认无需改动，在 SKILL.md 注明"无凭据依赖"
5. **plugin-wecom-fix**：无凭据依赖——同上注明

## 统一规范（新增凭据解析第 0 级）
所有技能的凭据解析函数统一改为：
```
第0级(自举): sessionToken(环境变量 FMODE_SESSION_TOKEN 或 ~/.fmode/config.json 的 sessionToken/user.json)
           → 调 fmode API 换取所需下游凭据(STS/API token/...)
第1-4级: 原有链保留(显式配置/环境变量/项目配置/平台默认)——已配置的用户不受影响
```
- STS/临时凭据：内存持有，禁落盘禁日志
- 换取失败要给出明确报错："sessionToken 缺失或失效，请重新登录 FMODE Studio 或配置 FMODE_SESSION_TOKEN"

## 交付
- 每仓修复（代码+README 凭据章节更新：画出自举链路图）
- 每仓 version 递增 patch（0.2.1 等）+ commit + push Gogs + push GitHub（双源）
- 汇总：每个仓"凭据解析链（第0级自举+回落）"一段话
完成后只输出一行：CRED-FIX-DONE 修复仓=<列表> 自举链=<storage STS/listen/vision/clone说明> 双推=<6/6>
