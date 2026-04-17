import React from 'react';

interface LogoProps {
  size?: number;
  className?: string;
  showText?: boolean;
  textClassName?: string;
}

export function Logo({
  size = 28,
  className = '',
  showText = false,
  textClassName = '',
}: LogoProps) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="flex-shrink-0"
      >
        <defs>
          <linearGradient id={`primaryGradient-${size}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#22C55E', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: '#16A34A', stopOpacity: 1 }} />
          </linearGradient>
          <linearGradient id={`accentGradient-${size}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#3B82F6', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: '#1D4ED8', stopOpacity: 1 }} />
          </linearGradient>
        </defs>

        {/* Main "T" shape for Tech */}
        <path
          d="M8 6 L24 6 L24 10 L18 10 L18 26 L14 26 L14 10 L8 10 Z"
          fill={`url(#primaryGradient-${size})`}
        />

        {/* News feed lines - representing data streams */}
        <rect
          x="20"
          y="12"
          width="8"
          height="1.5"
          rx="0.75"
          fill={`url(#accentGradient-${size})`}
          opacity="0.8"
        />
        <rect
          x="20"
          y="15"
          width="6"
          height="1.5"
          rx="0.75"
          fill={`url(#accentGradient-${size})`}
          opacity="0.6"
        />
        <rect
          x="20"
          y="18"
          width="7"
          height="1.5"
          rx="0.75"
          fill={`url(#accentGradient-${size})`}
          opacity="0.4"
        />

        {/* Signal dots - representing connectivity */}
        <circle cx="4" cy="16" r="1.5" fill={`url(#primaryGradient-${size})`} />
        <circle cx="4" cy="20" r="1" fill={`url(#primaryGradient-${size})`} opacity="0.7" />
        <circle cx="4" cy="24" r="0.5" fill={`url(#primaryGradient-${size})`} opacity="0.5" />
      </svg>

      {showText && <span className={`font-bold ${textClassName}`}>Tech News Agent</span>}
    </div>
  );
}
