<!-- README_SYNC: source=714af1db8a9814841c9aec26534a6aa2592829cc; updated=2026-10-18 -->

<p align="center">简体中文 · <a href="./README_EN.md">English</a></p>

<h1 align="center">狗头军师 Chat</h1>

<p align="center"><strong>聊天卡住时，帮你看清对话、理清下一步，写出更像自己的回复。</strong></p>

<p align="center">从<a href="https://github.com/shengjidaguai-china/goutoujunshi">狗头军师</a>延伸而来的聊天助手：读取可见对话或截图，核对后分析，再生成回复草稿。提供桌面悬浮窗、Android 悬浮助手与键盘，以及 iOS 键盘，发送始终由你决定。</p>

<p align="center">觉得有用，可以<a href="https://github.com/shengjidaguai-china/goutoujunshi-chat/stargazers">点一个 Star</a>，方便下次找到，也帮助更多人发现。</p>

<p align="center">
  <a href="https://github.com/shengjidaguai-china/goutoujunshi-chat/stargazers"><img src="https://img.shields.io/github/stars/shengjidaguai-china/goutoujunshi-chat?style=for-the-badge&amp;labelColor=263D35&amp;color=52796F&amp;logo=github&amp;logoColor=white" alt="Stars" height="24"></a>
  <a href="https://github.com/shengjidaguai-china/goutoujunshi-chat/releases"><img src="https://img.shields.io/github/v/release/shengjidaguai-china/goutoujunshi-chat?include_prereleases&amp;style=for-the-badge&amp;labelColor=263D35&amp;color=52796F&amp;logo=github&amp;logoColor=white" alt="Release" height="24"></a>
  <a href="https://github.com/shengjidaguai-china/goutoujunshi-chat/actions/workflows/validate.yml"><img src="https://img.shields.io/github/actions/workflow/status/shengjidaguai-china/goutoujunshi-chat/validate.yml?style=for-the-badge&amp;labelColor=263D35&amp;color=52796F&amp;logo=githubactions&amp;logoColor=white&amp;label=checks" alt="Checks" height="24"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-52796F?style=for-the-badge&amp;labelColor=263D35&amp;color=52796F" alt="License: MIT" height="24"></a>
</p>

## 能帮你做什么

- **看清对话**：区分已知事实、可能的意图和仍未知的信息，给出下一步与停止条件。
- **挑选回复**：比较候选的理由与代价，用「更像我一点」调整口吻。
- **带上关系背景**：结合当前对象、关系阶段和沟通目标生成建议。
- **回看聊天节奏**：导入聊天 CSV 查看 K 线，也可先体验五组示例。曲线反映消息方向的变化，不代表关系质量或爱意分数。

<a href="documentation/screenshots/product-overview-six.png"><img src="documentation/screenshots/product-overview-six.png" width="900" alt="桌面悬浮助手、分析建议、Android 设置与三种 iPhone 键盘界面的总览拼图"></a>

*基于截图的 AI 排版预览，点击放大；界面细节以原图为准。桌面分析为离线演示，判断把握为模型估计。*

<details>
<summary>查看原图与配置教程（8 张）</summary>

- **桌面端**：[悬浮助手](documentation/screenshots/overlay-in-wechat.png) · [分析建议](documentation/screenshots/analysis-detail-demo.png)
- **iPhone**：[本地打字](documentation/screenshots/ios-typing.jpg) · [读取截图](documentation/screenshots/ios-capture.jpg) · [核对原文](documentation/screenshots/ios-review.jpg)
- **配置截图**：[Mac 接口配置](documentation/design/provider-config-preview.png) · [Android 模型配置](documentation/guides/android-deepseek/images/02-DeepSeek判断与回复.png) · [Android 截图设置](documentation/guides/android-deepseek/images/04-识图开关与截屏方式.png)

配置图为对应版本截图；Mac 接口图未包含后续新增的 OpenRouter 选项，请以使用说明为准。

</details>

## 选择你的平台

目前各端均为预览版，设备与聊天应用的兼容性仍需分别验证。

| 平台 | 获取与安装 | 当前支持与限制 |
| --- | --- | --- |
| **macOS** | [源码预览 ZIP](https://github.com/shengjidaguai-china/goutoujunshi-chat/releases/download/v0.1.8-preview/goutoujunshi-jev-chat-mac.zip) · [使用说明](integrations/jev_mac/README.md) | 微信读屏与草稿填入；需要 Python 3.12、uv，暂无签名 `.app`。解压后依次运行 `安装依赖.command`、`离线演示.command`、`启动.command`。 |
| **Windows** | [预览 ZIP](https://github.com/shengjidaguai-china/goutoujunshi-chat/releases/download/v0.1.8-preview/goutoujunshi-jev-chat-windows-preview.zip) · [使用说明](integrations/jev_windows/README.md) | Windows 10 1903+ / 11，微信 4.x；完整解压后运行 `.exe`。**QQNT 9.x 支持需使用新版源码或下方 Actions 构建**。 |
| **Android** | [悬浮助手 APK（0.1.8）](https://github.com/shengjidaguai-china/goutoujunshi-chat/releases/download/v0.1.8-preview/goutoujunshi-jev-chat-android-debug.apk) · [图文教程](documentation/guides/android-deepseek/README.md) · [键盘版 APK（0.1.9 预览）](https://github.com/shengjidaguai-china/goutoujunshi-chat/releases/download/v0.1.9-keyboard-preview/goutoujunshi-chat-android-keyboard-0.1.9-preview.apk) · [键盘安装](https://github.com/shengjidaguai-china/goutoujunshi-chat/blob/v0.1.9-keyboard-preview/integrations/jev_android/README.md#android-系统键盘019-keyboard-preview) | Android 11+；Soul 等应用可走手动截图流程，需按设备验证。**暂不支持微信**。 |
| **iOS** | [中文安装说明](integrations/jev_ios/README.md) · [English guide](integrations/jev_ios/README_EN.md) | iOS 16+；需在 Mac 上用 Xcode 编译、签名。支持本地拼音打字、截图识别与回复填入；暂无公开 IPA、TestFlight 或 App Store 下载。 |

Windows QQ 仅适配 QQNT 主面板内嵌单聊，以浅色皮肤、100% 缩放为基准；群聊与独立聊天窗口暂不支持。贡献者报告已在 Windows 10 上验证识别与填入。请从 [Actions 最新成功构建](https://github.com/shengjidaguai-china/goutoujunshi-chat/actions/workflows/platform-build.yml)下载对应 Windows Artifacts，或按使用说明运行源码；Release ZIP 不随源码更新自动替换。

版本说明与文件校验值见 [Releases](https://github.com/shengjidaguai-china/goutoujunshi-chat/releases/latest)。Android 调试包若签名不一致，需要卸载旧版再安装，卸载会清除本地数据。

## 开始一轮对话

1. **配置模型**：在设置中选择策略判断与回复服务，填写自己的 API Key。策略支持 Jev 或 DeepSeek，回复可用 DeepSeek 或 OpenRouter；具体选项见各平台说明。
2. **读取对话**：桌面端保持目标聊天窗口可见；Android 可用悬浮球截图，键盘版也可从「军师」截图或导入图片；iOS 导入截图、粘贴文字或使用截图快捷指令。
3. **核对并分析**：确认识别文字、「我／对方」、关系阶段和目标，再提交分析。
4. **选择并发送**：查看建议与候选，按需改写口吻；复制或填入草稿，核对收件人和内容后自行发送。

**权限与数据：** Mac 读屏需给启动终端授予「屏幕录制」权限，填入需「辅助功能」权限；Android 悬浮助手需要无障碍和悬浮窗权限，系统键盘可独立启用；iOS 键盘联网需允许完全访问。使用本地 OCR 时，文字识别在设备上完成；选择云端识图会上传截图，发起分析会把对话文字与必要背景发送给所选模型服务，并可能产生费用。各端保存方式见[数据使用说明](PRIVACY.md)。

Windows 填入依赖窗口位置，无法读回验证输入控件；iOS 键盘无法自动核实收件人。填入前请确认当前会话，不确定时复制后手动粘贴。

## 开发与离线体验

Mac 源码运行需要 Python 3.12 和 [uv](https://docs.astral.sh/uv/)：

```bash
git clone https://github.com/shengjidaguai-china/goutoujunshi-chat.git
cd goutoujunshi-chat/integrations/jev_mac
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
./start.command --demo
```

安装完成后，`--demo` 使用合成对话离线展示界面。真实使用运行 `./start.command`；直接打开设置运行 `./start.command --settings`。

四端实现位于 `integrations/`，关系指南位于 `references/`。主要流程为：**获取对话 → 人工核对 → 策略判断 → 生成与排序候选 → 用户选择草稿**。

在仓库根目录运行现有离线检查：

```bash
python3 -B scripts/validate_skill.py
python3 -B -m unittest discover -s tests -q
```

更多配置与开发说明：[Mac](integrations/jev_mac/README.md) · [Windows](integrations/jev_windows/README.md) · [Android](integrations/jev_android/README.md) · [iOS](integrations/jev_ios/README.md)。离线检查不替代真实设备、模型接口与聊天应用的兼容性测试。

## 贡献与致谢

- [@RayWangQvQ（在7楼）](https://github.com/RayWangQvQ)：[PR #1](https://github.com/shengjidaguai-china/goutoujunshi-chat/pull/1)，修复 Android 原文核对与焦点恢复流程，并补充测试。
- [@wstaery](https://github.com/wstaery)：[PR #2](https://github.com/shengjidaguai-china/goutoujunshi-chat/pull/2)，贡献 Windows QQNT 适配、聊天记录累计与采集稳定性改进及测试。
- 感谢 [Jev Android](https://github.com/jev-chat/jev-chat-jarvis)、[Jev Mac](https://github.com/jev-chat/jev-chat-jarvis-mac) 与 [Jev Windows](https://github.com/jev-chat/jev-chat-windows) 提供的基础实现。

仓库主体采用 [MIT 许可证](LICENSE)。第三方组件沿用各自许可，详见 [Mac LICENSE](integrations/jev_mac/vendor/LICENSE)、[Android NOTICE](integrations/jev_android/NOTICE) 与 [Windows NOTICE](integrations/jev_windows/NOTICE)。

欢迎[提交问题或建议](https://github.com/shengjidaguai-china/goutoujunshi-chat/issues)，也欢迎 [Star 收藏](https://github.com/shengjidaguai-china/goutoujunshi-chat/stargazers)。加入升级打怪开源群：Email `247133278@qq.com` · WeChat `loonges` · QQ `247133278`。
