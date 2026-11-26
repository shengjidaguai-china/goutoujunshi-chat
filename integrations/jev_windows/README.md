# 狗头军师 · Windows 源码适配

本目录基于 [jev-chat-windows](https://github.com/jev-chat/jev-chat-windows) 的窗口采集、RapidOCR、悬浮窗和草稿填入链路。接入狗头军师的证据边界与自然口吻约束：先核对识别原文及说话人，再做策略判断、生成并排序候选；悬浮窗显示可能意图、模型估计的判断把握、已知事实、仍未知、下一步和停止条件。对方明确要求停止联系时，这轮不生成候选。**目标聊天应用可在设置页切换：微信（默认）或 QQ（QQNT 主面板内嵌形态）。**

**状态：可构建预览 ZIP。贡献者 @wstaery 在 PR #2 中报告 QQNT 路径已在一台 Windows 10 实机完成识别与填入验证；微信各版本的实机验收仍待进行。** GitHub Actions 会提供预览包；构建通过不代表所有聊天应用版本实机测试通过。策略可选 Jev 或 DeepSeek 官方；DeepSeek 独立整理证据，尝试以三次标签轮换的首 token 权重核对策略，无法稳定取得权重时明确标注不可用。候选百分比为本轮相对推荐权重，并非回复成功率。

使用流程：打开目标应用（微信或 QQ）的会话并保持窗口可见（QQ **只保留单聊**：用主面板内嵌聊天，独立聊天窗口暂不支持，切到群聊会提示跳过、切回好友自动恢复；换了窗口就重新拨一次「采集」开关，会自动重新找窗口接过去）；首次进入设置，选择目标聊天应用、策略与回复模型，配置 Key；识图可选本地 RapidOCR、DeepSeek 图片识别或 OpenRouter 图片识别。点「采集」会立刻显示当前窗口的会话；**采集中直接上滑翻出更早的消息，停稳后会自动把新露出的记录并入累计**（也可重拨一次「采集」强制重读）；核对弹窗里可以点「累计聊天记录」，合并后再次核对并确认分析。记录按对话先后顺序保留最近 60 条；手动修改与删除会保留。请小幅连续滚动、保留部分重叠；没有重叠的扫描默认按更早的历史处理，时间顺序仍需人工核对。云端识图会上传裁剪后的聊天区截图并可能计费。读取新消息后点「核对原文并分析」，逐行修正“我／对方”的归属和文字，再确认。结果页可选「详细分析」「更像我一点」，也可复制或填入候选草稿。K 线窗口内置五种走势并支持导入带 `timestamp,sender,message` 的聊天 CSV；图中展示消息方向净差，无法衡量关系质量。设置页可按会话保存阶段、目标和简短背景；完整聊天仅留在运行时内存。OCR 可能认错说话人，填入前还须确认当前会话、收件人和文字；程序不会自动发送。

要求 Windows 10 1903+ 或 Windows 11、微信 Windows 4.x 或 QQNT（QQ 9.x）、Python 3.10–3.12。源码运行：

```powershell
cd integrations\jev_windows
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

QQ 适配说明：按 QQNT 主面板标定（浅色皮肤、100% 显示缩放、默认列表宽度）；**只保留单聊**（切到群聊会提示跳过、切回好友自动恢复）；深色主题尽力兼容，独立聊天窗口与明显不合常规的窗口布局尚未覆盖。切换目标应用后采集会自动重启；QQ 或微信没打开时先打开主窗口再开启采集。

密钥写入当前 Windows 用户的 `GOUTOU_JEV_API_KEY`、`GOUTOU_DEEPSEEK_STRATEGY_KEY`、`GOUTOU_LLM_API_KEY` 和 `GOUTOU_OCR_API_KEY` 环境变量（按实际选择填写）；识图来源与回复来源相同时可以复用回复 Key。不会读取原版 Jev 安装时保存的 Key。其他设置写在本目录的 `config.json`，已被 Git 忽略。`build.bat` 可在 Windows 上生成可执行目录和 `dist/goutoujunshi-chat-windows-preview.zip`；ZIP 解压后保持整个目录完整，从其中运行 `.exe`。数据使用见仓库根目录 [说明](../../PRIVACY.md)。

源码来源及第三方组件许可见本目录的 [LICENSE](LICENSE) 与 [NOTICE](NOTICE)。特别是 PySide6-Fluent-Widgets 会影响 Windows 发布包的许可条件；发布时须单独核对。

持续集成：仓库的 GitHub Actions 启用后，推送会自动运行技能校验与三端构建（Windows / Android / Mac），构建产物在各 workflow 的 Artifacts 中下载。

本轮整合补充云端识图去重接口、QQ 群聊分析与填入拦截、记录时间顺序、微信／QQ 同名会话隔离和累计后确认的回归修复。关系资料按应用分别保存，原有微信资料继续兼容。源码合并不会自动替换 Release ZIP；QQ 支持请使用本轮 Actions 成功构建的 Windows Artifacts 或运行源码。

感谢 [@wstaery](https://github.com/wstaery) 通过 [PR #2](https://github.com/shengjidaguai-china/goutoujunshi-chat/pull/2) 贡献 QQNT 适配、采集稳定性改进及测试。
