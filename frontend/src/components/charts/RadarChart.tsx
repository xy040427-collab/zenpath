import {
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from 'recharts';

interface RadarChartProps {
  data: { subject: string; value: number; fullMark: number }[];
  height?: number;
  title?: string;
  color?: string;
}

export default function RadarChart({
  data,
  height = 300,
  title,
  color = '#2D4A3E',
}: RadarChartProps) {
  return (
    <div className="w-full">
      {title && (
        <h4 className="font-serif text-base font-normal text-brand-900 mb-4">{title}</h4>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <RechartsRadarChart data={data}>
          <PolarGrid stroke="#EDE6D8" />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fontSize: 11, fontFamily: 'Inter', fill: '#4A4A4A' }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={{ fontSize: 10, fontFamily: 'JetBrains Mono', fill: '#A09888' }}
          />
          <Radar
            dataKey="value"
            stroke={color}
            fill={color}
            fillOpacity={0.15}
            strokeWidth={2}
          />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
}
