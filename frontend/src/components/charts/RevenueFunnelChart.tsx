import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { formatCurrency } from '@/lib/formatters';

interface RevenueFunnelChartProps {
  grossFailed: number;
  recoverable: number;
  recovered: number;
  className?: string;
}

export const RevenueFunnelChart: React.FC<RevenueFunnelChartProps> = ({
  grossFailed,
  recoverable,
  recovered,
  className,
}) => {
  const chartData = [
    {
      stage: 'Gross Failed',
      amount: grossFailed,
      color: '#EC4899', // Pink
    },
    {
      stage: 'Est. Recoverable',
      amount: recoverable,
      color: '#6366F1', // Primary Indigo
    },
    {
      stage: 'Captured / Recovered',
      amount: recovered,
      color: '#10B981', // Emerald
    },
  ];

  return (
    <div className={className || 'w-full h-56'}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 5 }}>
          <XAxis
            dataKey="stage"
            tick={{ fill: '#9CA3AF', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            hide
            tickFormatter={(val: number) => `₹${(val / 100000).toFixed(0)}L`}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload;
                return (
                  <div className="bg-surface-solid border border-border px-3 py-2 rounded-xl shadow-xl">
                    <p className="text-xs font-semibold text-white">{item.stage}</p>
                    <p className="text-xs text-indigo-300 mt-0.5">
                      Amount: <span className="font-bold">{formatCurrency(item.amount)}</span>
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="amount" radius={[8, 8, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`funnel-cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
