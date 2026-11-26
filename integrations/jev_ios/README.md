<!-- README_SYNC: source=working-tree; updated=2026-10-12 -->

<p>简体中文 · <a href="./README_EN.md">English</a> · <a href="../../README.md">项目首页</a></p>

# 狗头军师 · iOS 安装与使用

**在 iPhone 键盘里打字、读聊天截图、看军师建议，确认后把回复填入草稿。** 主 App 用于配置模型、关系资料和查看 K 线；聊天时用地球键切换到狗头军师键盘，发送由你决定。

如果这个工具对你有用，可以[点一个 Star](https://github.com/shengjidaguai-china/goutoujunshi-chat/stargazers)，方便以后回来找到它。

[![Stars](https://img.shields.io/github/stars/shengjidaguai-china/goutoujunshi-chat?style=flat)](https://github.com/shengjidaguai-china/goutoujunshi-chat/stargazers)
[![iOS](https://img.shields.io/badge/iOS-16%2B-orange)](https://github.com/shengjidaguai-china/goutoujunshi-chat/tree/main/integrations/jev_ios)
[![iOS build](https://github.com/shengjidaguai-china/goutoujunshi-chat/actions/workflows/ios-build.yml/badge.svg)](https://github.com/shengjidaguai-china/goutoujunshi-chat/actions/workflows/ios-build.yml)
[![License](https://img.shields.io/badge/License-MIT-orange)](../../LICENSE)

> **当前安装方式：在 Mac 上用 Xcode 编译、签名，安装到自己的 iPhone。** 暂无公开签名 IPA、TestFlight 或 App Store 下载。GitHub Actions 的 iOS ZIP 是模拟器开发产物，不能直接装到手机。

保留狗头军师的关系阶段、目标、事实与推测分开、停止条件、候选理由和「更像我一点」。支持中文全拼与英文输入；判断和回复可以只用 DeepSeek；截图可选 Apple Vision 本地识别、DeepSeek 或 OpenRouter。

**第一次使用的顺序：** 安装 App → 添加键盘 → 保存模型配置 → 复制一段对话试用 → 再设置截图快捷指令。

[安装到 iPhone](#install) · [配置 DeepSeek](#configure) · [第一次使用](#use) · [截图识别](#screenshots) · [常见问题](#faq)

<a id="install"></a>

## 1. 安装到 iPhone

### 先准备这些

| 需要 | 说明 |
| --- | --- |
| Mac 与完整 Xcode | 安装 [Apple Xcode](https://developer.apple.com/xcode/)，首次打开完成组件安装。Xcode 15 或更新版本，且须支持你的 iPhone 系统；本工程已用 Xcode 27.0 构建验证。只有 Command Line Tools 不够 |
| iPhone 与数据线 | iOS 16 或更新版本；首次安装建议用数据线连接 |
| 自己的 Apple 账号 | 在 Xcode 登录，用于给 App 和扩展签名；不要使用别人的证书 |
| 模型 API Key | 联网分析需自己配置。没有 Key 也可先试本地打字、Apple Vision 识图和主 App 的离线示例 |

普通 Apple 账号可用 Xcode 的 **Personal Team** 在个人设备调试，描述文件 7 天到期，需要重新编译安装。Apple 当前能力表列出了 App Groups 与 Keychain Sharing 的账号支持；实际签名仍以 Xcode 为准。参见 [Apple 账号说明](https://developer.apple.com/help/account/basics/about-your-developer-account)与[能力表](https://developer.apple.com/help/account/reference/supported-capabilities-ios/)。

### 第一步：下载并打开工程

在[仓库首页](https://github.com/shengjidaguai-china/goutoujunshi-chat)点 **Code → Download ZIP**，解压后进入 `integrations/jev_ios`，双击 `GoutouJunshi.xcodeproj`。请下载整个仓库，工程会使用仓库中的关系指南和示例。

也可以在 Mac 终端运行：

```bash
git clone https://github.com/shengjidaguai-china/goutoujunshi-chat.git
cd goutoujunshi-chat/integrations/jev_ios
open GoutouJunshi.xcodeproj
```

工程已经生成，不需要安装 XcodeGen，也不需要准备 CocoaPods。

### 第二步：用自己的账号签名

1. 在 **Xcode → Settings → Accounts** 登录自己的 Apple 账号。
2. 点击左侧蓝色工程图标，在 **TARGETS → GoutouJunshi → Signing & Capabilities** 选择自己的 **Team**，开启 **Automatically manage signing**。团队标识可在该 target 的 **Build Settings** 搜索 `DEVELOPMENT_TEAM` 查看。
3. 在 `Signing.xcconfig` 同目录新建 **`Signing.local.xcconfig`**，填写自己的团队标识、唯一 App 标识与共享组。下面是格式示例，`YOUR_TEAM_ID` 和 `yourname` 都要替换成自己的值：

```text
DEVELOPMENT_TEAM = YOUR_TEAM_ID
GOUTOU_BUNDLE_ID = com.yourname.goutoujunshi
GOUTOU_APP_GROUP = group.com.yourname.goutoujunshi
```

`Signing.local.xcconfig` 会自动覆盖[公共签名配置](Signing.xcconfig)，已被 Git 忽略；不要把个人签名文件、证书或 API Key 提交到仓库。App ID 修改后，两个扩展的 ID 会自动追加 `.keyboard` 和 `.capture`。

4. 检查 **三个 target** 的 Team 和共享能力，保持一致：

| Target | 用途 | App Groups | Keychain Sharing |
| --- | --- | --- | --- |
| `GoutouJunshi` | 主 App | 同一个 `GOUTOU_APP_GROUP` | 同一个共享钥匙串组 |
| `GoutouKeyboard` | 键盘 | 同一个 `GOUTOU_APP_GROUP` | 与主 App 相同 |
| `GoutouCapture` | 实验截图扩展 | 同一个 `GOUTOU_APP_GROUP` | 不需要 |

三个 target 均使用 **Automatically manage signing**。共享钥匙串默认由 `AppIdentifierPrefix` 和 App ID 组成，保留工程默认值。若 Xcode 提示共享组未注册，按提示创建或选用自己团队拥有的组，并让描述文件包含它；不要删掉共享能力来绕过签名错误，键盘需要它们读取配置与 Key。

### 第三步：连接手机并运行

1. 用数据线连接并解锁 iPhone；手机出现「信任此电脑」时确认。
2. 按 Xcode 提示，在 iPhone **设置 → 隐私与安全性 → 开发者模式** 开启并重启；重启后解锁，完成系统的开启确认。若该菜单尚未出现，先让 Xcode 与手机配对。参见 [Apple 开发者模式说明](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device/)。
3. Xcode 顶部 scheme 选择 **`GoutouJunshi`**，运行目标选择**你的 iPhone**，点击 **▶ Run**。这会编译并安装主 App、键盘和截图扩展。
4. 若手机提示开发者未受信任，在 **设置 → 通用 → VPN 与设备管理** 中信任自己的开发者账号，再打开 App。

安装成功后，手机上会出现柴犬图标的「狗头军师」。主 App 底部有 **使用、关系、配置、K 线** 四个页面。

### 第四步：添加键盘

在 iPhone 打开：

**设置 → 通用 → 键盘 → 键盘 → 添加新键盘 → 狗头军师**。

再点已添加的「狗头军师」，开启 **允许完全访问**，供键盘读取共享配置、剪贴板和联网分析。关闭这个开关仍可本地打字，主 App 也可单独使用。权限用途见 [Apple 自定义键盘说明](https://developer.apple.com/library/archive/documentation/General/Conceptual/ExtensibilityPG/CustomKeyboard.html)。

打开聊天输入框，**长按地球键 → 狗头军师**。键盘默认进入「打字」，顶部「军师」切换分析面板，「识图」进入截图接收页。

<a id="configure"></a>

## 2. 配置模型：先用 DeepSeek 跑通

打开主 App 底部 **配置**：

1. 点 **「判断＋回复均使用 DeepSeek」**。
2. 在 **DeepSeek 官方** 中填入自己从[DeepSeek 开放平台](https://platform.deepseek.com/)创建的 API Key；模型 ID 默认是 **`deepseek-flash`**，也可填账户支持的模型。当前官方名称见 [DeepSeek API 文档](https://api-docs.deepseek.com/zh-cn/)。地址固定为 `https://api.deepseek.com`，无需填写。
3. 在 **截图识别 → 识别方式** 单独选择 OCR。第一次可选 **Apple Vision · 本地**；要截图也用 DeepSeek，就选 **DeepSeek · 图片识别**，使用同一 Key 和 DeepSeek 模型，模型须支持图片输入。
4. 设置回复口吻、长度和最多 1–3 条候选。
5. 点 **「测试 DeepSeek」**，成功后仍需点 **「保存并应用配置」**。

**「判断＋回复均使用 DeepSeek」只切换判断和回复，不会修改截图识别选项。** 希望三个环节都用 DeepSeek，需要再手动选 DeepSeek 图片识别。

| 环节 | 可选服务 | 做什么 |
| --- | --- | --- |
| 策略判断 | DeepSeek / TypeSafe Jev | 看证据与边界，选承接、降压、调侃、轻推、约见、澄清或收线 |
| 回复生成 | DeepSeek / OpenRouter | 按已接受的策略生成候选，再评分排序 |
| 截图识别 | Apple Vision / DeepSeek / OpenRouter | 提取可见聊天文字与初步说话人归属，之后由你核对 |

**Key 保存后不回显，输入框留空会保留原 Key。** 可以按服务删除或填写新 Key 替换。测试使用当前表单值，连接成功只证明该测试请求通过；真实策略分析和云端识图还需分别验证。测试、分析和云端识图都使用自己的接口用量，项目不提供免费模型额度。

### Jev / OpenRouter 怎么选

- **Jev 判断**：策略判断选 TypeSafe Jev，在对应区块填写 Jev Key 与模型 ID，点「测试 Jev 判断」，再保存。
- **OpenRouter 回复**：回复生成选 OpenRouter，填写它的 Key 与「回复模型 ID」，点「测试 OpenRouter 回复」，再保存。可以搭配 DeepSeek 或 Jev 判断。
- **OpenRouter 识图**：截图识别选 OpenRouter，另填「识图模型 ID（独立配置）」，须支持图片输入。回复模型与识图模型可以不同。

各服务使用自己的 Key；界面中的地址固定。OpenRouter 在本版提供回复与识图，判断仍选 DeepSeek 或 Jev。

<a id="use"></a>

## 3. 第一次使用：先复制文字

先在主 App **关系** 页面填写对象的称呼、关系阶段、本轮目标和必要背景，保存。关系阶段与目标可以按不同对象分别设置；勾选保存到档案后，键盘可切换对象。

在任意支持第三方键盘的聊天 App 中：

1. 长按一条文字消息，**复制**。
2. 点输入框，长按地球键切到狗头军师，点顶部 **军师 → 读取剪贴板**。
3. 核对当前对象、原文和说话人。单条消息可指定「我 / 对方」，多轮内容逐条确认；需要编辑错字或长对话，可到主 App 的「核对本轮对话」区域处理。
4. 点 **确认并分析**。结果会显示对方可能的意图、判断把握、军师建议和 **候选回复排序**。
5. 选一个候选：点「为什么这样回」看理由与代价；点「更像我一点」调整口吻；点「详细分析」查看事实、推测、未知、下一步与停止条件。
6. 点 **填入**，在键盘内确认当前收件人和候选文字，再确认填入。文字写入当前光标，已有草稿保留，随后回到狗头军师的打字布局。修改满意后，自己点聊天 App 的发送按钮。

键盘无法自动核实聊天对象。**切换会话后请切换对象并重新核对**，以免带入上一段关系背景。「读取输入框里的草稿」只取得光标附近自己的文字，无法读取聊天历史。

### 也可以在主 App 中分析

主 App **使用 → 核对本轮对话**，粘贴并编辑多轮原文，例如：

```text
我：周六想去看展，你有空吗？
对方：这周有点忙，下周再看看吧。
我：好，你先忙。
```

勾选 **已核对原文、双方身份与当前对象**，点「确认并分析」。想回聊天填写，点 **把本轮结果交给键盘**，再切回聊天使用狗头军师键盘。交接有效期 5 分钟，只能取用一次；改原文、对象或配置会清掉旧交接。

键盘最近一轮原文与分析另在本机暂存 5 分钟，收起或重开可恢复；重开不会延长时间，也不会保留填入确认。点「清空本轮」可立即删除。

<a id="screenshots"></a>

## 4. 从截图读取聊天

### 方式 A：在主 App 选择截图

手机截取聊天画面 → 狗头军师 **使用 → 从截图读取聊天 → 选择聊天截图**。也可「从文件选择截图」或「粘贴截图」。

Apple Vision 在手机本地识别；DeepSeek / OpenRouter 会先请求你确认上传这张截图。识别后核对错字、顺序和「我 / 对方」，再确认分析；需要填入时把结果交给键盘。

### 方式 B：聊天页截屏，结果回到键盘

先在主 App **使用 → 设置一键截屏识别** 查看引导，再在 iPhone「快捷指令」中创建 **截图问军师**：

| 顺序 | 添加的动作 | 参数 |
| --- | --- | --- |
| 1 | 系统「截屏」（也可能叫「拍摄截屏」） | 截取当前画面 |
| 2 | 狗头军师 **「截图交给键盘（按配置）」** | 「聊天截图」选择上一步的截屏结果 |

保持这两步相连，无需添加「打开 App」。想在主 App 核对时，第二步改选「识别聊天截图（按配置）」即可；这个动作会打开主 App。

为了在聊天页直接触发，把「截图问军师」绑定到：

**设置 → 辅助功能 → 触控 → 辅助触控 → 自定操作 → 轻点两下 → 截图问军师**。

之后这样使用：

1. 留在聊天页，切到狗头军师键盘，点顶部 **识图**。
2. **90 秒内双击辅助触控悬浮球**，运行刚才的快捷指令。首次运行按系统提示允许操作。
3. Apple Vision 模式直接回传文字；DeepSeek / OpenRouter 模式先把截图送回键盘预览，点 **发送截图并识别** 后才上传。
4. 核对文字与说话人，再确认分析、选择候选、确认填入。

**顶部「识图」是准备接收截图，实际截屏由快捷指令执行。** 截图会裁掉底部键盘，只识别上方可见的聊天。旧动作名称可能仍显示「截图交给键盘（本地）」，当前代码会沿用所选 OCR 配置；如返回了主 App，请检查是否误选「识别聊天截图」动作。

已有截图也可在「照片」中拷贝，回到键盘「识图」页点 **读取已复制的截图**。

「屏幕捕获（实验）」使用 ReplayKit 的系统确认界面，目前尚未完成真机端到端验收。日常使用优先按上面的快捷指令流程；实验机制与检查记录见[开发文档](docs/DEVELOPMENT.md)。

## 5. 其他功能

| 功能 | 怎么使用 / 怎样理解 |
| --- | --- |
| 本地打字 | 默认中文全拼；输入 `nihao` 选「你好」，空格确认首选。候选栏横向滑动，「分词」插入拼音分隔符；「中 / 英」切语言，「123」「#+=」「ABC」切数字、符号与字母。尚无九宫格、语音输入和个人词频学习 |
| 更像我一点 | 参考本轮已核对、标为「我」的句子修改候选口吻，保留已接受的判断与策略。多提供几句自己的话会更有参考价值 |
| 详细分析 | 展开可能意图、自己的感受、已知事实、合理推测、仍未知、下一步与停止条件；明确拒绝或要求停止联系时不生成推进建议 |
| 百分比 | 意图把握是模型自评；策略权重来自 Jev 或通过校验的 DeepSeek 首 token 权重；候选百分比是当前候选集合的相对推荐权重。均未经统计校准，不能当作回复成功率；权重缺失会明确显示不可用 |
| 关系资料 | 七种阶段、六种目标与有限背景；主动勾选档案保存才加入对象列表，最多 100 个，不自动保存聊天全文 |
| 关系趋势 K 线 | 主 App「K 线」查看五组走势示例或导入聊天 CSV。按每日消息净差绘制，需要带时间戳的历史数据，单张截图无法还原历史 |

K 线 CSV 使用 UTF-8、按时间升序，字段是 `timestamp,sender,message`，可加 `event`；`sender` 仅用 `me / other`。最多 4 MB、20,000 条消息：

```csv
timestamp,sender,message,event
2026-08-01 10:00:00,me,周六看展吗,提出邀约
2026-08-01 10:01:00,other,我先看下安排,
```

每条我方消息记 -1、对方记 +1，按天计算累计净差的开高低收，显示最近 180 个有消息的日期；带时区的 ISO 8601 时间按 UTC 分组。CSV 在本机处理，K 线反映消息净差，不能测量爱意或关系质量。

<a id="faq"></a>

## 6. 常见问题

| 遇到的问题 | 检查方法 |
| --- | --- |
| 手机上没有「开发者模式」 | 先用数据线与 Xcode 配对，解锁并信任电脑，再检查「隐私与安全性」；重启后还需完成开启确认 |
| Bundle ID / 描述文件 / 共享组报错 | 换成自己唯一的 ID；检查三个 target 的 Team、自动签名与 App Group，主 App 和键盘的 Keychain Sharing 必须一致。描述文件须包含对应共享组 |
| 显示「App Group 未连接」或键盘读不到已保存 Key | 核对共享组签名和完全访问。改签名后重新保存 Key；模拟器未签名构建可能不能访问共享组，见开发文档 |
| 列表里没有狗头军师键盘 | 先打开已安装的主 App，再到系统键盘设置添加；若仍没有，检查安装的 App 是否包含 `GoutouKeyboard` 扩展 |
| 切键盘后回到系统键盘 | 先在备忘录普通输入框试用。宿主 App 可以禁用第三方键盘，密码框和部分电话输入框也会使用系统键盘。若普通输入框仍退出，请提供系统版本、App 版本及复现步骤，提交 Issue |
| 点「识图」没有系统截屏弹窗 | 该按钮进入接收页。需要创建两步快捷指令，并在 90 秒内通过悬浮球触发 |
| 选了 DeepSeek 判断，OCR 还是本地 | 到「配置 → 截图识别」另选 DeepSeek 图片识别，再「保存并应用配置」；判断与 OCR 是独立选项 |
| 截图后跳到主 App | 快捷指令第二步用了「识别聊天截图」。要回键盘，改用「截图交给键盘（按配置）」 |
| 云端识图失败 / 模型格式错误 | 检查 Key、余额、模型 ID 和图片能力；核对原文后重试。连接测试不保证结构化分析或视觉请求成功；识图失败不会自动切到本地 |
| 收起后内容不见了 | 本轮暂存固定 5 分钟；切对象、改配置、清空本轮会清除。截图等待本身只有 90 秒，超时点「重新等待截图」 |
| 填入按钮不可用 | 先完成原文与对象核对，结束正在输入的拼音；保持键盘可见且完全访问开启。填入确认 60 秒到期，过期需重新选择候选 |
| 一周后 App 打不开 | Personal Team 描述文件可能已到期，连接 Mac 后在 Xcode 重新 Run 安装 |
| 能直接给别人一个安装包吗 | 当前需各自签名安装；本仓库没有可用的 TestFlight 邀请或公开签名 IPA |

## 数据与当前状态

- 日常打字在本机完成，不调用模型、不记录输入历史。聊天原文在你确认分析后直发所选服务，云端截图先确认上传；没有本项目的中转服务器。
- Key 存在主 App 与键盘共享的本机钥匙串。最近一轮与截图交接最长 5 分钟，排除备份；到期后下次访问清理，系统不保证后台准点删除。配置页可「清除键盘暂存与等待取用的内容」，也可删除各服务 Key。钥匙串项目卸载后可能保留，需主动删除。详见[隐私说明](../../PRIVACY.md)。
- 2026-10-12 已通过 **225 项离线检查、模拟器与签名设备编译**，并在个人 iPhone 安装、启动主 App。[首次 GitHub 源码构建](https://github.com/shengjidaguai-china/goutoujunshi-chat/actions/runs/38209076299)通过；这些检查不等于每个聊天 App 都完成真机验收。
- 编译命令、实验捕获限制和历史记录移至[开发与验证](docs/DEVELOPMENT.md)。

## 开源与致谢

项目原创代码采用根目录 [MIT License](../../LICENSE)。内容参考了jev-chat，这里非常感谢，保留其 [LICENSE](vendor/LICENSE)、[NOTICE](vendor/NOTICE) 与[来源版本](vendor/UPSTREAM.json)。本地拼音词库来自 [Rime 袖珍简化字拼音](https://github.com/rime/rime-pinyin-simp)，保留 [Apache-2.0 许可证](vendor/pinyin-simp/LICENSE)、[作者说明](vendor/pinyin-simp/AUTHORS)与[固定版本](vendor/pinyin-simp/UPSTREAM.json)。关系指南来自本仓库。项目与 Apple、微信及其他聊天平台无关联。

欢迎[收藏项目](https://github.com/shengjidaguai-china/goutoujunshi-chat/stargazers)，使用中遇到问题请[提交 Issue](https://github.com/shengjidaguai-china/goutoujunshi-chat/issues)，附上 iOS 版本、安装版本与复现步骤。
