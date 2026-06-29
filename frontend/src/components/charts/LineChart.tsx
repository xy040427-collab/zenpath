import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface LineChartProps {
  data: { year: number; value: number; label?: string }[];
  height?: number;
  color?: string;
  title?: string;
  dataKey?: string;
  xKey?: string;
}

export default function LineChart({
  data,
  height = 250,
  color = '#2D4A3E',
  title,
  dataKey = 'value',
  xKey = 'year',
}: LineChartProps) {
  const [key, setKey] = useState(0);

  useEffect(() => {
    // Trigger re-render to animate line drawing
    const timer = setTimeout(() => setKey(1), 300);
    return () => clearTimeout(timer);
  }, []);

  return (
    <motion.div
      className="w-full"
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
    >
      {title && (
        <h4 className="font-serif text-base font-normal text-brand-900 mb-4">{title}</h4>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <RechartsLineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#EDE6D8" vertical={false} />
          <XAxis
            dataKey={xKey}
            tick={{ fontSize: 11, fontFamily: 'JetBrains Mono', fill: '#A09888' }}
            tickLine={false}
            axisLine={{ stroke: '#E0D8CC' }}
          />
          <YAxis
            tick={{ fontSize: 11, fontFamily: 'JetBrains Mono', fill: '#A09888' }}
            tickLine={false}
            axisLine={false}
            width={40}
          />
          <Tooltip
            contentStyle={{
              background: '#FFFFFF',
              border: '1px solid #E0D8CC',
              borderRadius: '8px',
              fontSize: '13px',
              fontFamily: 'Inter',
            }}
          />
          <Line
            key={`line-${key}`}
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            strokeWidth={2.5}
            dot={{ fill: color, r: 4, strokeWidth: 0 }}
            activeDot={{ r: 6, fill: color }}
            animationDuration={1500}
            animationEasing="ease-out"
          />
        </RechartsLineChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
