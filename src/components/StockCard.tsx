import { useNavigate } from "react-router-dom";
import { Stock } from "../types";
import { TrendingUp, TrendingDown } from "lucide-react";

interface StockCardProps {
  stock: Stock;
}

export const StockCard = ({ stock }: StockCardProps) => {
  const navigate = useNavigate();
  const isPositive = stock.changePercent >= 0;

  return (
    <div
      onClick={() => navigate(`/stock/${stock.symbol}`)}
      className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 cursor-pointer hover:border-cyan-500/50 hover:bg-slate-800 transition-all duration-200"
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-white font-semibold">{stock.symbol}</h3>
          <p className="text-slate-400 text-sm">{stock.name}</p>
        </div>
        {isPositive ? (
          <TrendingUp className="h-5 w-5 text-emerald-400" />
        ) : (
          <TrendingDown className="h-5 w-5 text-red-400" />
        )}
      </div>
      <div className="flex justify-between items-end">
        <div>
          <p className="text-2xl font-bold text-white">
            ¥{stock.price.toFixed(2)}
          </p>
        </div>
        <div className={`text-right ${isPositive ? "text-emerald-400" : "text-red-400"}`}>
          <p className="font-semibold">
            {isPositive ? "+" : ""}
            {stock.change.toFixed(2)}
          </p>
          <p className="text-sm">
            ({isPositive ? "+" : ""}
            {stock.changePercent.toFixed(2)}%)
          </p>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-slate-700 flex justify-between text-xs text-slate-400">
        <span>高: ¥{stock.high.toFixed(2)}</span>
        <span>低: ¥{stock.low.toFixed(2)}</span>
        <span>量: {(stock.volume / 10000).toFixed(1)}万</span>
      </div>
    </div>
  );
};
