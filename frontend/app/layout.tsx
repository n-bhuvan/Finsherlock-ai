import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";

export const metadata: Metadata = {
  title: "RingGuard AI — Risk Operations Center",
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
      <body className="antialiased bg-[#090d16] text-slate-100 flex min-h-screen">
        {/* Left Navigation Sidebar */}
        <Sidebar />

        {/* Main Application Area */}
        <div className="flex-1 flex flex-col min-w-0 bg-[#090d16] bg-grid-pattern">
          <Header />
          <main className="flex-1 p-5 sm:p-7 overflow-y-auto max-w-[1720px] w-full mx-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
