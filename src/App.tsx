import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Navbar } from "./components/Navbar";
import { Dashboard } from "./pages/Dashboard";
import { StockDetail } from "./pages/StockDetail";
import { Backtest } from "./pages/Backtest";
import { Trading } from "./pages/Trading";

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-950">
        <Navbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/stock/:symbol" element={<StockDetail />} />
          <Route path="/backtest" element={<Backtest />} />
          <Route path="/trading" element={<Trading />} />
        </Routes>
      </div>
    </Router>
  );
}
