#!/usr/bin/env python3
"""OKX 行情数据客户端 - 对接欧易公开行情 API
无需 API Key，直接调用即可获取 K线、最新价、深度、成交等数据。

扩展功能：
- 数据落库（CSV/JSON）
- 价格监控告警
- 技术指标计算（MA/EMA/RSI/MACD）
- 异步版本（aiohttp）
"""

import asyncio
import csv
import json
import os
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional, Callable, AsyncGenerator

import requests


BASE_URL = "https://www.okx.com"
WS_URL = "wss://ws.okx.com:8443/ws/v5/public"

INTERVAL_MAP = {
    "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1H": "1H", "2H": "2H", "4H": "4H", "6H": "6H", "12H": "12H",
    "1D": "1D", "1W": "1W", "1M": "1M",
}


class OKXMarketClient:
    def __init__(self, base_url: str = BASE_URL, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "OKXMarketClient/1.0",
        })

    def _get(self, path: str, params: Optional[Dict] = None) -> Dict:
        url = f"{self.base_url}{path}"
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "0":
            raise RuntimeError(f"OKX API error [{data.get('code')}]: {data.get('msg')}")
        return data

    def get_ticker(self, inst_id: str) -> Dict:
        data = self._get("/api/v5/market/ticker", {"instId": inst_id})
        item = data["data"][0]
        return {
            "inst_id": item["instId"],
            "last": float(item["last"]),
            "open24h": float(item["open24h"]),
            "high24h": float(item["high24h"]),
            "low24h": float(item["low24h"]),
            "vol24h": float(item["vol24h"]),
            "vol_ccy24h": float(item.get("volCcy24h", 0)),
            "pct_chg": float(item.get("pctChg", 0)) * 100,
            "ts": self._ts_to_dt(item["ts"]),
        }

    def get_tickers(self, inst_type: str = "SPOT") -> List[Dict]:
        data = self._get("/api/v5/market/tickers", {"instType": inst_type})
        return [
            {
                "inst_id": item["instId"],
                "last": float(item["last"]),
                "high24h": float(item["high24h"]),
                "low24h": float(item["low24h"]),
                "vol24h": float(item["vol24h"]),
                "pct_chg": round(float(item.get("pctChg", 0)) * 100, 2),
            }
            for item in data["data"]
        ]

    def get_candles(
        self,
        inst_id: str,
        bar: str = "1H",
        limit: int = 100,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> List[Dict]:
        if bar not in INTERVAL_MAP:
            raise ValueError(f"Invalid bar '{bar}', valid: {', '.join(INTERVAL_MAP)}")
        params = {"instId": inst_id, "bar": bar, "limit": limit}
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        data = self._get("/api/v5/market/candles", params)
        return [
            {
                "time": self._ts_to_dt(parts[0]),
                "open": float(parts[1]),
                "high": float(parts[2]),
                "low": float(parts[3]),
                "close": float(parts[4]),
                "vol": float(parts[5]),
                "vol_ccy": float(parts[6]) if len(parts) > 6 else 0.0,
            }
            for parts in data["data"]
        ]

    def get_orderbook(self, inst_id: str, depth: int = 20) -> Dict:
        data = self._get("/api/v5/market/books", {"instId": inst_id, "sz": depth})
        item = data["data"][0]
        return {
            "inst_id": inst_id,
            "ts": self._ts_to_dt(item["ts"]),
            "asks": [{"price": float(p[0]), "size": float(p[1])} for p in item["asks"]],
            "bids": [{"price": float(p[0]), "size": float(p[1])} for p in item["bids"]],
        }

    def get_trades(self, inst_id: str, limit: int = 100) -> List[Dict]:
        data = self._get("/api/v5/market/trades", {"instId": inst_id, "limit": limit})
        return [
            {
                "trade_id": item["tradeId"],
                "price": float(item["px"]),
                "size": float(item["sz"]),
                "side": item["side"],
                "time": self._ts_to_dt(item["ts"]),
            }
            for item in data["data"]
        ]

    def get_instruments(self, inst_type: str = "SPOT") -> List[Dict]:
        data = self._get("/api/v5/public/instruments", {"instType": inst_type})
        return [
            {
                "inst_id": item["instId"],
                "base_ccy": item.get("baseCcy", ""),
                "quote_ccy": item.get("quoteCcy", ""),
                "state": item.get("state", ""),
                "tick_sz": float(item.get("tickSz", 0)),
                "lot_sz": float(item.get("lotSz", 0)),
                "min_sz": float(item.get("minSz", 0)),
                "ct_type": item.get("ctType", ""),
            }
            for item in data["data"]
        ]

    def subscribe_tickers_stream(
        self,
        inst_ids: List[str],
        on_message=None,
        max_duration: int = 30,
    ):
        try:
            import websocket
        except ImportError:
            raise RuntimeError("需要 websocket-client: pip install websocket-client")

        client = self

        def on_open(ws):
            sub = {
                "op": "subscribe",
                "args": [{"channel": "tickers", "instId": iid} for iid in inst_ids],
            }
            ws.send(json.dumps(sub))
            print(f"已订阅实时行情: {', '.join(inst_ids)}")

        def on_msg(ws, msg):
            try:
                payload = json.loads(msg)
                if "data" in payload and on_message:
                    for item in payload["data"]:
                        on_message({
                            "inst_id": item["instId"],
                            "last": float(item["last"]),
                            "pct_chg": round(float(item.get("pctChg", 0)) * 100, 2),
                            "ts": client._ts_to_dt(item["ts"]),
                        })
            except Exception as e:
                print(f"解析消息失败: {e}")

        ws = websocket.WebSocketApp(WS_URL, on_open=on_open, on_message=on_msg)
        print(f"WebSocket 连接中 (最长 {max_duration} 秒, Ctrl+C 退出)...")
        try:
            ws.run_forever(ping_interval=20, ping_timeout=15)
        except KeyboardInterrupt:
            print("\n已停止订阅")

    @staticmethod
    def _ts_to_dt(ts_ms: str) -> datetime:
        return datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc)


# ============================================================================
# 数据落库模块
# ============================================================================

class DataStorage:
    """数据落库：支持 CSV 和 JSON 格式"""

    def __init__(self, output_dir: str = "data/okx"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save_ticker_csv(self, ticker: Dict, filename: str = None):
        """保存单个 ticker 到 CSV（追加模式）"""
        if filename is None:
            filename = f"{ticker['inst_id'].replace('-', '_')}_ticker.csv"
        filepath = os.path.join(self.output_dir, filename)

        file_exists = os.path.exists(filepath)
        with open(filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "inst_id", "last", "open24h", "high24h", "low24h", "vol24h", "pct_chg"])
            writer.writerow([
                ticker["ts"].strftime("%Y-%m-%d %H:%M:%S"),
                ticker["inst_id"],
                ticker["last"],
                ticker["open24h"],
                ticker["high24h"],
                ticker["low24h"],
                ticker["vol24h"],
                ticker["pct_chg"],
            ])
        return filepath

    def save_tickers_json(self, tickers: List[Dict], filename: str = "tickers.json"):
        """保存批量 tickers 到 JSON"""
        filepath = os.path.join(self.output_dir, filename)
        data = {
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(tickers),
            "tickers": tickers,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filepath

    def save_candles_csv(self, candles: List[Dict], inst_id: str, bar: str = "1H"):
        """保存 K线数据到 CSV"""
        filename = f"{inst_id.replace('-', '_')}_{bar}.csv"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "open", "high", "low", "close", "vol", "vol_ccy"])
            for c in candles:
                writer.writerow([
                    c["time"].strftime("%Y-%m-%d %H:%M:%S"),
                    c["open"],
                    c["high"],
                    c["low"],
                    c["close"],
                    c["vol"],
                    c["vol_ccy"],
                ])
        return filepath

    def save_candles_json(self, candles: List[Dict], inst_id: str, bar: str = "1H"):
        """保存 K线数据到 JSON"""
        filename = f"{inst_id.replace('-', '_')}_{bar}.json"
        filepath = os.path.join(self.output_dir, filename)

        data = {
            "inst_id": inst_id,
            "bar": bar,
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(candles),
            "candles": [
                {
                    "time": c["time"].strftime("%Y-%m-%d %H:%M:%S"),
                    "open": c["open"],
                    "high": c["high"],
                    "low": c["low"],
                    "close": c["close"],
                    "vol": c["vol"],
                    "vol_ccy": c["vol_ccy"],
                }
                for c in candles
            ],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filepath

    def load_candles_csv(self, inst_id: str, bar: str = "1H") -> List[Dict]:
        """从 CSV 加载 K线数据"""
        filename = f"{inst_id.replace('-', '_')}_{bar}.csv"
        filepath = os.path.join(self.output_dir, filename)

        if not os.path.exists(filepath):
            return []

        candles = []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                candles.append({
                    "time": datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "vol": float(row["vol"]),
                    "vol_ccy": float(row.get("vol_ccy", 0)),
                })
        return candles


# ============================================================================
# 价格监控告警模块
# ============================================================================

class PriceMonitor:
    """价格监控告警：支持价格阈值、涨跌幅阈值告警"""

    def __init__(
        self,
        client: OKXMarketClient,
        storage: Optional[DataStorage] = None,
        alert_callback: Optional[Callable[[Dict], None]] = None,
    ):
        self.client = client
        self.storage = storage
        self.alert_callback = alert_callback or self._default_alert
        self.rules: Dict[str, Dict] = {}  # inst_id -> rule config
        self.last_prices: Dict[str, float] = {}

    def add_rule(
        self,
        inst_id: str,
        price_above: Optional[float] = None,
        price_below: Optional[float] = None,
        pct_change_above: Optional[float] = None,
        pct_change_below: Optional[float] = None,
    ):
        """添加监控规则"""
        self.rules[inst_id] = {
            "price_above": price_above,
            "price_below": price_below,
            "pct_change_above": pct_change_above,
            "pct_change_below": pct_change_below,
        }
        print(f"已添加监控规则: {inst_id}")

    def remove_rule(self, inst_id: str):
        """移除监控规则"""
        if inst_id in self.rules:
            del self.rules[inst_id]
            if inst_id in self.last_prices:
                del self.last_prices[inst_id]
            print(f"已移除监控规则: {inst_id}")

    def check(self) -> List[Dict]:
        """检查所有监控规则，返回触发的告警列表"""
        alerts = []
        for inst_id, rule in self.rules.items():
            try:
                ticker = self.client.get_ticker(inst_id)
                current_price = ticker["last"]
                pct_chg = ticker["pct_chg"]

                # 价格上限告警
                if rule["price_above"] and current_price > rule["price_above"]:
                    alerts.append({
                        "type": "price_above",
                        "inst_id": inst_id,
                        "current": current_price,
                        "threshold": rule["price_above"],
                        "ts": ticker["ts"],
                    })

                # 价格下限告警
                if rule["price_below"] and current_price < rule["price_below"]:
                    alerts.append({
                        "type": "price_below",
                        "inst_id": inst_id,
                        "current": current_price,
                        "threshold": rule["price_below"],
                        "ts": ticker["ts"],
                    })

                # 涨幅告警
                if rule["pct_change_above"] and pct_chg > rule["pct_change_above"]:
                    alerts.append({
                        "type": "pct_change_above",
                        "inst_id": inst_id,
                        "current_pct": pct_chg,
                        "threshold": rule["pct_change_above"],
                        "price": current_price,
                        "ts": ticker["ts"],
                    })

                # 跌幅告警
                if rule["pct_change_below"] and pct_chg < rule["pct_change_below"]:
                    alerts.append({
                        "type": "pct_change_below",
                        "inst_id": inst_id,
                        "current_pct": pct_chg,
                        "threshold": rule["pct_change_below"],
                        "price": current_price,
                        "ts": ticker["ts"],
                    })

                self.last_prices[inst_id] = current_price

                # 保存数据
                if self.storage:
                    self.storage.save_ticker_csv(ticker)

            except Exception as e:
                print(f"检查 {inst_id} 失败: {e}")

        # 触发告警回调
        for alert in alerts:
            self.alert_callback(alert)

        return alerts

    def run_periodic(self, interval_seconds: int = 60, max_runs: int = None):
        """周期性运行监控"""
        run_count = 0
        print(f"启动价格监控，间隔 {interval_seconds} 秒...")
        while True:
            if max_runs and run_count >= max_runs:
                break
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 检查监控规则...")
            alerts = self.check()
            if not alerts:
                print("  无告警触发")
            time.sleep(interval_seconds)
            run_count += 1

    def _default_alert(self, alert: Dict):
        """默认告警输出"""
        ts_str = alert["ts"].strftime("%Y-%m-%d %H:%M:%S UTC")
        if alert["type"] == "price_above":
            print(f"  ⚠️ [{ts_str}] {alert['inst_id']} 价格突破上限: {alert['current']} > {alert['threshold']}")
        elif alert["type"] == "price_below":
            print(f"  ⚠️ [{ts_str}] {alert['inst_id']} 价格跌破下限: {alert['current']} < {alert['threshold']}")
        elif alert["type"] == "pct_change_above":
            print(f"  ⚠️ [{ts_str}] {alert['inst_id']} 涨幅超阈值: {alert['current_pct']:.2f}% > {alert['threshold']}%")
        elif alert["type"] == "pct_change_below":
            print(f"  ⚠️ [{ts_str}] {alert['inst_id']} 跌幅超阈值: {alert['current_pct']:.2f}% < {alert['threshold']}%")


# ============================================================================
# 技术指标计算模块
# ============================================================================

class TechnicalIndicators:
    """技术指标计算：MA、EMA、RSI、MACD"""

    @staticmethod
    def ma(candles: List[Dict], period: int = 20) -> List[float]:
        """简单移动平均线 MA"""
        if len(candles) < period:
            return []
        closes = [c["close"] for c in candles]
        ma_values = []
        for i in range(period - 1, len(closes)):
            ma = sum(closes[i - period + 1:i + 1]) / period
            ma_values.append(ma)
        return ma_values

    @staticmethod
    def ema(candles: List[Dict], period: int = 20) -> List[float]:
        """指数移动平均线 EMA"""
        if len(candles) < period:
            return []
        closes = [c["close"] for c in candles]
        multiplier = 2 / (period + 1)

        # 初始 EMA = 前 period 个收盘价的 SMA
        initial_sma = sum(closes[:period]) / period
        ema_values = [initial_sma]

        for i in range(period, len(closes)):
            ema = (closes[i] - ema_values[-1]) * multiplier + ema_values[-1]
            ema_values.append(ema)

        return ema_values

    @staticmethod
    def rsi(candles: List[Dict], period: int = 14) -> List[float]:
        """相对强弱指数 RSI"""
        if len(candles) < period + 1:
            return []
        closes = [c["close"] for c in candles]

        # 计算价格变化
        changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

        # 分离上涨和下跌
        gains = [max(0, c) for c in changes]
        losses = [abs(min(0, c)) for c in changes]

        # 初始平均
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        rsi_values = []
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - (100 / (1 + rs)))

        # 后续使用平滑平均
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

            if avg_loss == 0:
                rsi_values.append(100.0)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100 - (100 / (1 + rs)))

        return rsi_values

    @staticmethod
    def macd(
        candles: List[Dict],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> Dict[str, List[float]]:
        """MACD 指标：返回 MACD线、信号线、柱状图"""
        ema_fast = TechnicalIndicators.ema(candles, fast_period)
        ema_slow = TechnicalIndicators.ema(candles, slow_period)

        if len(ema_fast) < len(ema_slow):
            return {"macd": [], "signal": [], "histogram": []}

        # MACD 线 = 快线EMA - 慢线EMA
        # 需要对齐：慢线EMA 从第 slow_period-1 个开始，快线从第 fast_period-1 个开始
        offset = slow_period - fast_period
        macd_line = [ema_fast[i + offset] - ema_slow[i] for i in range(len(ema_slow))]

        # 信号线 = MACD 线的 EMA
        # 构造虚拟 candles 用于计算 EMA（用 MACD 值代替 close）
        if len(macd_line) < signal_period:
            return {"macd": macd_line, "signal": [], "histogram": []}

        # 手动计算信号线 EMA
        multiplier = 2 / (signal_period + 1)
        initial_sma = sum(macd_line[:signal_period]) / signal_period
        signal_line = [initial_sma]
        for i in range(signal_period, len(macd_line)):
            sig = (macd_line[i] - signal_line[-1]) * multiplier + signal_line[-1]
            signal_line.append(sig)

        # 柱状图 = MACD - 信号线
        # 对齐长度
        histogram = []
        for i in range(len(signal_line)):
            idx = i + signal_period - 1
            if idx < len(macd_line):
                histogram.append(macd_line[idx] - signal_line[i])

        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram,
        }

    @staticmethod
    def bollinger_bands(
        candles: List[Dict],
        period: int = 20,
        std_dev: float = 2.0,
    ) -> Dict[str, List[float]]:
        """布林带：中轨（MA）、上轨、下轨"""
        if len(candles) < period:
            return {"middle": [], "upper": [], "lower": []}

        closes = [c["close"] for c in candles]
        middle = TechnicalIndicators.ma(candles, period)

        upper = []
        lower = []

        for i in range(period - 1, len(closes)):
            window = closes[i - period + 1:i + 1]
            mean = middle[i - period + 1]
            variance = sum((x - mean) ** 2 for x in window) / period
            std = variance ** 0.5
            upper.append(mean + std_dev * std)
            lower.append(mean - std_dev * std)

        return {"middle": middle, "upper": upper, "lower": lower}


# ============================================================================
# 异步客户端（aiohttp）
# ============================================================================

class AsyncOKXMarketClient:
    """异步 OKX 行情客户端，使用 aiohttp"""

    def __init__(self, base_url: str = BASE_URL, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = None

    async def _get_session(self):
        if self._session is None:
            try:
                import aiohttp
            except ImportError:
                raise RuntimeError("需要 aiohttp: pip install aiohttp")
            self._session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "AsyncOKXClient/1.0",
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )
        return self._session

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None

    async def _get(self, path: str, params: Optional[Dict] = None) -> Dict:
        session = await self._get_session()
        url = f"{self.base_url}{path}"
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
            if data.get("code") != "0":
                raise RuntimeError(f"OKX API error [{data.get('code')}]: {data.get('msg')}")
            return data

    async def get_ticker(self, inst_id: str) -> Dict:
        data = await self._get("/api/v5/market/ticker", {"instId": inst_id})
        item = data["data"][0]
        return {
            "inst_id": item["instId"],
            "last": float(item["last"]),
            "open24h": float(item["open24h"]),
            "high24h": float(item["high24h"]),
            "low24h": float(item["low24h"]),
            "vol24h": float(item["vol24h"]),
            "vol_ccy24h": float(item.get("volCcy24h", 0)),
            "pct_chg": float(item.get("pctChg", 0)) * 100,
            "ts": self._ts_to_dt(item["ts"]),
        }

    async def get_tickers(self, inst_type: str = "SPOT") -> List[Dict]:
        data = await self._get("/api/v5/market/tickers", {"instType": inst_type})
        return [
            {
                "inst_id": item["instId"],
                "last": float(item["last"]),
                "high24h": float(item["high24h"]),
                "low24h": float(item["low24h"]),
                "vol24h": float(item["vol24h"]),
                "pct_chg": round(float(item.get("pctChg", 0)) * 100, 2),
            }
            for item in data["data"]
        ]

    async def get_candles(
        self,
        inst_id: str,
        bar: str = "1H",
        limit: int = 100,
    ) -> List[Dict]:
        if bar not in INTERVAL_MAP:
            raise ValueError(f"Invalid bar '{bar}'")
        data = await self._get("/api/v5/market/candles", {"instId": inst_id, "bar": bar, "limit": limit})
        return [
            {
                "time": self._ts_to_dt(parts[0]),
                "open": float(parts[1]),
                "high": float(parts[2]),
                "low": float(parts[3]),
                "close": float(parts[4]),
                "vol": float(parts[5]),
                "vol_ccy": float(parts[6]) if len(parts) > 6 else 0.0,
            }
            for parts in data["data"]
        ]

    async def get_multiple_tickers(self, inst_ids: List[str]) -> Dict[str, Dict]:
        """并发获取多个 ticker"""
        tasks = [self.get_ticker(inst_id) for inst_id in inst_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            inst_id: result if not isinstance(result, Exception) else {"error": str(result)}
            for inst_id, result in zip(inst_ids, results)
        }

    @staticmethod
    def _ts_to_dt(ts_ms: str) -> datetime:
        return datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc)


def _print_ticker(t: Dict):
    print(
        f"\n[最新行情] {t['inst_id']}\n"
        f"  最新价: {t['last']:.2f}\n"
        f"  24h 涨跌: {t['pct_chg']:+.2f}%\n"
        f"  24h 最高/最低: {t['high24h']:.2f} / {t['low24h']:.2f}\n"
        f"  24h 成交量: {t['vol24h']:.4f}\n"
        f"  数据时间: {t['ts'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )


def _print_orderbook(book: Dict):
    print(f"\n[盘口] {book['inst_id']}  (时间: {book['ts'].strftime('%H:%M:%S')} UTC)")
    print(f"{'卖单':>20}")
    for ask in book["asks"][:5]:
        print(f"  {ask['price']:>12.2f}    {ask['size']:>12.4f}")
    print(f"  ------------------------")
    for bid in book["bids"][:5]:
        print(f"  {bid['price']:>12.2f}    {bid['size']:>12.4f}")
    print(f"{'买单':>20}")


def _print_candles(candles: List[Dict], inst_id: str):
    print(f"\n[K线] {inst_id}  最近 {len(candles)} 根")
    print(f"{'时间':<22} {'开盘':>10} {'最高':>10} {'最低':>10} {'收盘':>10} {'成交量':>12}")
    for c in candles[-10:]:
        print(
            f"{c['time'].strftime('%Y-%m-%d %H:%M'):<22} "
            f"{c['open']:>10.2f} {c['high']:>10.2f} "
            f"{c['low']:>10.2f} {c['close']:>10.2f} "
            f"{c['vol']:>12.4f}"
        )


def main():
    """演示所有功能"""
    client = OKXMarketClient()
    storage = DataStorage()
    targets = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]

    print("=" * 60)
    print("OKX 欧易行情数据客户端 - 完整功能演示")
    print("=" * 60)

    # 1. 获取行情
    print("\n【1. 获取实时行情】")
    for inst_id in targets:
        try:
            ticker = client.get_ticker(inst_id)
            _print_ticker(ticker)
            # 保存到 CSV
            storage.save_ticker_csv(ticker)
        except Exception as e:
            print(f"\n获取 {inst_id} 失败: {e}")

    # 2. 获取盘口
    print("\n【2. 获取盘口深度】")
    try:
        book = client.get_orderbook("BTC-USDT", depth=10)
        _print_orderbook(book)
    except Exception as e:
        print(f"\n获取盘口失败: {e}")

    # 3. 获取 K线并计算技术指标
    print("\n【3. 获取 K线 + 技术指标】")
    try:
        candles = client.get_candles("BTC-USDT", bar="1H", limit=100)
        _print_candles(candles, "BTC-USDT (1H)")

        # 保存 K线
        csv_path = storage.save_candles_csv(candles, "BTC-USDT", "1H")
        json_path = storage.save_candles_json(candles, "BTC-USDT", "1H")
        print(f"\nK线已保存: {csv_path}, {json_path}")

        # 计算技术指标
        print("\n--- 技术指标 ---")
        ma20 = TechnicalIndicators.ma(candles, 20)
        ema20 = TechnicalIndicators.ema(candles, 20)
        rsi14 = TechnicalIndicators.rsi(candles, 14)
        macd = TechnicalIndicators.macd(candles)
        bb = TechnicalIndicators.bollinger_bands(candles, 20, 2.0)

        if ma20:
            print(f"MA(20) 最新值: {ma20[-1]:.2f}")
        if ema20:
            print(f"EMA(20) 最新值: {ema20[-1]:.2f}")
        if rsi14:
            print(f"RSI(14) 最新值: {rsi14[-1]:.2f}")
        if macd["macd"]:
            print(f"MACD 最新值: {macd['macd'][-1]:.4f}")
        if bb["middle"]:
            print(f"布林带中轨: {bb['middle'][-1]:.2f}, 上轨: {bb['upper'][-1]:.2f}, 下轨: {bb['lower'][-1]:.2f}")

    except Exception as e:
        print(f"\n获取K线失败: {e}")

    # 4. 价格监控演示（单次检查）
    print("\n【4. 价格监控告警】")
    monitor = PriceMonitor(client, storage)
    # 添加监控规则（示例阈值，可根据实际价格调整）
    monitor.add_rule("BTC-USDT", price_above=100000, price_below=50000, pct_change_above=5, pct_change_below=-5)
    monitor.add_rule("ETH-USDT", price_above=5000, pct_change_above=3)
    print("执行单次监控检查...")
    alerts = monitor.check()
    if not alerts:
        print("当前无告警触发")

    # 5. 异步客户端演示
    print("\n【5. 异步客户端演示】")
    print("提示: 异步版本需要 aiohttp，可在代码中调用 AsyncOKXMarketClient")

    print("\n" + "=" * 60)
    print("功能列表:")
    print("  - OKXMarketClient: 同步行情客户端")
    print("  - AsyncOKXMarketClient: 异步行情客户端（aiohttp）")
    print("  - DataStorage: 数据落库（CSV/JSON）")
    print("  - PriceMonitor: 价格监控告警")
    print("  - TechnicalIndicators: 技术指标（MA/EMA/RSI/MACD/布林带）")
    print("  - subscribe_tickers_stream(): WebSocket 实时推送")
    print("=" * 60)


async def async_demo():
    """异步客户端演示"""
    client = AsyncOKXMarketClient()
    try:
        # 并发获取多个 ticker
        results = await client.get_multiple_tickers(["BTC-USDT", "ETH-USDT", "SOL-USDT"])
        for inst_id, data in results.items():
            if "error" in data:
                print(f"{inst_id}: 错误 - {data['error']}")
            else:
                print(f"{inst_id}: 最新价 {data['last']:.2f}, 24h涨跌 {data['pct_chg']:.2f}%")
    finally:
        await client.close()


if __name__ == "__main__":
    main()
