import { useStore } from "../store/useStore";
import { StockCard } from "../components/StockCard";
import { marketIndices } from "../utils/mockData";
import {
  ArrowUp,
  ArrowDown,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Users,
  Activity,
  Wallet,
} from "lucide-react";

export const Dashboard = () => {
  const { stocks, positions } = useStore();

  const gainers = [...stocks].sort((a, b) => b.changePercent - a.changePercent).slice(0, 4);
  const losers = [...stocks].sort((a, b) => a.changePercent - b.changePercent).slice(0, 4);

  const totalPortfolioValue = positions.reduce((sum, pos) => {
    const stock = stocks.find((s) => s.symbol === pos.symbol);
    return sum + (stock ? stock.price * pos.quantity : 0);
  }, 0);

  const totalCost = positions.reduce((sum, pos) => sum + pos.avgPrice * pos.quantity, 0);
  const totalProfit = totalPortfolioValue - totalCost;
  const profitPercent = totalCost > 0 ? (totalProfit / totalCost) * 100 : 0;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">市场概览</h1>
        <p className="text-slate-400 mt-1">实时掌握市场动态</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {marketIndices.map((index, i) => (
          <div
            key={i}
            className="bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 rounded-xl p-5"
          >
            <p className="text-slate-400 text-sm mb-2">{index.name}</p>
            <p className="text-2xl font-bold text-white mb-1">{index.value.toFixed(2)}</p>
            <div
              className={`flex items-center ${index.changePercent >= 0 ? "text-emerald-400" : "text-red-400"}`}
            >
              {index.changePercent >= 0 ? (
                <ArrowUp className="h-4 w-4 mr-1" />
              ) : (
                <ArrowDown className="h-4 w-4 mr-1" />
              )}
              <span className="font-medium">
                {index.changePercent >= 0 ? "+" : ""}
                {index.change.toFixed(2)} ({index.changePercent >= 0 ? "+" : ""}
                {index.changePercent.toFixed(2)}%)
              </span>
            </div>
          </div>
        ))}
      </div>

      {positions.length > 0 && (
        <div className="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white flex items-center">
              <Wallet className="h-5 w-5 mr-2 text-cyan-400" />
              我的持仓
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-800/50 rounded-lg p-4">
              <p className="text-slate-400 text-sm">总市值</p>
              <p className="text-2xl font-bold text-white">
                ¥{totalPortfolioValue.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4">
              <p className="text-slate-400 text-sm">持仓成本</p>
              <p className="text-2xl font-bold text-white">
                ¥{totalCost.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4">
              <p className="text-slate-400 text-sm">总盈亏</p>
              <p className={`text-2xl font-bold ${totalProfit >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {totalProfit >= 0 ? "+" : ""}
                ¥{totalProfit.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                <span className="text-sm ml-2">
                  ({profitPercent >= 0 ? "+" : ""}
                  {profitPercent.toFixed(2)}%)
                </span>
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h2 className="text-xl font-bold text-white mb-4 flex items-center">
            <TrendingUp className="h-5 w-5 mr-2 text-emerald-400" />
            涨幅榜
          </h2>
          <div className="space-y-3">
            {gainers.map((stock) => (
              <StockCard key={stock.symbol} stock={stock} />
            ))}
          </div>
        </div>

        <div>
          <h2 className="text-xl font-bold text-white mb-4 flex items-center">
            <TrendingDown className="h-5 w-5 mr-2 text-red-400" />
            跌幅榜
          </h2>
          <div className="space-y-3">
            {losers.map((stock) => (
              <StockCard key={stock.symbol} stock={stock} />
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
          <Activity className="h-8 w-8 text-cyan-400 mb-3" />
          <p className="text-3xl font-bold text-white">{stocks.length}</p>
          <p className="text-slate-400 text-sm">关注股票</p>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
          <BarChart3 className="h-8 w-8 text-blue-400 mb-3" />
          <p className="text-3xl font-bold text-white">3</p>
          <p className="text-slate-400 text-sm">回测策略</p>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
          <Users className="h-8 w-8 text-purple-400 mb-3" />
          <p className="text-3xl font-bold text-white">{positions.length}</p>
          <p className="text-slate-400 text-sm">持仓股票</p>
        </div>
      </div>
    </div>
  );
};
