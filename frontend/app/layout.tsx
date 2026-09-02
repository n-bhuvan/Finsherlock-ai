import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RingGuard AI — Network-Aware Abuse-Ring Detection",
  description:
    "Network-Aware Abuse-Ring Detection & Evidence-First Risk Investigation — Razorpay AI Buildathon 2026",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-grid-pattern selection:bg-sky-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
