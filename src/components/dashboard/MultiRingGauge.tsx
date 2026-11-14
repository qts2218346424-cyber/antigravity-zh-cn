import React from 'react';

export interface MultiRingGaugeMetric {
    key: string;
    label: string;
    value: number; // 0 - 100
    color: string;
    bgColor?: string;
    icon?: React.ReactNode;
}

interface MultiRingGaugeProps {
    metrics: MultiRingGaugeMetric[]; // 从外到内排序: [外环, 中环, 内环]
    centerValue: number; // 中心大字，通常为综合可用百分比
    centerLabel?: string; // 中心小字，例如 "综合加权"
    size?: number; // SVG 宽高大小，默认 150
    strokeWidth?: number; // 环线宽度，默认 7
    gap?: number; // 环间距，默认 4
}

export const MultiRingGauge: React.FC<MultiRingGaugeProps> = ({
    metrics,
    centerValue,
    centerLabel,
    size = 148,
    strokeWidth = 7,
    gap = 4.5,
}) => {
    const center = size / 2;
    // 最外环半径
    const baseRadius = center - strokeWidth;

    return (
        <div className="relative flex items-center justify-center shrink-0 select-none" style={{ width: size, height: size }}>
            <svg width={size} height={size} className="transform -rotate-90">
                {metrics.map((m, index) => {
                    const radius = baseRadius - index * (strokeWidth + gap);
                    if (radius <= 0) return null;
                    const circumference = 2 * Math.PI * radius;
                    const clampedVal = Math.min(100, Math.max(0, m.value));
                    const strokeDashoffset = circumference - (clampedVal / 100) * circumference;

                    return (
                        <g key={m.key}>
                            {/* 背景底槽环 */}
                            <circle
                                cx={center}
                                cy={center}
                                r={radius}
                                fill="transparent"
                                stroke="currentColor"
                                strokeWidth={strokeWidth}
                                className="text-gray-100 dark:text-base-300/80"
                            />
                            {/* 动态彩色进度环 */}
                            <circle
                                cx={center}
                                cy={center}
                                r={radius}
                                fill="transparent"
                                stroke={m.color}
                                strokeWidth={strokeWidth}
                                strokeDasharray={circumference}
                                strokeDashoffset={strokeDashoffset}
                                strokeLinecap="round"
                                className="transition-all duration-700 ease-out"
                            />
                        </g>
                    );
                })}
            </svg>

            {/* 中心数值与标签 */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
                <span className="text-2xl font-black font-mono tracking-tight text-gray-900 dark:text-base-content leading-none">
                    {centerValue}%
                </span>
                {centerLabel && (
                    <span className="text-[10px] font-medium text-gray-400 dark:text-gray-500 mt-1 scale-95">
                        {centerLabel}
                    </span>
                )}
            </div>
        </div>
    );
};
