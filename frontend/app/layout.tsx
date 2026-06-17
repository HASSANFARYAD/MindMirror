import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import type { ReactNode } from "react";
import { SiteHeader } from "@/components/SiteHeader";

const plusJakartaSans = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-plus-jakarta-sans" });

export const metadata: Metadata = {
  title: "MindMirror",
  description: "AI-powered CBT companion for emotional reflection and support.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className={plusJakartaSans.variable}>
      <body className="overflow-hidden bg-mindmirror-bg font-sans text-mindmirror-primary antialiased">
        <div className="relative flex h-screen flex-col overflow-hidden bg-[radial-gradient(circle_at_20%_20%,rgba(124,58,237,0.16),transparent_28%),radial-gradient(circle_at_80%_0%,rgba(236,72,153,0.12),transparent_22%),linear-gradient(180deg,#0D0B1A_0%,#0D0B1A_100%)]">
          <SiteHeader />
          <main className="relative z-10 mx-auto min-h-0 flex-1 overflow-y-auto px-5 py-8 md:px-12 lg:px-12">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
