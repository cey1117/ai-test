export interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
}

export interface KLineData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Trade {
  id: string;
  symbol: string;
  type: "buy" | "sell";
  price: number;
  quantity: number;
  timestamp: string;
}

export interface Position {
  symbol: string;
  quantity: number;
  avgPrice: number;
}

export interface BacktestResult {
  totalReturn: number;
  maxDrawdown: number;
  winRate: number;
  totalTrades: number;
  profitFactor: number;
  equityCurve: Array<{ date: string; equity: number }>;
}

export interface StrategyConfig {
  name: string;
  symbol: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  parameters: Record<string, number>;
}
