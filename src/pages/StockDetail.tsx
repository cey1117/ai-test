import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import { useStore } from "../store/useStore";
import { KLineChart } from "../components/KLineChart";
import { generateKLineData } from "../utils/mockData";
import {
  ArrowUp,
  ArrowDown,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Activity,
} from "lucide-react";

export const StockDetail = () => {
  const { symbol } = useParams<{ symbol: string }>();
  const { stocks } = useStore();
  const [timeframe, setTimeframe] = useState<"D" | "W" | "M">("D");
  const [klineData, setKlineData] = useState<ReturnType<typeof generateKLineData>>([]);

  const stock = stocks.find((s) => s.symbol === symbol);

  useEffect(() => {
    if (symbol) {
      const days = timeframe === "D" ? 120 : timeframe === "W" ? 250 : 500;
      setKlineData(generateKLineData(symbol, days));
    }
  }, [symbol, timeframe]);

  if (!stock) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <p className="text-slate-400">股票不存在</p>
      </div>
    );
  }

  const isPositive = stock.changePercent >= 0;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">{stock.symbol}</h1>
          <p className="text-slate-400">{stock.name}</p>
        </div>
        <div className="mt-4 md:mt-0 text-right">
          <p className="text-4xl font-bold text-white">¥{stock.price.toFixed(2)}</p>
          <div
            className={`flex items-center justify-end space-x-2 ${isPositive ? "text-emerald-400" : "text-red-400"}`}
          >
            {isPositive ? <ArrowUp className="h-5 w-5" /> : <ArrowDown className="h-5 w-5" />}
            <span className="text-xl font-semibold">
              {isPositive ? "+" : ""}
              {stock.change.toFixed(2)} ({isPositive ? "+" : ""}
              {stock.changePercent.toFixed(2)}%)
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <p className="text-slate-400 text-sm mb-1">今开</p>
          <p className="text-xl font-semibold text-white">¥{stock.open.toFixed(2)}</p>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <p className="text-slate-400 text-sm mb-1">最高</p>
          <p className="text-xl font-semibold text-emerald-400">¥{stock.high.toFixed(2)}</p>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <p className="text-slate-400 text-sm mb-1">最低</p>
          <p className="text-xl font-semibold text-red-400">¥{stock.low.toFixed(2)}</p>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <p className="text-slate-400 text-sm mb-1">成交量</p>
          <p className="text-xl font-semibold text-white">{(stock.volume / 10000).toFixed(1)}万</p>
        </div>
      </div>

      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white flex items-center">
            <BarChart3 className="h-5 w-5 mr-2 text-cyan-400" />
            K线图
          </h2>
          <div className="flex space-x-2">
            {(["D", "W", "M"] as const).map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  timeframe === tf
                    ? "bg-cyan-500 text-white"
                    : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                }`}
              >
                {tf === "D" ? "日线" : tf === "W" ? "周线" : "月线"}
              </button>
            ))}
          </div>
        </div>
        {klineData.length > 0 ? (
          <KLineChart data={klineData} height={450} />
        ) : (
          <div className="h-[450px] flex items-center justify-center text-slate-400">
            加载中...
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
          <div className="flex items-center mb-4">
            <Activity className="h-5 w-5 mr-2 text-cyan-400" />
            <h3 className="text-lg font-semibold text-white">MACD</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">DIF</span>
              <span className="text-emerald-400">+0.25</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">DEA</span>
              <span className="text-emerald-400">+0.18</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">MACD</span>
              <span className="text-emerald-400">+0.14</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
          <div className="flex items-center mb-4">
            <TrendingUp className="h-5 w-5 mr-2 text-cyan-400" />
            <h3 className="text-lg font-semibold text-white">KDJ</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">K</span>
              <span className="text-yellow-400">58.32</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">D</span>
              <span className="text-yellow-400">52.18</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">J</span>
              <span className="text-yellow-400">70.60</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
          <div className="flex items-center mb-4">
            <TrendingDown className="h-5 w-5 mr-2 text-cyan-400" />
            <h3 className="text-lg font-semibold text-white">RSI</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">RSI6</span>
              <span className="text-purple-400">55.20</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">RSI12</span>
              <span className="text-purple-400">51.80</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">RSI24</span>
              <span className="text-purple-400">49.50</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
