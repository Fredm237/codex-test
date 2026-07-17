export function Logo({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="filon-lg" x1="0" y1="0" x2="32" y2="32">
          <stop stopColor="#3C7BFF" />
          <stop offset="0.5" stopColor="#8B6CFF" />
          <stop offset="1" stopColor="#24E3C6" />
        </linearGradient>
      </defs>
      <rect x="1.5" y="1.5" width="29" height="29" rx="9" stroke="url(#filon-lg)" strokeWidth="2" />
      <path d="M9 22 L15 9 L18 16 L23 10" stroke="url(#filon-lg)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
