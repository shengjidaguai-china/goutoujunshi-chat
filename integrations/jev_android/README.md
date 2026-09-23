# 狗头军师 Chat · Android 源码适配

本目录基于 [Jev Android](https://github.com/jev-chat/jev-chat-jarvis) 的聊天应用采集、ML Kit 中文离线 OCR、悬浮窗、Jev 判断和候选填入链路。已改为独立应用 ID `com.goutoujunshi.chat`，接入狗头军师的自然口吻、事实与推测边界、下一步和停止条件。原文与说话人仍需用户核对；对方明确要求停止联系时不生成候选，不自动发送。

**状态：调试 APK 可构建，Android 真机验收待完成。** GitHub Actions 提供本项目的调试 APK；它不代表已完成真机测试。首次安装时助手和自动分析默认关闭，需在界面中主动开启。Mac 版的人工核对页、关系 K 线和完整关系档案界面尚未移植。本目录不包含上游现成 APK，以免把原版误认为狗头军师版本。

要求 Android 11+，构建机须安装 JDK 17、Android SDK 35。进入本目录后运行：

```bash
./gradlew :app:testDebugUnitTest :app:assembleDebug
```

成功后调试包在 `app/build/outputs/apk/debug/`。应用的设置页可分别配置判断、回复、视觉接口；只有同一协议、主机和端口的接口才能共用密钥，跨服务须分别填写。请仅在自己的设备和有权查看的对话中使用，并在系统设置里授予无障碍、悬浮窗权限；OCR 兜底由本地 ML Kit 执行。数据使用见仓库根目录 [说明](../../PRIVACY.md)。

源码来源与署名见本目录的 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。
