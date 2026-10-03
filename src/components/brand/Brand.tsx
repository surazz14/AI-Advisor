import Link from "next/link";

/** Two-peak outline of the Porongurup range — the app mark. */
export function PeakMark({
  className = "h-7 w-7",
  strokeWidth = 1.8,
}: {
  className?: string;
  strokeWidth?: number;
}) {
  return (
    <svg viewBox="0 0 28 28" className={className} aria-hidden fill="none">
      <path
        d="M2 22 L10 10 L15 16 L19 8 L26 22 Z"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Logo lock-up that links home. Inherits text colour from its parent. */
export function BrandLink({
  label = "Plantagenet Planning Advisor",
  className = "",
}: {
  label?: string;
  className?: string;
}) {
  return (
    <Link
      href="/"
      className={`inline-flex min-h-11 items-center gap-2.5 rounded-lg no-underline ${className}`}
    >
      <PeakMark />
      <span className="text-[15px] font-semibold sm:text-base">{label}</span>
    </Link>
  );
}

/** Round avatar used for advisor messages. */
export function AdvisorAvatar({ size = "h-8 w-8" }: { size?: string }) {
  return (
    <span
      className={`inline-flex ${size} flex-none items-center justify-center rounded-full bg-accent text-white`}
      aria-hidden
    >
      <PeakMark className="h-[18px] w-[18px]" strokeWidth={2.4} />
    </span>
  );
}

type ContourVariant = "hero" | "band" | "light";

/**
 * Topographic contour lines (Porongurup range) drawn behind headers.
 * Purely decorative.
 */
export function Contours({
  variant = "band",
  className = "",
}: {
  variant?: ContourVariant;
  className?: string;
}) {
  const stroke = variant === "light" ? "#ddd4c4" : "#4a5d4f";

  if (variant === "band") {
    return (
      <svg
        viewBox="0 0 1160 200"
        preserveAspectRatio="none"
        className={`pointer-events-none absolute inset-0 h-full w-full ${className}`}
        aria-hidden
      >
        <g fill="none" stroke={stroke} strokeWidth="1.2">
          <path d="M0 170 C180 140 280 100 440 108 S700 50 840 74 S1060 120 1160 98" />
          <path d="M0 188 C200 160 300 124 460 130 S720 78 860 98 S1070 142 1160 122" />
          <path d="M0 206 C220 180 320 148 480 152 S740 104 880 122 S1080 164 1160 146" />
          <path d="M500 100 C560 60 660 44 720 60 S800 92 786 106" />
          <path d="M540 104 C590 74 660 64 706 76 S770 98 760 108" />
        </g>
      </svg>
    );
  }

  return (
    <svg
      viewBox="0 0 1440 720"
      preserveAspectRatio="xMidYMid slice"
      className={`pointer-events-none absolute inset-0 h-full w-full ${className}`}
      aria-hidden
    >
      <g fill="none" stroke={stroke} strokeWidth="1.2">
        <path d="M0 560 C220 500 360 420 560 430 S880 300 1060 340 S1300 430 1440 390" />
        <path d="M0 590 C240 535 380 460 580 470 S900 345 1080 382 S1320 470 1440 430" />
        <path d="M0 620 C260 570 400 500 600 510 S920 390 1100 424 S1340 510 1440 470" />
        <path d="M0 650 C280 605 420 540 620 550 S940 435 1120 466 S1360 550 1440 510" />
        <path d="M0 680 C300 640 440 580 640 590 S960 480 1140 508 S1380 590 1440 550" />
        <path d="M820 300 C900 220 1040 190 1130 220 S1240 290 1210 320" />
        <path d="M860 310 C930 250 1040 232 1110 252 S1200 300 1180 322" />
        <path d="M900 318 C960 280 1040 270 1090 284 S1160 310 1150 324" />
      </g>
    </svg>
  );
}

/** Small inline icons (stroke, currentColor). */
export function Icon({
  name,
  className = "h-5 w-5",
}: {
  name:
    | "pin"
    | "arrow"
    | "plus"
    | "menu"
    | "close"
    | "copy"
    | "check"
    | "chevron"
    | "external"
    | "info"
    | "alert"
    | "wifi"
    | "trash"
    | "bulb";
  className?: string;
}) {
  const common = {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    className,
    "aria-hidden": true,
  };
  switch (name) {
    case "pin":
      return (
        <svg {...common}>
          <path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z" />
          <circle cx="12" cy="9.5" r="2.5" />
        </svg>
      );
    case "arrow":
      return (
        <svg {...common}>
          <path d="M5 12h14M13 6l6 6-6 6" />
        </svg>
      );
    case "plus":
      return (
        <svg {...common}>
          <path d="M12 5v14M5 12h14" />
        </svg>
      );
    case "menu":
      return (
        <svg {...common}>
          <path d="M4 7h16M4 12h16M4 17h10" />
        </svg>
      );
    case "close":
      return (
        <svg {...common}>
          <path d="M6 6l12 12M18 6L6 18" />
        </svg>
      );
    case "copy":
      return (
        <svg {...common}>
          <rect x="8" y="8" width="12" height="12" rx="2" />
          <path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3" />
        </svg>
      );
    case "check":
      return (
        <svg {...common}>
          <path d="M5 12.5l4.5 4.5L19 7.5" />
        </svg>
      );
    case "chevron":
      return (
        <svg {...common}>
          <path d="M6 9l6 6 6-6" />
        </svg>
      );
    case "external":
      return (
        <svg {...common}>
          <path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" />
        </svg>
      );
    case "info":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 11v5M12 8v.5" />
        </svg>
      );
    case "alert":
      return (
        <svg {...common}>
          <path d="M12 3l9.5 17h-19z" />
          <path d="M12 10v4M12 17v.5" />
        </svg>
      );
    case "wifi":
      return (
        <svg {...common}>
          <path d="M2 8.5a15 15 0 0 1 20 0M5.5 12a10 10 0 0 1 13 0M9 15.5a5 5 0 0 1 6 0M12 19v.5" />
        </svg>
      );
    case "trash":
      return (
        <svg {...common}>
          <path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-12M9 7V4h6v3" />
        </svg>
      );
    case "bulb":
      return (
        <svg {...common}>
          <path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9V16h7v-2.1A6 6 0 0 0 12 3z" />
        </svg>
      );
  }
}

/** Small spinning ring for busy states. */
export function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <span
      className={`spin inline-block flex-none rounded-full border-2 border-current border-r-transparent ${className}`}
      aria-hidden
    />
  );
}
