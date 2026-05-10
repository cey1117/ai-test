import { Link, useLocation } from "react-router-dom";
import { BarChart3, TrendingUp, LineChart, Wallet, Home } from "lucide-react";

const navItems = [
  { path: "/", icon: Home, label: "仪表盘" },
  { path: "/stock/600519", icon: TrendingUp, label: "股票详情" },
  { path: "/backtest", icon: BarChart3, label: "策略回测" },
  { path: "/trading", icon: Wallet, label: "模拟交易" },
];

export const Navbar = () => {
  const location = useLocation();

  return (
    <nav className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <LineChart className="h-8 w-8 text-cyan-400" />
            <span className="ml-2 text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              QuantTrade
            </span>
          </div>
          <div className="flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                location.pathname === item.path ||
                (item.path.startsWith("/stock") &&
                  location.pathname.startsWith("/stock"));

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                      : "text-slate-400 hover:text-white hover:bg-slate-800"
                  }`}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
};
