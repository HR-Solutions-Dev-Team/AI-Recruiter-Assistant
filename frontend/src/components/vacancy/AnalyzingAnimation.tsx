/**
 * Анимация робота, анализирующего документ.
 * Показывается во время парсинга вакансии.
 */

interface AnalyzingAnimationProps {
  message?: string;
}

export default function AnalyzingAnimation({
  message = 'Анализируем вакансию...'
}: AnalyzingAnimationProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      {/* Animated Robot */}
      <div className="relative w-48 h-48 mb-8">
        {/* Background glow */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full animate-pulse opacity-50" />

        {/* Robot SVG */}
        <svg
          viewBox="0 0 200 200"
          className="w-full h-full relative z-10"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Robot Head */}
          <g className="animate-[bobble_2s_ease-in-out_infinite]">
            {/* Head base */}
            <rect
              x="60"
              y="30"
              width="80"
              height="60"
              rx="12"
              fill="#374151"
              className="drop-shadow-lg"
            />

            {/* Antenna */}
            <line
              x1="100"
              y1="30"
              x2="100"
              y2="15"
              stroke="#374151"
              strokeWidth="4"
              strokeLinecap="round"
            />
            <circle
              cx="100"
              cy="12"
              r="6"
              fill="#3B82F6"
              className="animate-pulse"
            />

            {/* Eyes */}
            <g className="animate-[blink_3s_ease-in-out_infinite]">
              <circle cx="80" cy="55" r="10" fill="#1F2937" />
              <circle cx="120" cy="55" r="10" fill="#1F2937" />
              {/* Eye highlights - scanning effect */}
              <circle cx="80" cy="55" r="5" fill="#3B82F6" className="animate-[scan_1.5s_ease-in-out_infinite]" />
              <circle cx="120" cy="55" r="5" fill="#3B82F6" className="animate-[scan_1.5s_ease-in-out_infinite_0.2s]" />
            </g>

            {/* Mouth - processing indicator */}
            <rect
              x="85"
              y="72"
              width="30"
              height="6"
              rx="3"
              fill="#1F2937"
            />
            <rect
              x="85"
              y="72"
              width="30"
              height="6"
              rx="3"
              fill="#10B981"
              className="animate-[loading-bar_1.5s_ease-in-out_infinite]"
              style={{ transformOrigin: 'left center' }}
            />
          </g>

          {/* Robot Body */}
          <rect
            x="55"
            y="95"
            width="90"
            height="70"
            rx="8"
            fill="#4B5563"
          />

          {/* Chest display */}
          <rect
            x="70"
            y="105"
            width="60"
            height="40"
            rx="4"
            fill="#1F2937"
          />

          {/* Data lines on display */}
          <g className="animate-[data-scroll_2s_linear_infinite]">
            <rect x="75" y="112" width="40" height="3" rx="1" fill="#3B82F6" opacity="0.8" />
            <rect x="75" y="120" width="35" height="3" rx="1" fill="#10B981" opacity="0.6" />
            <rect x="75" y="128" width="45" height="3" rx="1" fill="#3B82F6" opacity="0.7" />
            <rect x="75" y="136" width="30" height="3" rx="1" fill="#10B981" opacity="0.5" />
          </g>

          {/* Arms */}
          {/* Left arm holding document */}
          <g className="animate-[arm-move_2s_ease-in-out_infinite]">
            <rect
              x="25"
              y="100"
              width="30"
              height="12"
              rx="6"
              fill="#6B7280"
            />
            {/* Hand */}
            <circle cx="25" cy="106" r="8" fill="#9CA3AF" />

            {/* Document in hand */}
            <g className="animate-[doc-float_3s_ease-in-out_infinite]">
              <rect
                x="5"
                y="85"
                width="28"
                height="36"
                rx="2"
                fill="white"
                stroke="#E5E7EB"
                strokeWidth="2"
              />
              {/* Document lines */}
              <rect x="9" y="92" width="20" height="2" rx="1" fill="#D1D5DB" />
              <rect x="9" y="98" width="16" height="2" rx="1" fill="#D1D5DB" />
              <rect x="9" y="104" width="18" height="2" rx="1" fill="#D1D5DB" />
              <rect x="9" y="110" width="14" height="2" rx="1" fill="#D1D5DB" />
            </g>
          </g>

          {/* Right arm */}
          <g className="animate-[arm-wave_1.5s_ease-in-out_infinite]" style={{ transformOrigin: '145px 106px' }}>
            <rect
              x="145"
              y="100"
              width="30"
              height="12"
              rx="6"
              fill="#6B7280"
            />
            <circle cx="175" cy="106" r="8" fill="#9CA3AF" />
          </g>

          {/* Legs */}
          <rect x="70" y="165" width="15" height="25" rx="4" fill="#6B7280" />
          <rect x="115" y="165" width="15" height="25" rx="4" fill="#6B7280" />

          {/* Feet */}
          <rect x="65" y="185" width="25" height="10" rx="3" fill="#4B5563" />
          <rect x="110" y="185" width="25" height="10" rx="3" fill="#4B5563" />
        </svg>

        {/* Floating particles */}
        <div className="absolute top-1/4 right-0 w-2 h-2 bg-blue-400 rounded-full animate-[float-particle_3s_ease-in-out_infinite]" />
        <div className="absolute top-1/2 right-4 w-1.5 h-1.5 bg-green-400 rounded-full animate-[float-particle_2.5s_ease-in-out_infinite_0.5s]" />
        <div className="absolute bottom-1/3 left-0 w-2 h-2 bg-purple-400 rounded-full animate-[float-particle_2.8s_ease-in-out_infinite_1s]" />
      </div>

      {/* Loading text */}
      <div className="text-center">
        <p className="text-lg font-medium text-gray-900 mb-2">{message}</p>
        <p className="text-sm text-gray-500">
          Извлекаем данные с помощью ИИ
        </p>

        {/* Progress dots */}
        <div className="flex justify-center gap-1.5 mt-4">
          <div className="w-2 h-2 bg-gray-900 rounded-full animate-[bounce_1s_ease-in-out_infinite]" />
          <div className="w-2 h-2 bg-gray-900 rounded-full animate-[bounce_1s_ease-in-out_infinite_0.1s]" />
          <div className="w-2 h-2 bg-gray-900 rounded-full animate-[bounce_1s_ease-in-out_infinite_0.2s]" />
        </div>
      </div>

      {/* Custom keyframes */}
      <style>{`
        @keyframes bobble {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-5px); }
        }

        @keyframes blink {
          0%, 90%, 100% { opacity: 1; }
          95% { opacity: 0.3; }
        }

        @keyframes scan {
          0%, 100% { transform: translateX(-2px); }
          50% { transform: translateX(2px); }
        }

        @keyframes loading-bar {
          0% { transform: scaleX(0); }
          50% { transform: scaleX(1); }
          100% { transform: scaleX(0); }
        }

        @keyframes data-scroll {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }

        @keyframes arm-move {
          0%, 100% { transform: rotate(0deg); }
          50% { transform: rotate(-5deg); }
        }

        @keyframes arm-wave {
          0%, 100% { transform: rotate(0deg); }
          25% { transform: rotate(10deg); }
          75% { transform: rotate(-5deg); }
        }

        @keyframes doc-float {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          50% { transform: translateY(-3px) rotate(-2deg); }
        }

        @keyframes float-particle {
          0%, 100% {
            transform: translateY(0) scale(1);
            opacity: 0.7;
          }
          50% {
            transform: translateY(-10px) scale(1.2);
            opacity: 1;
          }
        }

        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-4px); }
        }
      `}</style>
    </div>
  );
}
