# iOS 开发与验证 / Development and validation

返回 [中文安装与使用说明](../README.md) · [English installation and usage](../README_EN.md)

这里记录开发检查与历史验收，普通用户按 README 安装即可。编译成功、离线测试通过和聊天 App 内完整交互是不同的验证范围。

This page keeps development commands and historical evidence outside the user guide. A successful build or offline check does not establish complete keyboard behavior in every chat app.

## 离线检查 / Offline checks

在 `integrations/jev_ios` 目录运行；需要完整 Xcode，不调用真实模型。

Run from `integrations/jev_ios` with full Xcode installed. These checks do not call live models.

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer bash tools/check.sh
```

工程已经提交，无需安装 XcodeGen。按需重新生成工程或同步仓库关系指南：

The generated project is checked in; XcodeGen is not required. To regenerate it or sync repository guidance:

```bash
python3 tools/generate_project.py
python3 tools/sync_guidance.py
```

## 编译 / Builds

模拟器编译检查：

Simulator compilation check:

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild \
  -project GoutouJunshi.xcodeproj -scheme GoutouJunshi \
  -destination 'generic/platform=iOS Simulator' -derivedDataPath build \
  CODE_SIGNING_ALLOWED=NO build
```

上面的未签名产物用于编译验证。若模拟器运行时 App Group 未连接，可使用本地临时签名；这种签名不能安装到 iPhone：

The unsigned product is for compilation checks. For simulator App Group access, use ad-hoc local signing; it cannot install on an iPhone:

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild \
  -project GoutouJunshi.xcodeproj -scheme GoutouJunshi \
  -destination 'generic/platform=iOS Simulator' -derivedDataPath build \
  CODE_SIGN_STYLE=Manual CODE_SIGN_IDENTITY=- CODE_SIGNING_ALLOWED=YES build
```

未签名设备编译检查；真机安装需按 README 配置有效签名：

Unsigned device compilation check. Device installation still needs valid signing as described in the README:

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild \
  -project GoutouJunshi.xcodeproj -scheme GoutouJunshi \
  -destination 'generic/platform=iOS' -derivedDataPath build-device \
  CODE_SIGNING_ALLOWED=NO build
```

模拟器产物：`build/Build/Products/Debug-iphonesimulator/GoutouJunshi.app`。设备产物：`build-device/Build/Products/Debug-iphoneos/GoutouJunshi.app`。两个扩展位于 App 的 `PlugIns/GoutouKeyboard.appex` 与 `PlugIns/GoutouCapture.appex`。

Simulator and device product paths are listed above; the app embeds both keyboard and capture extensions.

## 实验捕获与模型权重 / Experimental capture and model weights

「屏幕捕获（实验）」在 iOS 16–26 使用 ReplayKit，必须允许键盘完全访问，并由用户在系统界面确认。GoutouCapture 仅取一帧、裁掉底部键盘后停止，不读取 Key、不联网、不处理音频。iOS 27 上该入口不启用，键盘显示快捷指令与复制截图方案。这个入口尚未完成真机端到端验收，受保护画面也可能无法捕获。

On iOS 16–26, the ReplayKit experiment requires keyboard Full Access and explicit system confirmation. GoutouCapture takes one frame, crops the keyboard and stops; it reads no key, makes no network request and handles no audio. The entry is disabled on iOS 27, where the keyboard shows shortcut/copied-image alternatives. Device end-to-end acceptance is pending, and protected content may be unavailable.

DeepSeek 正常多候选分析通常有六次请求：证据一次、七类策略的标签轮换三次、回复一次、候选排序一次。权重缺失会提前结束权重检查，单候选无需单独排序；证据格式可能额外修复一次。三轮首 token logprobs 须包含全部策略、胜出一致且与证据判断相符，才展示相对策略权重；否则保留证据判断并标注权重不可用。明确停止联系时跳过权重请求并约束为收线。候选推荐权重来自独立评分再归一化，不是这些策略 token 的概率。

A normal multi-candidate DeepSeek run usually makes six requests: evidence, three rotations of labels for seven strategies, generation and candidate ranking. Missing weights can stop the weight check early; a single candidate skips ranking, and evidence-format repair may add one request. Relative strategy weights require all classes in first-token logprobs, consistent winners across rotations and agreement with the evidence decision. Otherwise evidence remains and weights are marked unavailable. Explicit stop-contact cases skip weight requests and constrain the strategy to end contact. Candidate weights are separately scored and normalized, not derived from these strategy tokens.

## 当前验证范围 / Current validation scope

- 2026-10-12：225 项离线检查通过（核心 165、打字 33、OCR 27），模拟器与签名设备构建通过，个人 iPhone 安装与主 App 启动完成。该轮未调用真实模型、未发送聊天消息。
- [GitHub 首次源码构建](https://github.com/shengjidaguai-china/goutoujunshi-chat/actions/runs/38209076299)通过离线检查、模拟器和未签名设备编译。[自动构建](https://github.com/shengjidaguai-china/goutoujunshi-chat/actions/workflows/ios-build.yml)的 ZIP 是模拟器开发产物。
- 宿主聊天 App 的键盘恢复、云端图片识别和候选填入需要逐个真机验收；ReplayKit 实验入口尚未完成真机端到端验收。

On October 12, 2026, all 225 offline checks passed (165 core, 33 typing, 27 OCR), simulator and signed-device builds passed, and installation plus companion-app launch succeeded on a personal iPhone. That run made no live model requests or sent chat messages. The linked GitHub source build passed offline checks and both compilation jobs. Its ZIP contains a simulator development app. Keyboard restoration, cloud OCR and draft insertion need validation in each host app; the ReplayKit experiment has not completed device end-to-end acceptance.

## 历史记录 / Historical notes

以下保留原 README 的分次验证记录。以每条当时的版本和验收范围为准；其中旧 build 的待验收说明不表示最新版本回退。

The following Chinese notes preserve the original README's dated checks. Each describes its own build and scope; an older pending check is not evidence that a newer build regressed.

<details>
<summary>展开历史验证记录 / Expand historical validation notes</summary>

2026-10-11 填入崩溃修复：build 11 真机报告显示 confirmInsert 创建 UIAlertController 时触发 _UIApplicationAssertForExtensionType，键盘以 SIGABRT 退出。build 12 将收件人确认与候选理由改为键盘内视图，确认后只调用文字插入并回到本键盘打字布局，保留本轮分析。新增单次填入、取消、60 秒过期、切换文档 / 对象 / 配置、键盘隐藏与失去权限等检查，以及禁止键盘使用系统弹窗的工程检查。225 项离线检查通过（核心 165、打字 33、OCR 27），模拟器和签名真机编译、签名核验通过，已覆盖安装到个人 iPhone。手机使用中导致镜像断开，完整宿主 App 填入与继续打字的界面验收仍待直接手机重试；本轮未调用真实模型或发送聊天消息。

2026-10-11 OCR 配置路由修复：build 11 修正快捷指令与实验捕获固定使用 Apple Vision 的问题；现在严格沿用 OCR 配置，云端截图先回到键盘预览，主动确认后才发至所选模型。209 项离线检查通过（核心 149、打字 33、OCR 27），覆盖云端图片交接、跨进程预览恢复、过期与取消、不同模型的图片请求、缺失 Key 和接口失败不回退本地。模拟器、签名真机编译及签名核验通过，已覆盖安装到个人 iPhone；真机使用页确认仍选 DeepSeek，截屏指引已显示按配置流程。本轮未发送私人截图或调用真实模型，宿主 App 中完整截屏到云端识图仍需用户重试验证。

2026-10-11 收起键盘丢失内容修复：build 10 通过模拟器与已签名 iPhone 编译、签名核验，并已覆盖安装到个人 iPhone。175 项离线检查通过（核心 123、打字 33、OCR 19），新增检查覆盖跨进程恢复原文与结果、不可延长的过期时间、对象与配置变化清理、损坏文件及收起期间截图回传。真机“收起 → 重开”的界面验收仍待用户直接操作手机确认；本次未调用真实模型。

2026-10-11 入口修正（build 9）：用户反馈广播面板未弹出，不能据编译通过宣称直接截屏可用。顶部改为“识图”，默认说明系统截屏快捷指令；新增后台“截图交给键盘（本地）”动作、底部键盘裁剪与 90 秒超时反馈。103 项核心、33 项输入法、19 项 OCR 检查通过，模拟器和真机编译通过，并覆盖安装到个人 iPhone；快捷指令编辑与真机键盘接收仍待验收。

2026-10-11 键盘系统捕获实验：build 8 已通过模拟器与已签名 iPhone 编译，三个扩展 / App 的签名组和内嵌关系检查通过；已覆盖安装到个人 iPhone。151 项离线检查通过（共享核心 103、拼音 33、截图 OCR 15），包含请求有效期、一次性回传、对象 / 配置切换、取消及非法内容。模拟器已显示新版键盘截屏入口；系统取帧、OCR 回到键盘和候选填入尚待用户在手机上确认测试，本轮未调用真实模型。

2026-10-11 真机快捷指令检查：在 iPhone 14 Pro（iOS 26.6.2，App build 6）创建并保存“截图问军师”，包含“截屏 → 识别聊天截图（本地）”两项动作，图片参数自动连接上一项输出。运行后主 App 显示“快捷指令 · Apple Vision 本地”来源，提取文字并打开核对区域，未自动调用分析模型。已按用户选择开启辅助触控，并确认“轻点两下”绑定为“截图问军师”。iPhone 镜像运行时手机处于锁屏，系统实际捕获锁屏画面；此检查验证了图片传入与本地识别链路，悬浮球双击截取聊天页面需要解锁手机后直接触发验证。真机键盘填入仍待验收。

2026-10-11 一键识图与键盘布局更新：0.1.0（build 4）已通过模拟器和已签名 iPhone 编译、签名核验，并在个人 iPhone 覆盖安装和启动。模拟器中已创建“截屏 → 识别聊天截图（本地）”快捷指令，参数自动连接上一项截图；运行后实际提取画面文字并打开核对区域，确认开关保持关闭，未自动分析。新版固定键盘实际完成 nihao → 你好候选选择及写入。136 项离线检查通过，未调用真实模型。真机聊天 App 截屏与键盘识图仍需用户验收。

2026-10-11 截图入口更新：主 App 增加独立截图卡片、图片预览与粘贴截图；键盘增加图片按钮、剪贴板图片识别和原文核对。共享核心 88 项、拼音 33 项与截图 OCR 15 项检查通过；OCR 检查使用生成的中文聊天图，覆盖读取顺序、初步说话人归属、未确认标记、图片缩小、方向修正、元数据去除、非法图片和取消。主 App 与键盘扩展的模拟器、已签名 iPhone 编译通过，0.1.0（build 3）已在个人 iPhone 覆盖安装并启动。模拟器相册选图已实际提取三条中文聊天并初步区分左右说话人，居中标题标为待确认；键盘 OCR 在真机聊天 App 中的行为，以及真实视觉接口仍待验收；未调用真实模型。

2026-10-10 本机验证：共享核心 88 项与离线拼音输入 33 项检查通过。更新后的主 App 和键盘扩展均通过模拟器与已签名 iPhone 编译、签名核验；个人 iPhone 已安装并启动 0.1.0（build 2）。模拟器关闭完全访问时，已用自定义键盘输入 nihao、选择“你好”并写入主 App 输入框，验证英文、数字、删除、空格与换行写入，以及“军师 / 打字”切换。**真机聊天 App 内的键盘输入、共享 Keychain 和真实模型请求仍待验收**；本轮未填写真实 Key 或调用模型。

2026-10-08 历史验证：使用 Xcode 27.0 / iOS 27.0 SDK，主 App 与键盘扩展的模拟器版本（arm64、x86_64）和未签名 iPhone 设备版本（arm64）均编译成功；共享核心 88 项离线检查、UI 语法解析、工程与资源元数据检查通过。后续真机验收需覆盖：DeepSeek / Jev / OpenRouter 真实请求、云端截图确认、切换对象与取消任务、已有草稿追加、拒绝联系场景、系统禁用第三方键盘场景。当时的未签名设备产物不能直接安装到 iPhone。

另已在 iPhone 17 / iOS 27.0 模拟器中启动主 App，检查离线分析与详细页、接口配置页面、配置保存以及 K 线示例绘制。本地临时签名后 App Group 配置连接正常；本轮未填写真实 Key、未调用模型接口，未开启键盘完全访问。

此前本机另已完成 iPhone Release 编译并封装未签名 IPA，核对主 App、内嵌键盘扩展、arm64 架构及包结构。该旧包不包含本次输入法更新，尚未配置签名和设备描述文件，不能直接安装或上传 TestFlight，未作为 GitHub Release 发布。

</details>
