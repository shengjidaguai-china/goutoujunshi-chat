# 狗头军师 Chat

**Mac 上的聊天副驾：读屏、核对、分析、生成回复草稿。** 这是从[狗头军师](https://github.com/shengjidaguai-china/goutoujunshi)延伸出来的独立桌面项目。它保留狗头军师按场景取用关系知识、区分事实与推测、给出行动和停止条件的方式，并加入可拖动的悬浮窗。

![狗头军师 Chat 的接口配置窗口](documentation/design/provider-config-preview.png)

## 一轮怎么用

1. 打开 Mac 微信中的目标会话，点悬浮球的「读取对话」。
2. 核对识别出的原文、说话人、关系阶段和目标，再确认分析。
3. 查看对方**可能的意图**、判断把握、依据、军师建议和「候选回复排序」。打开「详细分析」可看事实、推测、未知、下一步与停止条件。
4. 选择候选并复制，或在确认当前会话和输入控件后填入**草稿**。发送由你决定。

默认使用 **Apple Vision 本地文字识别**；设置中可改为 **DeepSeek 图片识别**，此时聊天区域截图会发送至 DeepSeek 并产生接口用量。回复生成可用 DeepSeek 或自定义的 OpenAI 兼容接口。**TypeSafe Jev 是可选的策略判断层**：启用后先选策略，再由回复模型生成候选。两组 Key 分开配置，界面输入后存入本项目专用的 Mac 钥匙串条目；仓库不包含任何真实 Key。

「判断把握」是模型对意图推测的自评；候选百分比是本轮回复的相对推荐权重。它们都不是对方的真实意图概率、回复率或关系成功率。没有可靠依据时，界面会提示无法判断。

## 项目特色

- **像自己说话**：只参考当前会话中经过核对、确认为「我」的原话；「更像我一点」可重新调整候选口吻。不训练模型，也不读取其他会话来模仿。
- **把理由讲清楚**：每条候选可展开适用理由和代价；建议同时给观察窗口与停止条件，避免只产出一句话术。
- **关系档案可选择**：首次明确同意后才保存有限的对象背景，可查看、暂停、撤销和删除；不存整份聊天。
- **K 线有计算口径**：内置五组合成事件示例，也能导入核对过双方身份的 CSV，按每日消息方向绘图。图线不代表关系质量或爱意分数。
- **控制留给用户**：OCR 后先核对，自动分析默认关闭，填入前重新检查会话；程序不会替你点发送。

## 安装与启动

需要 macOS、Python 3.12 和 [`uv`](https://docs.astral.sh/uv/)。在仓库根目录运行：

```bash
cd integrations/jev_mac
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
./start.command --demo
```

`--demo` 使用合成对话，离线展示界面，不读取微信、不调用模型。真实使用时运行 `./start.command`；`./start.command --settings` 可直接打开设置，点击「接口与模型 → 配置接口」填写 DeepSeek Key，并按需填写 TypeSafe Jev Key。打开微信后，需要给**启动程序的终端**授予 macOS「屏幕录制」权限；使用「填入」还需要「辅助功能」权限。

模型、OCR、钥匙串、可选环境变量、K 线 CSV 格式和操作限制见 [Mac 使用说明](integrations/jev_mac/README.md)。

## 验证与状态

```bash
python3 -B scripts/validate_skill.py
python3 -B -m unittest discover -s tests -q
```

当前发布的是**源码实验版**，没有签名和公证的 `.app`。不同微信版本的控件与布局需要逐机核对；输入控件不可验证时仍可复制、手动粘贴。云端识图和分析会发送你确认范围内的内容到所选服务。

本项目包含狗头军师的行为规则与按需知识文件，以便桌面端独立运行。狗头军师主体采用 [MIT 许可](LICENSE)；窗口感知和辅助功能模块改编自 [jev-chat-jarvis-mac](https://github.com/jev-chat/jev-chat-jarvis-mac)，其 MIT 许可见 [vendor/LICENSE](integrations/jev_mac/vendor/LICENSE)。
