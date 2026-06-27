import type { Metadata, Viewport } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import type { ReactNode } from "react";
import { Suspense } from "react";
import { AppShell } from "@/components/AppShell";
import { PwaRegister } from "@/components/PwaRegister";

const plusJakartaSans = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-plus-jakarta-sans" });

export const metadata: Metadata = {
  title: "MindMirror",
  description: "AI-powered CBT companion for emotional reflection and support.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "MindMirror",
  },
};

export const viewport: Viewport = {
  themeColor: "#7C3AED",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className={plusJakartaSans.variable}>
      <head>
        <link rel="apple-touch-icon" href="/icons/icon-192.svg" />
      </head>
      <body className="bg-mindmirror-bg font-sans text-mindmirror-primary antialiased">
        <AppShell>{children}</AppShell>
        <Suspense fallback={null}>
          <PwaRegister />
        </Suspense>
      </body>
    </html>
  );
}
