import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

interface PriorityPieChartProps {
  data: Record<string, number>;
  className?: string;
}

const PRIORITY_COLORS: Record<string, string> = {
  CRITICAL: '#EC4899',
  HIGH: '#F59E0B',
  MEDIUM: '#3B82F6',
  LOW: '#10B981',
};

export const PriorityPieChart: React.FC<PriorityPieChartProps> = ({ data, className }) => {
  const chartData = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    .map(priority => ({
      name: priority,
      value: data?.[priority] || 0,
    }))
    .filter(item => item.value > 0);

  if (chartData.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-xs text-gray-500">
        No priority distribution data
      </div>
    );
  }

  return (
    <div className={className || 'w-full h-56 flex items-center justify-center'}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0];
                return (
                  <div className="bg-surface-solid border border-border px-3 py-2 rounded-xl shadow-xl">
                    <p className="text-xs font-semibold text-white">{item.name}</p>
                    <p className="text-xs text-gray-300 mt-0.5">
                      Opportunities: <span className="font-bold text-white">{item.value}</span>
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={75}
            paddingAngle={4}
            dataKey="value"
          >
            {chartData.map(entry => (
              <Cell
                key={`cell-${entry.name}`}
                fill={PRIORITY_COLORS[entry.name] || '#64748B'}
                stroke="transparent"
              />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
