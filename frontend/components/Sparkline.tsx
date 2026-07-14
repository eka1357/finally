"use client";

export function Sparkline({
  values,
  width = 96,
  height = 24,
  positive = true,
}: {
  values: number[];
  width?: number;
  height?: number;
  positive?: boolean;
}) {
  if (!values || values.length < 2) {
    return (
      <svg width={width} height={height} className="opacity-30">
        <line
          x1={0}
          y1={height / 2}
          x2={width}
          y2={height / 2}
          stroke="#30363d"
          strokeWidth={1}
        />
      </svg>
    );
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const pts = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * width;
      const y = height - ((v - min) / span) * (height - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const color = positive ? "#3fb950" : "#f85149";
  const last = values[values.length - 1];
  const first = values[0];
  const up = last >= first;

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        fill="none"
        stroke={up ? "#3fb950" : "#f85149"}
        strokeWidth={1.5}
        points={pts}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <circle
        cx={width}
        cy={
          height - ((last - min) / span) * (height - 4) - 2
        }
        r={2}
        fill={color}
      />
    </svg>
  );
}
