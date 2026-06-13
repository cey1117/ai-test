#!/usr/bin/env python3
"""OKX 行情数据客户端 - 对接欧易公开行情 API
无需 API Key，直接调用即可获取 K线、最新价、深度、成交等数据。
"""

import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional

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
    client = OKXMarketClient()
    targets = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]

    print("=" * 60)
    print("OKX 欧易行情数据客户端")
    print("=" * 60)

    for inst_id in targets:
        try:
            ticker = client.get_ticker(inst_id)
            _print_ticker(ticker)
        except Exception as e:
            print(f"\n获取 {inst_id} 失败: {e}")

    try:
        book = client.get_orderbook("BTC-USDT", depth=10)
        _print_orderbook(book)
    except Exception as e:
        print(f"\n获取盘口失败: {e}")

    try:
        candles = client.get_candles("BTC-USDT", bar="1H", limit=30)
        _print_candles(candles, "BTC-USDT (1H)")
    except Exception as e:
        print(f"\n获取K线失败: {e}")

    print("\n" + "=" * 60)
    print("提示: 可在代码中调用 subscribe_tickers_stream() 订阅实时推送")
    print("=" * 60)


if __name__ == "__main__":
    main()
