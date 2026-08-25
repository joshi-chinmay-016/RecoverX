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
import { formatEnum } from '@/lib/formatters';

interface FailureDistributionChartProps {
  data: Record<string, number>;
  className?: string;
}

const COLORS = [
  '#6366F1', // Primary Indigo
  '#EC4899', // Pink
  '#8B5CF6', // Purple
  '#3B82F6', // Blue
  '#F59E0B', // Amber
  '#10B981', // Emerald
  '#06B6D4', // Cyan
  '#64748B', // Slate
];

export const FailureDistributionChart: React.FC<FailureDistributionChartProps> = ({
  data,
  className,
}) => {
  const chartData = Object.entries(data || {}).map(([category, count]) => ({
    category: formatEnum(category),
    rawCategory: category,
    count,
  }));

  if (chartData.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-xs text-gray-500">
        No failure category data available
      </div>
    );
  }

  return (
    <div className={className || 'w-full h-56'}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
        >
          <XAxis type="number" hide />
          <YAxis
            dataKey="category"
            type="category"
            width={120}
            tick={{ fill: '#9CA3AF', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload;
                return (
                  <div className="bg-surface-solid border border-border px-3 py-2 rounded-xl shadow-xl">
                    <p className="text-xs font-semibold text-white">{item.category}</p>
                    <p className="text-xs text-indigo-300 mt-0.5">
                      Failures: <span className="font-bold">{item.count}</span>
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="count" radius={[0, 6, 6, 0]}>
            {chartData.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
