import { MobileWeek } from "@/utils/mobileHome"

export function WeekChart({ weeks }: { weeks: MobileWeek[] }) {
  const max = Math.max(1, ...weeks.map((week) => week.count))
  return (
    <svg viewBox="0 0 330 108" width="100%" height="96" role="img" aria-label="Applications by week">
      {weeks.map((week, index) => {
        const height = week.count === 0 ? 0 : Math.max(4, Math.round((week.count / max) * 64))
        const x = 14 + index * 50
        const y = 78 - height
        const current = week.current
        return (
          <g key={`${week.label}-${index}`}>
            {height > 0 ? (
              <rect
                x={x}
                y={y}
                width="22"
                height={height}
                rx="4"
                fill={current ? "#F8B500" : "#18181B"}
                opacity={current ? 1 : 0.85}
              />
            ) : null}
            <text
              x={x + 11}
              y="98"
              textAnchor="middle"
              fontSize="9"
              fill="#71717A"
              fontFamily="Inter, sans-serif"
            >
              {week.label}
            </text>
            {week.count > 0 ? (
              <text
                x={x + 11}
                y={y - 4}
                textAnchor="middle"
                fontSize="9"
                fontWeight="600"
                fill="#09090B"
                fontFamily="Inter, sans-serif"
              >
                {week.count}
              </text>
            ) : null}
          </g>
        )
      })}
    </svg>
  )
}
