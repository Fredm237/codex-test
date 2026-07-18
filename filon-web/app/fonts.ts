import localFont from "next/font/local";

// Fraunces — high-contrast display serif (optical-size axis), self-hosted.
export const fraunces = localFont({
  src: [
    { path: "./fonts/Fraunces-opsz-normal.woff2", style: "normal" },
    { path: "./fonts/Fraunces-opsz-italic.woff2", style: "italic" },
  ],
  variable: "--font-serif",
  display: "swap",
  weight: "100 900",
});
