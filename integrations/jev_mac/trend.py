"""Local, evidence-labelled candlesticks for timestamped chat CSVs.

The candle is a running *message balance*: an ``other`` message adds one and
an ``me`` message subtracts one. It is not a relationship quality score.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = ROOT / "examples" / "relationship_cases"
MAX_BYTES = 4_000_000
MAX_MESSAGES = 20_000


@dataclass(frozen=True)
class Candle:
    date: str
    open: int
    high: int
    low: int
    close: int
    mine: int
    other: int
    events: tuple[str, ...] = ()

    @property
    def count(self):
        return self.mine + self.other


@dataclass(frozen=True)
class Trend:
    title: str
    candles: tuple[Candle, ...]
    source: str
    note: str = ""
    metric: str = "message_balance"

    @property
    def messages(self):
        return sum(c.count for c in self.candles)


def load_csv(path: str | Path, title: str = "导入的聊天记录") -> Trend:
    source = Path(path)
    if source.suffix.lower() != ".csv" or not source.is_file():
        raise ValueError("请选择带 timestamp,sender,message 列的 CSV 文件")
    if source.stat().st_size > MAX_BYTES:
        raise ValueError("聊天 CSV 超过 4 MB，请缩小时间范围后重试")
    candles: list[Candle] = []
    balance = 0
    previous_at: datetime | None = None
    count = 0
    try:
        with source.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or not {"timestamp", "sender", "message"}.issubset(reader.fieldnames):
                raise ValueError("CSV 需要 timestamp,sender,message 三列")
            for row in reader:
                count += 1
                if count > MAX_MESSAGES:
                    raise ValueError("聊天记录超过 20000 条，请缩小时间范围")
                at = datetime.fromisoformat((row.get("timestamp") or "").strip())
                if previous_at is not None and at < previous_at:
                    raise ValueError("聊天时间没有按升序排列")
                previous_at = at
                sender = (row.get("sender") or "").strip()
                if sender not in {"me", "other"}:
                    raise ValueError("sender 只接受 me／other；请先确认双方身份")
                if not (row.get("message") or "").strip():
                    raise ValueError("存在空消息，请先核对导出文件")
                date = at.date().isoformat()
                if not candles or candles[-1].date != date:
                    candles.append(Candle(date, balance, balance, balance, balance, 0, 0))
                current = candles[-1]
                balance += 1 if sender == "other" else -1
                events = current.events
                event = (row.get("event") or "").strip()
                if event:
                    if len(event) > 160:
                        raise ValueError("事件标注过长，请控制在 160 字以内")
                    events += (event,)
                candles[-1] = replace(current, high=max(current.high, balance),
                                      low=min(current.low, balance), close=balance,
                                      mine=current.mine + (sender == "me"),
                                      other=current.other + (sender == "other"), events=events)
    except (UnicodeError, csv.Error, TypeError, OverflowError) as exc:
        raise ValueError("聊天 CSV 无法读取，请检查编码、列名和时间格式") from exc
    except ValueError as exc:
        if "Invalid isoformat string" in str(exc):
            raise ValueError("timestamp 需要 YYYY-MM-DD HH:MM:SS 格式") from exc
        raise
    if not candles:
        raise ValueError("CSV 没有可分析的聊天记录")
    return Trend(title, tuple(candles), str(source))


def demo_cases() -> tuple[tuple[str, str], ...]:
    manifest = json.loads((DEMO_DIR / "manifest.json").read_text(encoding="utf-8"))
    return tuple((row["id"], row["title"]) for row in manifest["cases"])


def load_demo(case_id: str) -> Trend:
    manifest = json.loads((DEMO_DIR / "manifest.json").read_text(encoding="utf-8"))
    case = next((row for row in manifest["cases"] if row["id"] == case_id), None)
    if case is None:
        raise ValueError("没有这个合成案例")
    trend = load_csv(DEMO_DIR / case["csv"], case["title"] + " · 合成示例")
    illustrative = json.loads((Path(__file__).with_name("demo_kline.json")).read_text(encoding="utf-8"))
    rows = illustrative["cases"].get(case_id)
    if rows is None or len(rows) != len(trend.candles):
        raise ValueError("合成 K 线与聊天日期不匹配")
    events: dict[str, list[str]] = {}
    for event in case.get("key_events", []):
        events.setdefault(event["at"][:10], []).append(event["evidence"])
    candles = []
    previous = None
    for source_candle, (date, open_, high, low, close) in zip(trend.candles, rows):
        if date != source_candle.date or (previous is not None and open_ != previous) or not (
                0 <= low <= min(open_, close) <= max(open_, close) <= high <= 100):
            raise ValueError("合成 K 线开高低收格式不正确")
        candles.append(replace(source_candle, open=open_, high=high, low=low, close=close,
                               events=source_candle.events + tuple(events.get(date, ()))))
        previous = close
    return replace(trend, candles=tuple(candles), note=case["expected_pattern"],
                   metric="synthetic_event_index")
