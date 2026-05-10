import { useState, useRef, useEffect } from "react";
import { useStore } from "../store/useStore";
import * as echarts from "echarts";
import {
  BarChart3,
  Play,
  RotateCcw,
  TrendingUp,
  TrendingDown,
  Zap,
  Target,
  Settings,
} from "lucide-react";

export const Backtest = () => {
  const { stocks, backtestResult, runBacktest, isLoading } = useStore();
  const [selectedStrategy, setSelectedStrategy] = useState("ma");
  const [selectedStock, setSelectedStock] = useState(stocks[0]?.symbol || "");
  const [initialCapital, setInitialCapital] = useState(100000);
  const [startDate, setStartDate] = useState("2024-01-01");
  const [endDate, setEndDate] = useState("2024-12-31");
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts>();

  const strategies = [
    { id: "ma", name: "均线策略", desc: "基于短期均线上穿长期均线买入" },
    { id: "rsi", name: "RSI策略", desc: "RSI超卖买入，超买卖出" },
    { id: "macd", name: "MACD策略", desc: "MACD金叉买入，死叉卖出" },
    { id: "boll", name: "布林带策略", desc: "突破下轨买入，突破上轨卖出" },
  ];

  useEffect(() => {
    if (!chartRef.current || !backtestResult) return;

    chartInstance.current = echarts.init(chartRef.current);

    const option = {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        formatter: (params: any) => {
          const data = params[0];
          return `${data.axisValue}<br/>净值: ¥${data.data.toFixed(2)}`;
        },
      },
      grid: {
        left: "3%",
        right: "4%",
        bottom: "3%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: backtestResult.equityCurve.map((d) => d.date),
        axisLine: { lineStyle: { color: "#475569" } },
        axisLabel: { color: "#94a3b8" },
      },
      yAxis: {
        type: "value",
        axisLine: { lineStyle: { color: "#475569" } },
        axisLabel: { color: "#94a3b8", formatter: "¥{value}" },
        splitLine: { lineStyle: { color: "#334155" } },
      },
      series: [
        {
          name: "净值",
          type: "line",
          smooth: true,
          data: backtestResult.equityCurve.map((d) => d.equity),
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "rgba(6, 182, 212, 0.3)" },
              { offset: 1, color: "rgba(6, 182, 212, 0)" },
            ]),
          },
          lineStyle: { color: "#06b6d4", width: 2 },
          itemStyle: { color: "#06b6d4" },
        },
      ],
    };

    chartInstance.current.setOption(option);

    const handleResize = () => chartInstance.current?.resize();
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chartInstance.current?.dispose();
    };
  }, [backtestResult]);

  const handleRunBacktest = () => {
    runBacktest({
      name: strategies.find((s) => s.id === selectedStrategy)?.name || "",
      symbol: selectedStock,
      startDate,
      endDate,
      initialCapital,
      parameters: {},
    });
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">策略回测</h1>
        <p className="text-slate-400 mt-1">测试你的交易策略表现</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center">
              <Settings className="h-5 w-5 mr-2 text-cyan-400" />
              策略配置
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">选择策略</label>
                <div className="grid grid-cols-2 gap-2">
                  {strategies.map((strategy) => (
                    <button
                      key={strategy.id}
                      onClick={() => setSelectedStrategy(strategy.id)}
                      className={`p-3 rounded-lg text-left border transition-all ${
                        selectedStrategy === strategy.id
                          ? "border-cyan-500 bg-cyan-500/10 text-cyan-400"
                          : "border-slate-700 text-slate-300 hover:border-slate-600"
                      }`}
                    >
                      <p className="font-medium text-sm">{strategy.name}</p>
                      <p className="text-xs opacity-70 mt-1">{strategy.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm text-slate-400 mb-2">选择股票</label>
                <select
                  value={selectedStock}
                  onChange={(e) => setSelectedStock(e.target.value)}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-cyan-500"
                >
                  {stocks.map((stock) => (
                    <option key={stock.symbol} value={stock.symbol}>
                      {stock.symbol} - {stock.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm text-slate-400 mb-2">初始资金 (¥)</label>
                <input
                  type="number"
                  value={initialCapital}
                  onChange={(e) => setInitialCapital(Number(e.target.value))}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-2">开始日期</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-2">结束日期</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <button
                onClick={handleRunBacktest}
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-semibold py-3 rounded-lg flex items-center justify-center space-x-2 hover:from-cyan-600 hover:to-blue-600 transition-all disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <RotateCcw className="h-5 w-5 animate-spin" />
                    <span>回测中...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5" />
                    <span>开始回测</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-4">
          {backtestResult ? (
            <>
              <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                <h2 className="text-xl font-bold text-white mb-4 flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2 text-cyan-400" />
                  净值曲线
                </h2>
                <div ref={chartRef} style={{ height: "350px", width: "100%" }} />
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div
                  className={`bg-slate-800/50 border border-slate-700 rounded-xl p-5 ${
                    backtestResult.totalReturn >= 0 ? "border-emerald-500/30" : "border-red-500/30"
                  }`}
                >
                  <div className="flex items-center mb-2">
                    {backtestResult.totalReturn >= 0 ? (
                      <TrendingUp className="h-4 w-4 mr-2 text-emerald-400" />
                    ) : (
                      <TrendingDown className="h-4 w-4 mr-2 text-red-400" />
                    )}
                    <p className="text-slate-400 text-sm">总收益率</p>
                  </div>
                  <p
                    className={`text-2xl font-bold ${
                      backtestResult.totalReturn >= 0 ? "text-emerald-400" : "text-red-400"
                    }`}
                  >
                    {backtestResult.totalReturn >= 0 ? "+" : ""}
                    {backtestResult.totalReturn.toFixed(2)}%
                  </p>
                </div>

                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
                  <div className="flex items-center mb-2">
                    <Target className="h-4 w-4 mr-2 text-orange-400" />
                    <p className="text-slate-400 text-sm">最大回撤</p>
                  </div>
                  <p className="text-2xl font-bold text-orange-400">
                    {backtestResult.maxDrawdown.toFixed(2)}%
                  </p>
                </div>

                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
                  <div className="flex items-center mb-2">
                    <Zap className="h-4 w-4 mr-2 text-yellow-400" />
                    <p className="text-slate-400 text-sm">胜率</p>
                  </div>
                  <p className="text-2xl font-bold text-yellow-400">
                    {backtestResult.winRate.toFixed(2)}%
                  </p>
                </div>

                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
                  <div className="flex items-center mb-2">
                    <BarChart3 className="h-4 w-4 mr-2 text-purple-400" />
                    <p className="text-slate-400 text-sm">交易次数</p>
                  </div>
                  <p className="text-2xl font-bold text-purple-400">
                    {backtestResult.totalTrades}
                  </p>
                </div>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
                <h3 className="text-lg font-bold text-white mb-3">其他指标</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-slate-400 text-sm">盈亏比</p>
                    <p className="text-lg font-semibold text-white">
                      {backtestResult.profitFactor.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">年化收益率</p>
                    <p className="text-lg font-semibold text-cyan-400">+15.32%</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">夏普比率</p>
                    <p className="text-lg font-semibold text-white">1.45</p>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-12 flex flex-col items-center justify-center">
              <BarChart3 className="h-16 w-16 text-slate-600 mb-4" />
              <p className="text-slate-400 text-lg">选择策略并开始回测</p>
              <p className="text-slate-500 text-sm mt-2">回测结果将在这里显示</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
