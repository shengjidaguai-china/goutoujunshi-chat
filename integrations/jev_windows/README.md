# 狗头军师 Jev Chat · Windows 源码适配

本目录基于 [jev-chat-windows](https://github.com/jev-chat/jev-chat-windows) 的窗口采集、RapidOCR、悬浮窗和微信草稿填入链路。新增了狗头军师的证据边界与自然口吻约束：先经 Jev 判断，再起草和排序；悬浮窗显示可见原文、可能意图、模型估计的判断把握、仍未知、下一步和停止条件。对方明确要求停止联系时，这轮不生成候选。

**状态：可构建预览 ZIP，尚未在 Windows 实机验收。** GitHub Actions 会提供预览包；它不代表已完成实机测试。Jev 判断失败时停止起草，不悄悄跳过判断。Mac 版的原文人工核对页、关系 K 线和关系档案管理页尚未移植到这里。OCR 可能认错说话人，填入前必须核对当前会话、收件人和文字；程序只填草稿，不自动发送。

要求 Windows 10 1903+ 或 Windows 11、微信 Windows 4.x、Python 3.10–3.12。源码运行：

```powershell
cd integrations\jev_windows
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

首次启动在设置页填写 Jev 判断接口与回复生成接口的 Key；密钥写入当前 Windows 用户的 `GOUTOU_JEV_API_KEY` 与 `GOUTOU_LLM_API_KEY` 环境变量，不会读取原版 Jev 安装时保存的 Key。其他设置写在本目录的 `config.json`，已被 Git 忽略。`build.bat` 可在 Windows 上生成可执行目录和 `dist/goutoujunshi-jev-chat-windows-preview.zip`；ZIP 解压后保持整个目录完整，从其中运行 `.exe`。数据使用见仓库根目录 [说明](../../PRIVACY.md)。

源码来源及第三方组件许可见本目录的 [LICENSE](LICENSE) 与 [NOTICE](NOTICE)。特别是 PySide6-Fluent-Widgets 会影响 Windows 发布包的许可条件；发布时须单独核对。
