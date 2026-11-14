import React from 'react';

export interface DonutSegment {
    key: string;
    label: string;
    value: number;
    color: string;
}

interface AccountDonutGaugeProps {
    total: number;
    segments: DonutSegment[];
    centerLabel?: string;
    size?: number;
    strokeWidth?: number;
}

export const AccountDonutGauge: React.FC<AccountDonutGaugeProps> = ({
    total,
    segments,
    centerLabel,
    size = 138,
    strokeWidth = 10,
}) => {
    const center = size / 2;
    const radius = center - strokeWidth;
    const circumference = 2 * Math.PI * radius;

    // 计算分段偏移
    let accumulatedAngle = 0;

    return (
        <div className="relative flex items-center justify-center shrink-0 select-none" style={{ width: size, height: size }}>
            <svg width={size} height={size} className="transform -rotate-90">
                {/* 默认空底槽 */}
                <circle
                    cx={center}
                    cy={center}
                    r={radius}
                    fill="transparent"
                    stroke="currentColor"
                    strokeWidth={strokeWidth}
                    className="text-gray-100 dark:text-base-300"
                />

                {total > 0 && segments.map((seg) => {
                    if (seg.value <= 0) return null;
                    const fraction = seg.value / total;
                    const strokeDasharray = `${fraction * circumference} ${circumference}`;
                    const strokeDashoffset = -accumulatedAngle;
                    accumulatedAngle += fraction * circumference;

                    return (
                        <circle
                            key={seg.key}
                            cx={center}
                            cy={center}
                            r={radius}
                            fill="transparent"
                            stroke={seg.color}
                            strokeWidth={strokeWidth}
                            strokeDasharray={strokeDasharray}
                            strokeDashoffset={strokeDashoffset}
                            strokeLinecap="butt"
                            className="transition-all duration-700 ease-out"
                        />
                    );
                })}
            </svg>

            {/* 中心总数字与标签 */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
                <span className="text-3xl font-black font-mono tracking-tight text-gray-900 dark:text-base-content leading-none">
                    {total}
                </span>
                {centerLabel && (
                    <span className="text-[10px] font-medium text-gray-400 dark:text-gray-500 mt-1">
                        {centerLabel}
                    </span>
                )}
            </div>
        </div>
    );
};
