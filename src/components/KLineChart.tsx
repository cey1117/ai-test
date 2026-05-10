import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import { KLineData } from "../types";

interface KLineChartProps {
  data: KLineData[];
  height?: number;
}

export const KLineChart = ({ data, height = 400 }: KLineChartProps) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts>();

  useEffect(() => {
    if (!chartRef.current) return;

    chartInstance.current = echarts.init(chartRef.current);

    const option = {
      backgroundColor: "#0f172a",
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "cross",
        },
      },
      grid: [
        {
          left: "10%",
          right: "8%",
          top: "10%",
          height: "55%",
        },
        {
          left: "10%",
          right: "8%",
          top: "72%",
          height: "15%",
        },
      ],
      xAxis: [
        {
          type: "category",
          data: data.map((d) => d.date),
          boundaryGap: false,
          axisLine: { lineStyle: { color: "#475569" } },
          axisLabel: { color: "#94a3b8", fontSize: 10 },
          min: "dataMin",
          max: "dataMax",
        },
        {
          type: "category",
          gridIndex: 1,
          data: data.map((d) => d.date),
          boundaryGap: false,
          axisLine: { lineStyle: { color: "#475569" } },
          axisLabel: { show: false },
          splitLine: { show: false },
        },
      ],
      yAxis: [
        {
          type: "value",
          scale: true,
          splitArea: {
            show: true,
            areaStyle: { color: ["rgba(250,250,250,0.02)", "rgba(200,200,200,0.02)"] },
          },
          axisLine: { lineStyle: { color: "#475569" } },
          axisLabel: { color: "#94a3b8" },
          splitLine: { lineStyle: { color: "#334155" } },
        },
        {
          type: "value",
          gridIndex: 1,
          scale: true,
          splitNumber: 2,
          axisLine: { lineStyle: { color: "#475569" } },
          axisLabel: { color: "#94a3b8" },
          splitLine: { lineStyle: { color: "#334155" } },
        },
      ],
      dataZoom: [
        {
          type: "inside",
          xAxisIndex: [0, 1],
          start: 50,
          end: 100,
        },
        {
          show: true,
          xAxisIndex: [0, 1],
          type: "slider",
          bottom: "5%",
          start: 50,
          end: 100,
          borderColor: "#334155",
          backgroundColor: "#1e293b",
          fillerColor: "rgba(6, 182, 212, 0.2)",
          handleStyle: { color: "#06b6d4" },
        },
      ],
      series: [
        {
          name: "K线",
          type: "candlestick",
          data: data.map((d) => [d.open, d.close, d.low, d.high]),
          itemStyle: {
            color: "#10b981",
            color0: "#ef4444",
            borderColor: "#10b981",
            borderColor0: "#ef4444",
          },
        },
        {
          name: "成交量",
          type: "bar",
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: data.map((d, i) => ({
            value: d.volume,
            itemStyle: {
              color: i > 0 && data[i].close >= data[i - 1].close ? "#10b981" : "#ef4444",
            },
          })),
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
  }, [data]);

  return <div ref={chartRef} style={{ height: `${height}px`, width: "100%" }} />;
};
