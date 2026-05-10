import { create } from "zustand";
import { Stock, Trade, Position, BacktestResult, StrategyConfig } from "../types";
import { mockStocks } from "../utils/mockData";

interface AppState {
  stocks: Stock[];
  selectedStock: Stock | null;
  trades: Trade[];
  positions: Position[];
  backtestResult: BacktestResult | null;
  isLoading: boolean;
  setSelectedStock: (stock: Stock | null) => void;
  addTrade: (trade: Trade) => void;
  updatePosition: (symbol: string, quantity: number, price: number) => void;
  runBacktest: (config: StrategyConfig) => Promise<void>;
}

const loadTradesFromStorage = (): Trade[] => {
  try {
    const saved = localStorage.getItem("trades");
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
};

const loadPositionsFromStorage = (): Position[] => {
  try {
    const saved = localStorage.getItem("positions");
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
};

export const useStore = create<AppState>((set, get) => ({
  stocks: mockStocks,
  selectedStock: null,
  trades: loadTradesFromStorage(),
  positions: loadPositionsFromStorage(),
  backtestResult: null,
  isLoading: false,

  setSelectedStock: (stock) => set({ selectedStock: stock }),

  addTrade: (trade) => {
    const newTrades = [...get().trades, trade];
    localStorage.setItem("trades", JSON.stringify(newTrades));
    set({ trades: newTrades });
  },

  updatePosition: (symbol, quantity, price) => {
    const positions = get().positions;
    const existingIndex = positions.findIndex((p) => p.symbol === symbol);

    let newPositions;
    if (existingIndex >= 0) {
      newPositions = [...positions];
      const existing = newPositions[existingIndex];
      const totalQuantity = existing.quantity + quantity;

      if (totalQuantity === 0) {
        newPositions = newPositions.filter((p) => p.symbol !== symbol);
      } else if (quantity > 0) {
        const newAvgPrice =
          (existing.quantity * existing.avgPrice + quantity * price) /
          totalQuantity;
        newPositions[existingIndex] = {
          ...existing,
          quantity: totalQuantity,
          avgPrice: parseFloat(newAvgPrice.toFixed(2)),
        };
      } else {
        newPositions[existingIndex] = { ...existing, quantity: totalQuantity };
      }
    } else if (quantity > 0) {
      newPositions = [...positions, { symbol, quantity, avgPrice: price }];
    } else {
      newPositions = positions;
    }

    localStorage.setItem("positions", JSON.stringify(newPositions));
    set({ positions: newPositions });
  },

  runBacktest: async (config) => {
    set({ isLoading: true });

    await new Promise((resolve) => setTimeout(resolve, 1500));

    const days = Math.floor(
      (new Date(config.endDate).getTime() - new Date(config.startDate).getTime()) /
        (1000 * 60 * 60 * 24)
    );
    const equityCurve: { date: string; equity: number }[] = [];
    let equity = config.initialCapital;
    const startDate = new Date(config.startDate);

    for (let i = 0; i <= days; i++) {
      const date = new Date(startDate);
      date.setDate(date.getDate() + i);
      const dailyReturn = (Math.random() - 0.48) * 0.03;
      equity = equity * (1 + dailyReturn);

      equityCurve.push({
        date: date.toISOString().split("T")[0],
        equity: parseFloat(equity.toFixed(2)),
      });
    }

    const totalReturn = ((equity - config.initialCapital) / config.initialCapital) * 100;
    const maxDrawdown = Math.random() * 20 + 5;
    const winRate = Math.random() * 30 + 40;
    const totalTrades = Math.floor(Math.random() * 50 + 10);
    const profitFactor = Math.random() * 1.5 + 1;

    const result: BacktestResult = {
      totalReturn: parseFloat(totalReturn.toFixed(2)),
      maxDrawdown: parseFloat(maxDrawdown.toFixed(2)),
      winRate: parseFloat(winRate.toFixed(2)),
      totalTrades,
      profitFactor: parseFloat(profitFactor.toFixed(2)),
      equityCurve,
    };

    set({ backtestResult: result, isLoading: false });
  },
}));
