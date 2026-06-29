import {
  ScatterChart as RechartsScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ZAxis,
} from 'recharts';

interface DataPoint {
  x: number;
  y: number;
  z: number;
  name: string;
}

interface ScatterChartProps {
  data: DataPoint[];
  height?: number;
  title?: string;
  xLabel?: string;
  yLabel?: string;
  color?: string;
}

export default function ScatterChart({
  data,
  height = 300,
  title,
  xLabel,
  yLabel,
  color = '#2D4A3E',
}: ScatterChartProps) {
  return (
    <div className="w-full">
      {title && (
        <h4 className="font-serif text-base font-normal text-brand-900 mb-4">{title}</h4>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <RechartsScatterChart margin={{ top: 8, right: 8, bottom: 20, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#EDE6D8" />
          <XAxis
            dataKey="x"
            name={xLabel || 'X'}
            tick={{ fontSize: 11, fontFamily: 'JetBrains Mono', fill: '#A09888' }}
            tickLine={false}
            axisLine={{ stroke: '#E0D8CC' }}
            label={xLabel ? { value: xLabel, position: 'bottom', style: { fontSize: 11, fill: '#A09888', fontFamily: 'Inter' } } : undefined}
          />
          <YAxis
            dataKey="y"
            name={yLabel || 'Y'}
            tick={{ fontSize: 11, fontFamily: 'JetBrains Mono', fill: '#A09888' }}
            tickLine={false}
            axisLine={false}
          />
          <ZAxis dataKey="z" range={[40, 160]} />
          <Tooltip
            contentStyle={{
              background: '#FFFFFF',
              border: '1px solid #E0D8CC',
              borderRadius: '8px',
              fontSize: '13px',
              fontFamily: 'Inter',
            }}
            formatter={(value: number, name: string) => [value, name]}
          />
          <Scatter data={data} fill={color} opacity={0.7} />
        </RechartsScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
