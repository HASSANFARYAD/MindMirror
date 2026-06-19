import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import type { ReactNode } from "react";
import { AppShell } from "@/components/AppShell";

const plusJakartaSans = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-plus-jakarta-sans" });

export const metadata: Metadata = {
  title: "MindMirror",
  description: "AI-powered CBT companion for emotional reflection and support.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className={plusJakartaSans.variable}>
      <body className="bg-mindmirror-bg font-sans text-mindmirror-primary antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
