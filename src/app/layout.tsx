import type { Metadata, Viewport } from "next";
import { Figtree, Newsreader } from "next/font/google";
import { Providers } from "@/components/Providers";
import "./globals.css";

const serif = Newsreader({
  variable: "--font-serif",
  subsets: ["latin"],
  weight: ["500", "600"],
  display: "swap",
});

const body = Figtree({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Plantagenet Planning Advisor",
  description:
    "Plain-English planning guidance for the Shire of Plantagenet — sheds, fences, granny flats and water tanks, checked against your lot with sources shown.",
};

export const viewport: Viewport = {
  themeColor: "#2f3b33",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en-AU"
      className={`${serif.variable} ${body.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-stone font-sans text-ink">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
