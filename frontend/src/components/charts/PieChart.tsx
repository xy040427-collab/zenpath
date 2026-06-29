import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';

interface PieChartProps {
  data: { name: string; value: number; color: string }[];
  height?: number;
  title?: string;
  innerRadius?: number;
  outerRadius?: number;
}

export default function PieChart({
  data,
  height = 280,
  title,
  innerRadius = 50,
  outerRadius = 90,
}: PieChartProps) {
  return (
    <div className="w-full">
      {title && (
        <h4 className="font-serif text-base font-normal text-brand-900 mb-4">{title}</h4>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <RechartsPieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            dataKey="value"
            paddingAngle={2}
          >
            {data.map((entry, index) => (
              <Cell key={index} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: '#FFFFFF',
              border: '1px solid #E0D8CC',
              borderRadius: '8px',
              fontSize: '13px',
              fontFamily: 'Inter',
            }}
          />
          <Legend
            formatter={(value: string) => (
              <span className="font-sans text-xs font-light text-ink">{value}</span>
            )}
          />
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  );
}
