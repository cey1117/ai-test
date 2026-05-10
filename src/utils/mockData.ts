import { Stock, KLineData } from "../types";

export const mockStocks: Stock[] = [
  {
    symbol: "600519",
    name: "贵州茅台",
    price: 1856.0,
    change: 28.5,
    changePercent: 1.56,
    volume: 2580000,
    high: 1872.0,
    low: 1820.0,
    open: 1830.0,
  },
  {
    symbol: "000858",
    name: "五粮液",
    price: 156.8,
    change: -3.2,
    changePercent: -2.0,
    volume: 3850000,
    high: 162.5,
    low: 155.2,
    open: 160.5,
  },
  {
    symbol: "601318",
    name: "中国平安",
    price: 48.65,
    change: 1.25,
    changePercent: 2.63,
    volume: 12500000,
    high: 49.2,
    low: 47.3,
    open: 47.5,
  },
  {
    symbol: "000001",
    name: "平安银行",
    price: 12.35,
    change: 0.45,
    changePercent: 3.78,
    volume: 45600000,
    high: 12.5,
    low: 11.9,
    open: 11.95,
  },
  {
    symbol: "600036",
    name: "招商银行",
    price: 32.8,
    change: -0.8,
    changePercent: -2.38,
    volume: 8900000,
    high: 34.2,
    low: 32.5,
    open: 33.8,
  },
  {
    symbol: "002594",
    name: "比亚迪",
    price: 265.3,
    change: 12.5,
    changePercent: 4.95,
    volume: 5200000,
    high: 268.0,
    low: 252.0,
    open: 253.5,
  },
  {
    symbol: "600900",
    name: "长江电力",
    price: 28.5,
    change: 0.3,
    changePercent: 1.06,
    volume: 6800000,
    high: 28.8,
    low: 28.1,
    open: 28.2,
  },
  {
    symbol: "601899",
    name: "紫金矿业",
    price: 15.2,
    change: -0.5,
    changePercent: -3.18,
    volume: 15800000,
    high: 16.0,
    low: 15.0,
    open: 15.8,
  },
];

export const generateKLineData = (
  symbol: string,
  days: number = 120
): KLineData[] => {
  const data: KLineData[] = [];
  let basePrice = mockStocks.find((s) => s.symbol === symbol)?.price || 100;
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);

  for (let i = 0; i < days; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);

    const volatility = basePrice * 0.03;
    const open = basePrice + (Math.random() - 0.5) * volatility;
    const close = open + (Math.random() - 0.5) * volatility;
    const high = Math.max(open, close) + Math.random() * volatility * 0.5;
    const low = Math.min(open, close) - Math.random() * volatility * 0.5;
    const volume = Math.floor(1000000 + Math.random() * 5000000);

    data.push({
      date: date.toISOString().split("T")[0],
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
      volume,
    });

    basePrice = close;
  }

  return data;
};

export const marketIndices = [
  { name: "上证指数", value: 3186.52, change: 28.35, changePercent: 0.9 },
  { name: "深证成指", value: 10567.89, change: -45.23, changePercent: -0.43 },
  { name: "创业板指", value: 2156.34, change: 32.15, changePercent: 1.52 },
];
