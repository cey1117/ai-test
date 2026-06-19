#!/usr/bin/env python3
"""OKX 行情数据客户端 - 完整实现
包含：REST API、WebSocket、技术指标、价格监控、数据落库、异步客户端
"""

import asyncio
import csv
import json
import os
import time
import random
from datetime import datetime, timezone
from typing import List, Dict, Optional, Callable

import requests


BASE_URL = "https://www.okx.com"
WS_URL = "wss://ws.okx.com:8443/ws/v5/public"

INTERVAL_MAP = {
    "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1H": "1H", "2H": "2H", "4H": "4H", "6H": "6H", "12H": "12H",
    "1D": "1D", "1W": "1W", "1M": "1M",
}


# ============================================================================
# 模拟数据生成器（用于测试/演示）
# ============================================================================

class MockOKXClient:
    """模拟 OKX API 响应，用于无法访问外网的环境"""

    BASE_PRICES = {
        "BTC-USDT": 96000,
        "ETH-USDT": 3200,
        "SOL-USDT": 180,
        "DOGE-USDT": 0.35,
        "XRP-USDT": 2.5,
    }

    @classmethod
    def _mock_ticker(cls, inst_id: str) -> Dict:
        base = cls.BASE_PRICES.get(inst_id, 100)
        noise = base * 0.005 * (random.random() - 0.5)
        price = base + noise
        pct = (random.random() - 0.5) * 10
        return {
            "instId": inst_id,
            "last": f"{price:.2f}",
            "open24h": f"{price * (1 - pct/100 * 0.3):.2f}",
            "high24h": f"{price * (1 + abs(pct)/100 * 0.5):.2f}",
            "low24h": f"{price * (1 - abs(pct)/100 * 0.5):.2f}",
            "vol24h": f"{random.uniform(1000, 50000):.4f}",
            "volCcy24h": f"{random.uniform(50000, 2000000):.4f}",
            "pctChg": f"{pct/100:.6f}",
            "ts": str(int(time.time() * 1000)),
        }

    @classmethod
    def _mock_candles(cls, inst_id: str, bar: str, limit: int) -> List[List]:
        base = cls.BASE_PRICES.get(inst_id, 100)
        now = datetime.now(timezone.utc)
        bar_seconds = {"1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800,
                       "1H": 3600, "2H": 7200, "4H": 14400, "6H": 21600, "12H": 43200,
                       "1D": 86400, "1W": 604800, "1M": 2592000}
        interval = bar_seconds.get(bar, 3600)

        candles = []
        price = base
        for i in range(limit):
            ts = now.timestamp() - interval * (limit - i)
            open_p = price
            change = price * 0.005 * (random.random() - 0.5)
            high = max(open_p, open_p + change) * (1 + random.random() * 0.005)
            low = min(open_p, open_p + change) * (1 - random.random() * 0.005)
            close = open_p + change
            vol = random.uniform(10, 1000)
            vol_ccy = vol * close
            price = close
            candles.append([
                str(int(ts * 1000)),
                f"{open_p:.2f}", f"{high:.2f}", f"{low:.2f}", f"{close:.2f}",
                f"{vol:.4f}", f"{vol_ccy:.4f}",
            ])
        return candles

    @classmethod
    def _mock_orderbook(cls, inst_id: str, depth: int) -> Dict:
        base = cls.BASE_PRICES.get(inst_id, 100)
        mid = base
        asks, bids = [], []
        for i in range(depth):
            ask_p = mid * (1 + (i + 1) * 0.0002)
            bid_p = mid * (1 - (i + 1) * 0.0002)
            asks.append([f"{ask_p:.2f}", f"{random.uniform(0.01, 10):.4f}"])
            bids.append([f"{bid_p:.2f}", f"{random.uniform(0.01, 10):.4f}"])
        return {
            "instId": inst_id,
            "asks": asks,
            "bids": bids,
            "ts": str(int(time.time() * 1000)),
        }


# ============================================================================
# 同步行情客户端
# ============================================================================

class OKXMarketClient:
    """OKX 市场行情客户端，支持 REST API"""

    def __init__(self, base_url: str = BASE_URL, timeout: int = 10, use_mock: bool = False):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.use_mock = use_mock
        if not use_mock:
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
        if self.use_mock:
            item = MockOKXClient._mock_ticker(inst_id)
        else:
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
        if self.use_mock:
            return [
                {
                    "inst_id": inst_id,
                    "last": float(MockOKXClient._mock_ticker(inst_id)["last"]),
                    "high24h": float(MockOKXClient._mock_ticker(inst_id)["high24h"]),
                    "low24h": float(MockOKXClient._mock_ticker(inst_id)["low24h"]),
                    "vol24h": float(MockOKXClient._mock_ticker(inst_id)["vol24h"]),
                    "pct_chg": round(float(MockOKXClient._mock_ticker(inst_id)["pctChg"]) * 100, 2),
                }
                for inst_id in MockOKXClient.BASE_PRICES
            ]
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

    def get_candles(self, inst_id: str, bar: str = "1H", limit: int = 100) -> List[Dict]:
        if bar not in INTERVAL_MAP:
            raise ValueError(f"Invalid bar '{bar}', valid: {', '.join(INTERVAL_MAP)}")
        if self.use_mock:
            raw = MockOKXClient._mock_candles(inst_id, bar, limit)
        else:
            data = self._get("/api/v5/market/candles", {"instId": inst_id, "bar": bar, "limit": limit})
            raw = data["data"]
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
            for parts in raw
        ]

    def get_orderbook(self, inst_id: str, depth: int = 20) -> Dict:
        if self.use_mock:
            item = MockOKXClient._mock_orderbook(inst_id, depth)
        else:
            data = self._get("/api/v5/market/books", {"instId": inst_id, "sz": depth})
            item = data["data"][0]
        return {
            "inst_id": inst_id,
            "ts": self._ts_to_dt(item["ts"]),
            "asks": [{"price": float(p[0]), "size": float(p[1])} for p in item["asks"]],
            "bids": [{"price": float(p[0]), "size": float(p[1])} for p in item["bids"]],
        }

    def get_trades(self, inst_id: str, limit: int = 100) -> List[Dict]:
        if self.use_mock:
            now = time.time()
            return [
                {
                    "trade_id": str(int(now * 1000) - i * 100),
                    "price": float(MockOKXClient._mock_ticker(inst_id)["last"]) * (1 + (random.random()-0.5)*0.001),
                    "size": random.uniform(0.01, 5),
                    "side": random.choice(["buy", "sell"]),
                    "time": datetime.fromtimestamp(now - i, tz=timezone.utc),
                }
                for i in range(min(limit, 20))
            ]
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
        if self.use_mock:
            return [
                {"inst_id": inst_id, "base_ccy": inst_id.split("-")[0], "quote_ccy": inst_id.split("-")[1]}
                for inst_id in MockOKXClient.BASE_PRICES
            ]
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

    def subscribe_tickers_stream(self, inst_ids: List[str], on_message=None, max_duration: int = 30):
        """模拟 WebSocket 实时推送（实际环境请用真实 websocket-client）"""
        print(f"[模拟] WebSocket 订阅: {', '.join(inst_ids)} (持续 {max_duration} 秒)")
        end = time.time() + max_duration
        while time.time() < end:
            for inst_id in inst_ids:
                ticker = self.get_ticker(inst_id)
                if on_message:
                    on_message(ticker)
            time.sleep(2)

    @staticmethod
    def _ts_to_dt(ts_ms: str) -> datetime:
        return datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc)


# ============================================================================
# 数据落库
# ============================================================================

class DataStorage:
    """数据持久化：CSV 追加、JSON 全量、加载回读"""

    def __init__(self, output_dir: str = "data/okx"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save_ticker_csv(self, ticker: Dict, filename: str = None) -> str:
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
                ticker["inst_id"], ticker["last"], ticker["open24h"],
                ticker["high24h"], ticker["low24h"], ticker["vol24h"], ticker["pct_chg"],
            ])
        return filepath

    def save_tickers_json(self, tickers: List[Dict], filename: str = "tickers.json") -> str:
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "count": len(tickers),
                "tickers": tickers,
            }, f, ensure_ascii=False, indent=2)
        return filepath

    def save_candles_csv(self, candles: List[Dict], inst_id: str, bar: str = "1H") -> str:
        filename = f"{inst_id.replace('-', '_')}_{bar}.csv"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "open", "high", "low", "close", "vol", "vol_ccy"])
            for c in candles:
                writer.writerow([
                    c["time"].strftime("%Y-%m-%d %H:%M:%S"),
                    c["open"], c["high"], c["low"], c["close"], c["vol"], c["vol_ccy"],
                ])
        return filepath

    def save_candles_json(self, candles: List[Dict], inst_id: str, bar: str = "1H") -> str:
        filename = f"{inst_id.replace('-', '_')}_{bar}.json"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "inst_id": inst_id, "bar": bar,
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "count": len(candles),
                "candles": [{"time": c["time"].strftime("%Y-%m-%d %H:%M:%S"),
                             "open": c["open"], "high": c["high"],
                             "low": c["low"], "close": c["close"],
                             "vol": c["vol"], "vol_ccy": c["vol_ccy"]} for c in candles],
            }, f, ensure_ascii=False, indent=2)
        return filepath

    def load_candles_csv(self, inst_id: str, bar: str = "1H") -> List[Dict]:
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
                    "open": float(row["open"]), "high": float(row["high"]),
                    "low": float(row["low"]), "close": float(row["close"]),
                    "vol": float(row["vol"]), "vol_ccy": float(row.get("vol_ccy", 0)),
                })
        return candles


# ============================================================================
# 价格监控告警
# ============================================================================

class PriceMonitor:
    """价格监控，支持价格阈值 + 涨跌幅阈值"""

    def __init__(self, client: OKXMarketClient, storage: Optional[DataStorage] = None,
                 alert_callback: Optional[Callable[[Dict], None]] = None):
        self.client = client
        self.storage = storage
        self.alert_callback = alert_callback or self._default_alert
        self.rules: Dict[str, Dict] = {}
        self.last_prices: Dict[str, float] = {}

    def add_rule(self, inst_id: str, price_above: float = None, price_below: float = None,
                 pct_change_above: float = None, pct_change_below: float = None):
        self.rules[inst_id] = {
            "price_above": price_above, "price_below": price_below,
            "pct_change_above": pct_change_above, "pct_change_below": pct_change_below,
        }

    def remove_rule(self, inst_id: str):
        self.rules.pop(inst_id, None)
        self.last_prices.pop(inst_id, None)

    def check(self) -> List[Dict]:
        alerts = []
        for inst_id, rule in self.rules.items():
            try:
                ticker = self.client.get_ticker(inst_id)
                price = ticker["last"]
                pct = ticker["pct_chg"]

                if rule.get("price_above") and price > rule["price_above"]:
                    alerts.append({"type": "price_above", "inst_id": inst_id,
                                   "current": price, "threshold": rule["price_above"], "ts": ticker["ts"]})
                if rule.get("price_below") and price < rule["price_below"]:
                    alerts.append({"type": "price_below", "inst_id": inst_id,
                                   "current": price, "threshold": rule["price_below"], "ts": ticker["ts"]})
                if rule.get("pct_change_above") and pct > rule["pct_change_above"]:
                    alerts.append({"type": "pct_change_above", "inst_id": inst_id,
                                   "current_pct": pct, "threshold": rule["pct_change_above"],
                                   "price": price, "ts": ticker["ts"]})
                if rule.get("pct_change_below") and pct < rule["pct_change_below"]:
                    alerts.append({"type": "pct_change_below", "inst_id": inst_id,
                                   "current_pct": pct, "threshold": rule["pct_change_below"],
                                   "price": price, "ts": ticker["ts"]})

                self.last_prices[inst_id] = price
                if self.storage:
                    self.storage.save_ticker_csv(ticker)
            except Exception as e:
                print(f"  检查 {inst_id} 失败: {e}")

        for alert in alerts:
            self.alert_callback(alert)
        return alerts

    def run_periodic(self, interval_seconds: int = 60, max_runs: int = None):
        count = 0
        print(f"启动价格监控，间隔 {interval_seconds} 秒 (Ctrl+C 退出)...")
        while True:
            if max_runs and count >= max_runs:
                break
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 检查监控规则...")
            alerts = self.check()
            if not alerts:
                print("  无告警触发")
            time.sleep(interval_seconds)
            count += 1

    def _default_alert(self, alert: Dict):
        ts = alert["ts"].strftime("%H:%M:%S")
        icons = {"price_above": "↑↑↑", "price_below": "↓↓↓", "pct_change_above": "📈", "pct_change_below": "📉"}
        icon = icons.get(alert["type"], "⚠️")
        if alert["type"] in ("price_above", "price_below"):
            print(f"  {icon} [{ts}] {alert['inst_id']} {alert['type'].replace('_', ' ')}: "
                  f"{alert['current']:.2f} {'>' if 'above' in alert['type'] else '<'} {alert['threshold']}")
        else:
            print(f"  {icon} [{ts}] {alert['inst_id']} {alert['type'].replace('_', ' ')}: "
                  f"{alert['current_pct']:+.2f}% (阈值 {alert['threshold']:+.2f}%)")


# ============================================================================
# 技术指标
# ============================================================================

class TechnicalIndicators:

    @staticmethod
    def ma(candles: List[Dict], period: int = 20) -> List[float]:
        if len(candles) < period:
            return []
        closes = [c["close"] for c in candles]
        return [sum(closes[i - period + 1:i + 1]) / period for i in range(period - 1, len(closes))]

    @staticmethod
    def ema(candles: List[Dict], period: int = 20) -> List[float]:
        if len(candles) < period:
            return []
        closes = [c["close"] for c in candles]
        k = 2 / (period + 1)
        ema = [sum(closes[:period]) / period]
        for i in range(period, len(closes)):
            ema.append((closes[i] - ema[-1]) * k + ema[-1])
        return ema

    @staticmethod
    def rsi(candles: List[Dict], period: int = 14) -> List[float]:
        if len(candles) < period + 1:
            return []
        closes = [c["close"] for c in candles]
        changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        gains = [max(0, c) for c in changes]
        losses = [abs(min(0, c)) for c in changes]

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        rsi_values = []
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - 100 / (1 + rs))

        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0:
                rsi_values.append(100.0)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100 - 100 / (1 + rs))
        return rsi_values

    @staticmethod
    def macd(candles: List[Dict], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
        ema_fast = TechnicalIndicators.ema(candles, fast)
        ema_slow = TechnicalIndicators.ema(candles, slow)
        if len(ema_fast) < len(ema_slow):
            return {"macd": [], "signal": [], "histogram": []}

        offset = slow - fast
        macd_line = [ema_fast[i + offset] - ema_slow[i] for i in range(len(ema_slow))]

        if len(macd_line) < signal:
            return {"macd": macd_line, "signal": [], "histogram": []}

        k = 2 / (signal + 1)
        sig = [sum(macd_line[:signal]) / signal]
        for i in range(signal, len(macd_line)):
            sig.append((macd_line[i] - sig[-1]) * k + sig[-1])

        histogram = [macd_line[i + signal - 1] - sig[i] for i in range(len(sig))]
        return {"macd": macd_line, "signal": sig, "histogram": histogram}

    @staticmethod
    def bollinger_bands(candles: List[Dict], period: int = 20, std_dev: float = 2.0) -> Dict[str, List[float]]:
        if len(candles) < period:
            return {"middle": [], "upper": [], "lower": []}
        middle = TechnicalIndicators.ma(candles, period)
        closes = [c["close"] for c in candles]
        upper, lower = [], []
        for i in range(period - 1, len(closes)):
            window = closes[i - period + 1:i + 1]
            mean = middle[i - period + 1]
            variance = sum((x - mean) ** 2 for x in window) / period
            std = variance ** 0.5
            upper.append(mean + std_dev * std)
            lower.append(mean - std_dev * std)
        return {"middle": middle, "upper": upper, "lower": lower}


# ============================================================================
# 异步客户端
# ============================================================================

class AsyncOKXMarketClient:
    """异步 OKX 客户端"""

    def __init__(self, base_url: str = BASE_URL, timeout: int = 10, use_mock: bool = False):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.use_mock = use_mock
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession(
                headers={"Content-Type": "application/json", "User-Agent": "AsyncOKXClient/1.0"},
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )
        return self._session

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None

    async def _get(self, path: str, params: Dict = None) -> Dict:
        session = await self._get_session()
        async with session.get(f"{self.base_url}{path}", params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
            if data.get("code") != "0":
                raise RuntimeError(f"OKX API error [{data.get('code')}]: {data.get('msg')}")
            return data

    async def get_ticker(self, inst_id: str) -> Dict:
        if self.use_mock:
            item = MockOKXClient._mock_ticker(inst_id)
        else:
            item = (await self._get("/api/v5/market/ticker", {"instId": inst_id}))["data"][0]
        return {
            "inst_id": item["instId"],
            "last": float(item["last"]),
            "open24h": float(item["open24h"]),
            "high24h": float(item["high24h"]),
            "low24h": float(item["low24h"]),
            "vol24h": float(item["vol24h"]),
            "pct_chg": float(item.get("pctChg", 0)) * 100,
            "ts": datetime.fromtimestamp(int(item["ts"]) / 1000, tz=timezone.utc),
        }

    async def get_multiple_tickers(self, inst_ids: List[str]) -> Dict[str, Dict]:
        tasks = [self.get_ticker(iid) for iid in inst_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            iid: r if not isinstance(r, Exception) else {"error": str(r)}
            for iid, r in zip(inst_ids, results)
        }

    async def get_candles(self, inst_id: str, bar: str = "1H", limit: int = 100) -> List[Dict]:
        if self.use_mock:
            raw = MockOKXClient._mock_candles(inst_id, bar, limit)
        else:
            raw = (await self._get("/api/v5/market/candles", {"instId": inst_id, "bar": bar, "limit": limit}))["data"]
        return [
            {"time": datetime.fromtimestamp(int(p[0]) / 1000, tz=timezone.utc),
             "open": float(p[1]), "high": float(p[2]), "low": float(p[3]),
             "close": float(p[4]), "vol": float(p[5]), "vol_ccy": float(p[6]) if len(p) > 6 else 0.0}
            for p in raw
        ]


# ============================================================================
# 演示 / 主程序
# ============================================================================

def _print_ticker(t: Dict):
    print(f"\n  【{t['inst_id']}】")
    print(f"    最新价: {t['last']:>14.4f}")
    print(f"    24h 涨跌: {t['pct_chg']:>+8.2f}%")
    print(f"    24h 高/低: {t['high24h']:>12.2f} / {t['low24h']:>.2f}")
    print(f"    24h 成交量: {t['vol24h']:>12.4f}")
    print(f"    数据时间: {t['ts'].strftime('%Y-%m-%d %H:%M:%S UTC')}")


def _print_orderbook(book: Dict):
    print(f"\n  【盘口】{book['inst_id']}  {book['ts'].strftime('%H:%M:%S UTC')}")
    print(f"  {'─'*36}")
    for ask in book["asks"][:5]:
        print(f"    卖 {ask['price']:>14.4f}    数量 {ask['size']:>10.4f}")
    print(f"  {'─'*36}")
    for bid in book["bids"][:5]:
        print(f"    买 {bid['price']:>14.4f}    数量 {bid['size']:>10.4f}")


def _print_indicators(candles: List[Dict], inst_id: str):
    ma5 = TechnicalIndicators.ma(candles, 5)
    ma20 = TechnicalIndicators.ma(candles, 20)
    ema20 = TechnicalIndicators.ema(candles, 20)
    rsi14 = TechnicalIndicators.rsi(candles, 14)
    macd = TechnicalIndicators.macd(candles)
    bb = TechnicalIndicators.bollinger_bands(candles, 20)

    latest = candles[-1]
    print(f"\n  【技术指标】{inst_id}  (收盘价: {latest['close']:.4f})")
    print(f"  {'─'*44}")
    if ma5:  print(f"    MA(5)        {ma5[-1]:>14.4f}")
    if ma20: print(f"    MA(20)       {ma20[-1]:>14.4f}")
    if ema20: print(f"    EMA(20)      {ema20[-1]:>14.4f}")
    if rsi14:
        rsi_val = rsi14[-1]
        zone = "超买区(>70)" if rsi_val > 70 else "超卖区(<30)" if rsi_val < 30 else "中性区"
        print(f"    RSI(14)      {rsi_val:>14.2f}  [{zone}]")
    if macd["macd"]:
        m = macd
        hist = m["histogram"][-1] if m["histogram"] else 0
        print(f"    MACD         {m['macd'][-1]:>14.4f}")
        print(f"    Signal       {m['signal'][-1]:>14.4f}")
        print(f"    Histogram    {hist:>+14.4f}  {'▲ 金叉' if hist > 0 else '▼ 死叉'}")
    if bb["middle"]:
        print(f"    BB 上轨      {bb['upper'][-1]:>14.4f}")
        print(f"    BB 中轨      {bb['middle'][-1]:>14.4f}")
        print(f"    BB 下轨      {bb['lower'][-1]:>14.4f}")
        width = (bb["upper"][-1] - bb["lower"][-1]) / bb["middle"][-1] * 100
        print(f"    BB 带宽      {width:>14.2f}%")


def main():
    # use_mock=True 因为当前环境网络不通，用模拟数据演示
    client = OKXMarketClient(use_mock=True)
    storage = DataStorage()
    targets = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║       OKX 欧易行情数据客户端  - 完整功能演示            ║")
    print("║       (使用模拟数据，实际环境 set use_mock=False)        ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # ── 1. 实时行情 ───────────────────────────────────────────────
    print("\n┌────────────────────────────────────────────────────────┐")
    print("│ 1️⃣  实时行情 ticker                                    │")
    print("└────────────────────────────────────────────────────────┘")
    for inst_id in targets:
        ticker = client.get_ticker(inst_id)
        _print_ticker(ticker)
        storage.save_ticker_csv(ticker)

    # ── 2. 批量行情 ──────────────────────────────────────────────
    print("\n┌────────────────────────────────────────────────────────┐")
    print("│ 2️⃣  批量行情 all tickers                               │")
    print("└────────────────────────────────────────────────────────┘")
    all_tickers = client.get_tickers()
    storage.save_tickers_json(all_tickers)
    print(f"  共获取 {len(all_tickers)} 个交易对，已保存 JSON")
    for t in all_tickers:
        print(f"  {t['inst_id']:<14} {t['last']:>12}  {t['pct_chg']:>+7.2f}%")

    # ── 3. 盘口深度 ─────────────────────────────────────────────
    print("\n┌────────────────────────────────────────────────────────┐")
    print("│ 3️⃣  盘口深度 orderbook                                 │")
    print("└────────────────────────────────────────────────────────┘")
    book = client.get_orderbook("BTC-USDT", depth=10)
    _print_orderbook(book)

    # ── 4. K线 + 技术指标 ───────────────────────────────────────
    print("\n┌────────────────────────────────────────────────────────┐")
    print("│ 4️⃣  K线数据 + 技术指标                                 │")
    print("└────────────────────────────────────────────────────────┘")
    candles = client.get_candles("BTC-USDT", bar="1H", limit=100)
    csv_path = storage.save_candles_csv(candles, "BTC-USDT", "1H")
    json_path = storage.save_candles_json(candles, "BTC-USDT", "1H")
    print(f"  K线已保存: {csv_path}")
    print(f"  K线已保存: {json_path}")
    print(f"\n  最近 5 根 K线 (1H):")
    print(f"  {'时间':<20} {'开':>10} {'高':>10} {'低':>10} {'收':>10} {'成交量':>10}")
    print(f"  {'─'*72}")
    for c in candles[-5:]:
        print(f"  {c['time'].strftime('%Y-%m-%d %H:%M'):<20} "
              f"{c['open']:>10.2f} {c['high']:>10.2f} {c['low']:>10.2f} "
              f"{c['close']:>10.2f} {c['vol']:>10.4f}")
    _print_indicators(candles, "BTC-USDT")

    # ── 5. 价格监控 ──────────────────────────────────────────────
    print("\n┌────────────────────────────────────────────────────────┐")
    print("│ 5️⃣  价格监控告警  (模拟触发场景)                      │")
    print("└────────────────────────────────────────────────────────┘")
    monitor = PriceMonitor(client, storage)
    # 设置宽松阈值，大部分币种不会触发
    monitor.add_rule("BTC-USDT", price_above=200000, price_below=100)
    monitor.add_rule("ETH-USDT", price_above=10000, price_below=100)
    monitor.add_rule("SOL-USDT", pct_change_above=100, pct_change_below=-100)
    print("  监控规则已添加，执行检查...")
    alerts = monitor.check()
    if alerts:
        for a in alerts:
            print(f"  告警: {a}")
    else:
        print("  当前无告警触发（价格均在阈值范围内）")

    # ── 6. 异步客户端 ───────────────────────────────────────────
    print("\n┌────────────────────────────────────────────────────────┐")
    print("│ 6️⃣  异步客户端 async + 并发请求                        │")
    print("└────────────────────────────────────────────────────────┘")
    asyncio.run(async_demo())

    # ── 7. WebSocket 实时推送 ────────────────────────────────────
    print("\n┌────────────────────────────────────────────────────────┐")
    print("│ 7️⃣  WebSocket 实时推送  (模拟 6 秒)                   │")
    print("└────────────────────────────────────────────────────────┘")
    client.subscribe_tickers_stream(["BTC-USDT", "ETH-USDT"], on_message=lambda t: print(
        f"  实时 >>> {t['inst_id']} = {t['last']:.4f}  ({t['pct_chg']:+.2f}%)"), max_duration=6)

    # ── 总结 ──────────────────────────────────────────────────────
    print("\n┌────────────────────────────────────────────────────────┐")
    print("│ 📁 数据已落库到 data/okx/ 目录                          │")
    print("└────────────────────────────────────────────────────────┘")
    for f in sorted(os.listdir(storage.output_dir)):
        size = os.path.getsize(os.path.join(storage.output_dir, f))
        print(f"  {f:<40} {size:>8} bytes")

    print("\n✅ 演示完成！")
    print("   实际使用时请将 OKXMarketClient(use_mock=False) 即可连接真实 API")


async def async_demo():
    client = AsyncOKXMarketClient(use_mock=True)
    try:
        print("  并发请求多个 ticker...")
        results = await client.get_multiple_tickers(["BTC-USDT", "ETH-USDT", "SOL-USDT"])
        for inst_id, data in results.items():
            if "error" in data:
                print(f"  {inst_id}: ❌ {data['error']}")
            else:
                print(f"  {inst_id}: {data['last']:.4f}  ({data['pct_chg']:+.2f}%) ✅")

        candles = await client.get_candles("BTC-USDT", bar="1H", limit=10)
        print(f"  异步 K线: 最新收盘 {candles[-1]['close']:.2f} ✅")
    finally:
        await client.close()


if __name__ == "__main__":
    main()
