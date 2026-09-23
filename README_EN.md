<!-- README_SYNC: source=working-tree; updated=2026-09-23 -->

<p align="center"><a href="./README.md">简体中文</a> · English</p>

# Goutoujunshi Chat

**A Mac chat companion for screen reading, transcript review, relationship analysis, and reply drafts.** This standalone desktop project builds on [Goutoujunshi](https://github.com/shengjidaguai-china/goutoujunshi). It retains the original project's scenario-specific relationship guidance, evidence boundaries, next steps, and stop conditions, then brings them into a draggable overlay.

If it helps you, [Star the project](https://github.com/shengjidaguai-china/goutoujunshi-chat/stargazers) so you can find it again and help others discover it.

## Screenshots

### Overlay beside WeChat

![The overlay beside WeChat shows possible intent, evidence, advice, and ranked reply drafts](documentation/screenshots/overlay-in-wechat.png)

*Desktop screenshot supplied by the author. The panel shows a possible intent, the model's confidence estimate, evidence from the visible chat, and ranked reply drafts. The 52% and 48% values are relative recommendation weights for this set of drafts. “Copy” puts a draft on the clipboard; “Fill” inserts it into the current chat draft. You choose whether to send it.*

### Detailed analysis

![Detailed analysis in an offline synthetic demo](documentation/screenshots/analysis-detail-demo.png)

*Offline synthetic demo. The detail view separates possible intent, advice, your own feelings, observed facts, and reasonable hypotheses. The transcript tab lets you check the recognized text before analysis. The 62% shown here is a model self-assessment for its intent hypothesis, not a validated probability.*

### Relationship candlestick window

![The relationship candlestick window with example patterns and a chat CSV import option](documentation/screenshots/kline-window.png)

*Open this window with the overlay's “K-line” button. You can explore five example patterns or import a chat CSV with `timestamp,sender,message` columns. Imported records produce daily open, high, low, and close values for the running message-direction balance; first verify that `sender` is `me` or `other`. A visible WeChat screen does not provide a complete history for a long-term chart.*

### Five illustrative patterns

![Five relationship candlestick examples](documentation/screenshots/five-kline-patterns.png)

*Five relationship patterns: mutual warming, cooling after intense chat, repair after conflict, a busy but reliable partner, and drawing a line after a clear boundary. The 0–100 index was assigned by hand from each example's events to illustrate how to read them alongside a chart; it is not a relationship success rate. The bottom-right note saying the Mac overlay has no candlestick feature is from an earlier illustration; the current app has the window shown above.*

## One round of use

1. Open the target conversation in WeChat for Mac and click “Read conversation” in the overlay.
2. Check the recognized text, speakers, relationship stage, and your goal before confirming analysis.
3. Review the possible intent, confidence estimate, evidence, advice, and ranked reply drafts. Open “Detailed analysis” for facts, hypotheses, unknowns, next steps, and stop conditions.
4. Copy a draft or fill the verified chat input. You decide when and whether to send it.

**Apple Vision** performs local text recognition by default. You can opt into **DeepSeek image recognition**; that mode sends a cropped chat screenshot to DeepSeek and incurs API usage. DeepSeek or a configured OpenAI-compatible endpoint generates reply drafts. **TypeSafe Jev is an optional strategy layer**: when enabled, it chooses a strategy before the reply model generates drafts. The two API keys are configured separately through the UI and stored in dedicated Mac Keychain entries. No real keys are included in this repository.

Intent confidence is the reply model's uncalibrated self-assessment. Candidate percentages are relative recommendation weights within the current set of drafts. Neither is a verified probability of intent, reply rate, or relationship outcome. The app shows an unknown state when the evidence is insufficient.

## What makes it different

- **Replies in your style:** It uses only verified messages attributed to you in the current conversation. “More like me” revises the current drafts without training a model or borrowing text from other conversations.
- **Reasons and trade-offs:** Expand each candidate to see why it fits and what it costs. Advice includes an observation window and a stop condition.
- **Opt-in relationship profiles:** With explicit consent, the app stores limited background details. You can inspect, pause, undo, or delete them. It does not store the full chat.
- **Charts with stated rules:** Five example patterns are included. For an imported CSV, the chart tracks daily message-direction balance. Neither chart measures love or relationship quality.
- **Human control:** OCR results are reviewed first, automatic analysis starts off, and the chat is checked again before filling. The app does not press Send.

## Install and run

Requires macOS, Python 3.12, and [`uv`](https://docs.astral.sh/uv/). From the repository root:

```bash
cd integrations/jev_mac
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
./start.command --demo
```

`--demo` uses a synthetic conversation and stays offline: it neither reads WeChat nor calls a model. For real use, run `./start.command`. Run `./start.command --settings` to open settings directly, then use “Interfaces and models → Configure interfaces” to save a DeepSeek key and, optionally, a TypeSafe Jev key. Grant the launching terminal macOS Screen Recording permission. Filling a draft also requires Accessibility permission.

![Offline preview of the provider configuration window](documentation/design/provider-config-preview.png)

*Offline preview of the provider settings. DeepSeek and Jev keys are saved separately. Stored values are never shown in the form, and this image contains no real key.*

For models, OCR choices, Keychain and environment configuration, CSV format, and operating limits, see the [Mac usage guide](integrations/jev_mac/README.md) (Chinese).

## Verification and status

```bash
python3 -B scripts/validate_skill.py
python3 -B -m unittest discover -s tests -q
```

This is an **experimental source release**, without a signed or notarized `.app`. WeChat controls and layouts need verification on each supported version. If the input control cannot be verified, you can still copy a reply and paste it manually. Cloud image recognition and analysis send the selected content to the configured services.

The repository bundles Goutoujunshi's behavior rules and selected knowledge so that the desktop app can run on its own. The main project uses the [MIT License](LICENSE). Window perception and Accessibility modules are adapted from [jev-chat-jarvis-mac](https://github.com/jev-chat/jev-chat-jarvis-mac); its MIT notice is in [vendor/LICENSE](integrations/jev_mac/vendor/LICENSE).
