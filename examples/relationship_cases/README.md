# 关系趋势合成案例

这里的五组人物、聊天和日期均为虚构数据，不来自微信或用户档案。`timestamp,sender,message` CSV 可用于测试带时间戳的聊天分析；`manifest.json` 给出狗头军师的精简关系档案、可观察转折和预期判断。`sender=me` 固定为用户，`sender=other` 固定为对象，不能靠左右气泡或语气重新猜身份。

| 案例 | 聊天表现 | 期望看见的走势 | 不应得出的结论 |
| --- | --- | --- | --- |
| `mutual_warming` | 双方主动、邀约具体且兑现 | 稳步升温 | “一定喜欢”或关系成功概率 |
| `hot_then_cool` | 前期热聊，后期多次推迟且没有替代时间 | 前高后低 | 仅凭慢回断言动机 |
| `conflict_then_repair` | 失约、道歉、具体补救并兑现 | 下探后修复 | 一次道歉就等于问题解决 |
| `busy_but_reliable` | 回复少，但提前说明忙碌、给出时间并兑现 | 互动量低，可靠性不低 | 把低频率直接画成关系下跌 |
| `clear_boundary` | 对方明确表示不愿继续接触 | 收线并停止建议联系 | 用 K 线寻找“反转机会” |

这些 CSV 可以作为 [Relationship Candlestick Lab](https://github.com/ZhenyuanPAN822/relationship-candlestick-lab) 一类工具的输入，但本仓库目前**没有实现关系 K 线图或消息级指数评分**。`manifest.json` 的 `expected_pattern` 是案例设计预期，不是实际模型运行结果；先核对说话人和关键事件，再看图形是否与证据一致。K 线的 OHLC、成交量和技术指标不是爱意、忠诚或分手概率。

狗头军师的长期关系档案只应保存经同意的精简字段及必要关键事件。CSV 原文仅作测试输入，不应自动写进 `memory.sqlite3`。Mac 悬浮窗目前只有一组硬编码离线演示对话；这些案例尚未接入它的案例切换器。
