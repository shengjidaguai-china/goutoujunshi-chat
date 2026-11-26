<!-- README_SYNC: source=working-tree; updated=2026-10-12 -->

<p><a href="./README.md">简体中文</a> · English · <a href="../../README.md">Project home</a></p>

# Goutoujunshi · iOS installation and usage

**Type, recognize chat screenshots and get relationship advice inside an iPhone keyboard, then confirm a reply before inserting it into your draft.** The companion app manages models, relationship profiles and candlesticks. Switch keyboards with the globe button in your chat; you decide when to send.

[Star the project](https://github.com/shengjidaguai-china/goutoujunshi-chat/stargazers) if it is useful, so you can find it again.

[![Stars](https://img.shields.io/github/stars/shengjidaguai-china/goutoujunshi-chat?style=flat)](https://github.com/shengjidaguai-china/goutoujunshi-chat/stargazers)
[![iOS](https://img.shields.io/badge/iOS-16%2B-orange)](https://github.com/shengjidaguai-china/goutoujunshi-chat/tree/main/integrations/jev_ios)
[![iOS build](https://github.com/shengjidaguai-china/goutoujunshi-chat/actions/workflows/ios-build.yml/badge.svg)](https://github.com/shengjidaguai-china/goutoujunshi-chat/actions/workflows/ios-build.yml)
[![License](https://img.shields.io/badge/License-MIT-orange)](../../LICENSE)

> **Installation currently requires a Mac and Xcode to build, sign and install on your own iPhone.** There is no public signed IPA, TestFlight invitation or App Store release. The iOS ZIP from GitHub Actions is a simulator development product and cannot install directly on a phone.

The port keeps relationship stages and goals, separated facts and inferences, stop conditions, candidate reasoning and “More like me.” It supports full Chinese Pinyin and English typing, DeepSeek-only judgment and replies, and Apple Vision, DeepSeek or OpenRouter screenshot recognition. Current in-app labels are Chinese; the steps below include their exact names.

**First-use order:** install → add the keyboard → save model settings → try copied text → configure the screenshot shortcut.

[Install on iPhone](#install) · [Configure DeepSeek](#configure) · [First use](#use) · [Screenshots](#screenshots) · [Troubleshooting](#faq)

<a id="install"></a>

## 1. Install on iPhone

### What you need

| Requirement | Details |
| --- | --- |
| Mac and full Xcode | Install [Apple Xcode](https://developer.apple.com/xcode/) and finish first-launch component setup. Use Xcode 15 or later with support for your phone's OS; this project has been built with Xcode 27.0. Command Line Tools alone are insufficient |
| iPhone and cable | iOS 16 or later; a cable is recommended for the initial installation |
| Your Apple Account | Sign into Xcode to sign the app and extensions with your own team |
| Model API key | Required for online analysis. Without one, you can try offline typing, local Apple Vision OCR and the companion app's offline example |

An ordinary Apple Account can use an Xcode **Personal Team** for personal-device testing. Its provisioning profiles expire after seven days and require rebuilding and reinstalling. Apple's current capability table lists account support for App Groups and Keychain Sharing; actual signing remains subject to Xcode. See [Apple's account guide](https://developer.apple.com/help/account/basics/about-your-developer-account) and [capability table](https://developer.apple.com/help/account/reference/supported-capabilities-ios/).

### Step 1: Download and open the project

On the [repository page](https://github.com/shengjidaguai-china/goutoujunshi-chat), choose **Code → Download ZIP**, extract it, open `integrations/jev_ios`, and double-click `GoutouJunshi.xcodeproj`. Download the whole repository: the project uses its relationship guidance and examples.

Alternatively, run on your Mac:

```bash
git clone https://github.com/shengjidaguai-china/goutoujunshi-chat.git
cd goutoujunshi-chat/integrations/jev_ios
open GoutouJunshi.xcodeproj
```

The generated project is checked in. XcodeGen and CocoaPods are not needed.

### Step 2: Sign with your own account

1. Sign into your Apple Account under **Xcode → Settings → Accounts**.
2. Select the blue project icon, then **TARGETS → GoutouJunshi → Signing & Capabilities**. Choose your **Team** and enable **Automatically manage signing**. You can inspect its identifier by searching for `DEVELOPMENT_TEAM` in that target's **Build Settings**.
3. Create **`Signing.local.xcconfig`** beside `Signing.xcconfig`. Supply your team identifier, unique app ID and shared group. Replace both `YOUR_TEAM_ID` and `yourname` in this format example:

```text
DEVELOPMENT_TEAM = YOUR_TEAM_ID
GOUTOU_BUNDLE_ID = com.yourname.goutoujunshi
GOUTOU_APP_GROUP = group.com.yourname.goutoujunshi
```

`Signing.local.xcconfig` overrides the [public signing configuration](Signing.xcconfig) and is ignored by Git. Do not commit personal signing files, certificates or API keys. Extension bundle IDs automatically append `.keyboard` and `.capture` to your app ID.

4. Check **all three targets**, keeping their team and shared capabilities consistent:

| Target | Role | App Groups | Keychain Sharing |
| --- | --- | --- | --- |
| `GoutouJunshi` | Companion app | Same `GOUTOU_APP_GROUP` | Shared keychain group |
| `GoutouKeyboard` | Keyboard | Same `GOUTOU_APP_GROUP` | Same as companion app |
| `GoutouCapture` | Experimental capture extension | Same `GOUTOU_APP_GROUP` | Not required |

Use **Automatically manage signing** for all three. The shared keychain group defaults to `AppIdentifierPrefix` plus the app ID; keep that derivation. If Xcode reports an unregistered group, create or select a group owned by your team and ensure provisioning includes it. Do not remove shared capabilities to bypass signing errors: the keyboard needs them for configuration and credentials.

### Step 3: Connect the phone and run

1. Connect and unlock your iPhone. Confirm “Trust This Computer” if prompted.
2. Follow Xcode's prompts to enable **Settings → Privacy & Security → Developer Mode**, restart, unlock, and confirm enabling it. If the menu is absent, initiate pairing with Xcode first. See [Apple's Developer Mode guide](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device/).
3. Select scheme **`GoutouJunshi`**, select **your iPhone** as the destination, then click **▶ Run**. This builds and installs the companion app, keyboard and capture extension.
4. If the phone reports an untrusted developer, trust your own developer account under **Settings → General → VPN & Device Management**, then open the app.

The Shiba-icon “狗头军师” app should appear. Its tabs are **使用** (Use), **关系** (Relationship), **配置** (Configuration), and **K 线** (Candlesticks).

### Step 4: Add the keyboard

On your iPhone, open:

**Settings → General → Keyboard → Keyboards → Add New Keyboard → 狗头军师**.

Select the added keyboard and enable **Allow Full Access** for shared configuration, clipboard reading and online analysis. Offline typing still works without it; the companion app can also be used independently. See [Apple's custom keyboard documentation](https://developer.apple.com/library/archive/documentation/General/Conceptual/ExtensibilityPG/CustomKeyboard.html).

In a chat input field, **hold the globe button → 狗头军师**. The keyboard starts in **打字** (Typing); **军师** opens the assistant and **识图** opens screenshot reception.

<a id="configure"></a>

## 2. Configure models: start with DeepSeek

Open the companion app's **配置** tab:

1. Tap **判断＋回复均使用 DeepSeek** to select DeepSeek for both judgment and reply generation.
2. Under **DeepSeek 官方**, enter your own API key from the [DeepSeek platform](https://platform.deepseek.com/). The default model ID is **`deepseek-flash`**; you may use another model supported by your account. See the current names in the [DeepSeek API documentation](https://api-docs.deepseek.com/zh-cn/). The endpoint is fixed at `https://api.deepseek.com` and needs no entry.
3. Choose OCR separately under **截图识别 → 识别方式**. Start with **Apple Vision · 本地** for local recognition. For DeepSeek OCR, select **DeepSeek · 图片识别**; it uses the same DeepSeek key and model, which must support image input.
4. Set tone, length and a maximum of 1–3 candidates.
5. Tap **测试 DeepSeek**, then **保存并应用配置** even if the test succeeds.

**The DeepSeek shortcut changes judgment and replies only. It does not change OCR.** To use DeepSeek for all three stages, select DeepSeek image recognition separately.

| Stage | Providers | Purpose |
| --- | --- | --- |
| Strategy judgment | DeepSeek / TypeSafe Jev | Assess evidence and boundaries; select acknowledge, reduce pressure, banter, gently advance, invite, clarify or end contact |
| Reply generation | DeepSeek / OpenRouter | Generate candidates for the accepted strategy, then score and rank them |
| Screenshot recognition | Apple Vision / DeepSeek / OpenRouter | Extract visible messages and preliminary speaker assignments for your review |

**Saved keys are never displayed; leaving the field blank keeps the existing key.** Each provider's key can be deleted or replaced. Tests use the current form values; success only confirms that test request. Structured strategy analysis and cloud OCR require separate verification. Tests, analysis and cloud OCR consume your own API allowance; the project supplies no free model credits.

### Jev and OpenRouter

- **Jev judgment:** select TypeSafe Jev for strategy judgment, fill its key and model ID, tap **测试 Jev 判断**, then save.
- **OpenRouter replies:** select OpenRouter for generation, supply its key and **回复模型 ID**, tap **测试 OpenRouter 回复**, then save. Combine with either DeepSeek or Jev judgment.
- **OpenRouter OCR:** select OpenRouter for screenshot recognition and set **识图模型 ID（独立配置）** to an image-capable model. Reply and image models may differ.

Use each provider's own key. Endpoints are fixed. OpenRouter provides replies and OCR here; judgment remains DeepSeek or Jev.

<a id="use"></a>

## 3. First use: try copied text

In the companion app's **关系** tab, set the person's label, relationship stage, current goal and necessary context, then save. Context can be set per person; explicitly saving a profile makes it available in the keyboard's person selector.

In a chat app that supports third-party keyboards:

1. Hold a text message and **copy** it.
2. Tap the input field, switch to Goutoujunshi with the globe button, and select **军师 → 读取剪贴板**.
3. Check the current person, original text and speakers. Assign a single message to “我” (me) or “对方” (other); review multi-turn transcripts line by line. Use the companion app's **核对本轮对话** editor for typos or longer conversations.
4. Tap **确认并分析**. The result shows possible intent, confidence, advice and **候选回复排序** (ranked replies).
5. Select a candidate: **为什么这样回** explains rationale and tradeoffs; **更像我一点** adjusts voice; **详细分析** shows facts, inferences, unknowns, next steps and stop conditions.
6. Tap **填入**, confirm the current recipient and reply inside the keyboard, then approve insertion. Text is inserted at the cursor without deleting an existing draft. The keyboard returns to Typing; edit and press your chat app's Send button yourself.

The keyboard cannot verify the recipient automatically. **After changing chats, change the selected person and review again** to avoid reusing another relationship's context. **读取输入框里的草稿** only reads your own local cursor context, not chat history.

### Analyze in the companion app

Under **使用 → 核对本轮对话**, paste and edit a multi-turn transcript, for example:

```text
我：周六想去看展，你有空吗？
对方：这周有点忙，下周再看看吧。
我：好，你先忙。
```

Enable **已核对原文、双方身份与当前对象**, then tap **确认并分析**. To use the result in chat, tap **把本轮结果交给键盘**, return to the chat and select this keyboard. The handoff expires after five minutes and can be consumed once; editing text, person or configuration clears it.

The keyboard separately caches the latest transcript and analysis locally for five minutes to restore after dismissal or reopening. Reopening does not extend expiry or preserve insertion approval. **清空本轮** deletes it immediately.

<a id="screenshots"></a>

## 4. Read chat screenshots

### Option A: Select a screenshot in the companion app

Take a chat screenshot, then open **使用 → 从截图读取聊天 → 选择聊天截图**. You can also choose **从文件选择截图** (a file) or **粘贴截图** (paste an image).

Apple Vision recognizes locally. DeepSeek/OpenRouter asks before uploading the selected image. Review text, order and speakers, then confirm analysis; hand the result to the keyboard when you want to insert a draft.

### Option B: Screenshot in chat and return to the keyboard

Open **使用 → 设置一键截屏识别** for guidance, then create a shortcut called **截图问军师** in the iPhone's Shortcuts app:

| Order | Action | Input |
| --- | --- | --- |
| 1 | System “Take Screenshot” (截屏 / 拍摄截屏) | Current screen |
| 2 | Goutoujunshi **截图交给键盘（按配置）** | Set 聊天截图 to the screenshot from the previous action |

Keep these two actions connected; no “Open App” action is needed. To review in the companion app instead, use **识别聊天截图（按配置）** as the second action. That action opens the app.

For a trigger available in chat, bind the shortcut under:

**Settings → Accessibility → Touch → AssistiveTouch → Custom Actions → Double-Tap → 截图问军师**.

Then:

1. Stay in the chat, switch to the keyboard and tap **识图** at the top.
2. **Double-tap the AssistiveTouch button within 90 seconds** to run the shortcut. Follow any first-run system permission prompts.
3. Apple Vision returns text directly. DeepSeek/OpenRouter returns an image preview first; tap **发送截图并识别** to upload it.
4. Review text and speakers, confirm analysis, choose a reply and confirm insertion.

**识图 prepares to receive a screenshot; the shortcut performs the screenshot itself.** The bottom keyboard region is cropped, so only visible chat above it is read. A legacy shortcut may still display **截图交给键盘（本地）**, but current code follows your OCR setting. If it opens the companion app, check that you did not choose **识别聊天截图** instead.

For an existing screenshot, copy it in Photos, then tap **读取已复制的截图** on the keyboard's screenshot page.

**屏幕捕获（实验）** uses ReplayKit's system confirmation interface and has not completed device end-to-end acceptance. Prefer the shortcut workflow above; implementation limits and checks are in the [development document](docs/DEVELOPMENT.md).

## 5. Other features

| Feature | Usage / interpretation |
| --- | --- |
| Offline typing | Full Pinyin by default: enter `nihao`, choose 你好, or press space for the first candidate. Scroll candidates horizontally; 分词 inserts a syllable separator. 中 / 英 switches language; 123, #+= and ABC switch digits, symbols and letters. No nine-key layout, voice input or personal frequency learning yet |
| More like me | Uses reviewed lines marked “我” in this round to rewrite candidate voice, preserving accepted judgment and strategy. Include several of your own sentences for better reference |
| Detailed analysis | Possible intent, your feelings, known facts, reasonable inferences, unknowns, next steps and stop conditions. An explicit refusal or request to stop contact prevents advancing suggestions |
| Percentages | Intent confidence is model self-assessment. Strategy weights come from Jev or validated DeepSeek first-token weights. Candidate percentages are relative recommendation weights within this set. None are statistically calibrated reply-success probabilities; unavailable weights are labeled |
| Relationship profiles | Seven stages, six goals and limited background. Only explicitly saved profiles enter the list, up to 100; full chat logs are not archived automatically |
| Relationship candlesticks | Use the companion app's K 线 tab for five example trends or import a chat CSV. Charts use daily message balance and need timestamped history; one screenshot cannot restore history |

Use UTF-8 CSV in ascending time order with `timestamp,sender,message` and optional `event`. Sender must be `me / other`; maximum size is 4 MB and 20,000 messages:

```csv
timestamp,sender,message,event
2026-08-01 10:00:00,me,周六看展吗,提出邀约
2026-08-01 10:01:00,other,我先看下安排,
```

Each “me” message contributes -1 and “other” +1. Daily cumulative-balance OHLC shows the latest 180 dates with messages; timezone-bearing ISO 8601 values are grouped in UTC. CSV processing stays local. The chart measures message balance, not affection or relationship quality.

<a id="faq"></a>

## 6. Troubleshooting

| Problem | What to check |
| --- | --- |
| Developer Mode is missing | Pair with Xcode over a cable, unlock and trust the Mac, then check Privacy & Security. Confirm enabling again after restart |
| Bundle ID, provisioning or group errors | Use your own unique IDs. Check team, automatic signing and App Group on all three targets; app and keyboard must share Keychain Sharing. Provisioning must include those groups |
| App Group 未连接, or keyboard cannot read a saved key | Check shared-group signing and Full Access. Save keys again after a signing change. Unsigned simulator builds may lack shared-container access; see the development document |
| Keyboard is absent from the list | Open the installed companion app, then add the keyboard in Settings. If absent, check that the installed app embeds GoutouKeyboard |
| Selecting it returns to the system keyboard | Try a normal Notes field. Host apps can reject custom keyboards; password and some phone fields also use the system keyboard. If it exits in ordinary fields too, report OS/app versions and reproduction steps in an Issue |
| 识图 produces no screenshot dialog | It opens a receiver page. Create the two-action shortcut and trigger it with AssistiveTouch within 90 seconds |
| DeepSeek judgment is selected, but OCR is local | Choose DeepSeek separately under 配置 → 截图识别, then save with 保存并应用配置 |
| Screenshot opens the companion app | Replace the shortcut's 识别聊天截图 action with 截图交给键盘（按配置） |
| Cloud OCR fails or model format is invalid | Check key, balance, model ID and image capability; review the text and retry. A connection test does not prove structured analysis or visual-request support. OCR failures do not silently fall back to local recognition |
| Content disappears after dismissal | The session expires after five minutes; person/config changes or clearing the round remove it. Screenshot waiting lasts 90 seconds; tap 重新等待截图 after timeout |
| Insertion is disabled | Review text and person, finish any pending Pinyin, keep the keyboard visible and Full Access enabled. Insertion approval expires in 60 seconds; select the candidate again |
| App stops opening after a week | The Personal Team provisioning profile may have expired. Reconnect to your Mac and Run again in Xcode |
| Can I give others an installable package? | They currently need their own signing. This repository has no public signed IPA or TestFlight invitation |

## Data and current status

- Everyday typing is local, calls no model and saves no input history. Reviewed chats are sent directly to the selected provider after analysis confirmation; cloud images require upload approval. There is no project-owned relay server.
- Keys live in the app/keyboard shared local Keychain. Session and screenshot handoffs last at most five minutes and are excluded from backup; expired data is deleted on next access, not guaranteed at an exact background deadline. Use **清除键盘暂存与等待取用的内容** in settings or delete provider keys. Keychain items may survive uninstall and need explicit deletion. See [privacy details](../../PRIVACY.md).
- On October 12, 2026, **225 offline checks, simulator and signed-device builds** passed, with installation and companion-app launch on a personal iPhone. The [first GitHub source build](https://github.com/shengjidaguai-china/goutoujunshi-chat/actions/runs/38209076299) passed. This does not establish complete device acceptance in every chat app.
- Build commands, experimental capture limits and history are in [Development and validation](docs/DEVELOPMENT.md).

## Licensing and acknowledgments

Original project code uses the root [MIT License](../../LICENSE). The keyboard/shared-container architecture adapts [Jev iOS](https://github.com/jev-chat/jev-chat-jarvis-ios), retaining its [LICENSE](vendor/LICENSE), [NOTICE](vendor/NOTICE) and [upstream revision](vendor/UPSTREAM.json). The offline dictionary uses [Rime pinyin-simp](https://github.com/rime/rime-pinyin-simp), retaining its [Apache-2.0 license](vendor/pinyin-simp/LICENSE), [authors](vendor/pinyin-simp/AUTHORS) and [pinned revision](vendor/pinyin-simp/UPSTREAM.json). Relationship guidance comes from this repository. The project is not affiliated with Apple, WeChat or other chat platforms.

[Star the project](https://github.com/shengjidaguai-china/goutoujunshi-chat/stargazers) to find it later. For problems, [open an Issue](https://github.com/shengjidaguai-china/goutoujunshi-chat/issues) with your iOS version, installed build and reproduction steps.
