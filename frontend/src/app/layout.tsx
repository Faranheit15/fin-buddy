import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthHashCatcher } from "@/features/auth/auth-hash-catcher";
import { AuthProvider } from "@/features/auth/auth-provider";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: {
    default: "Fin Buddy",
    template: "%s · Fin Buddy",
  },
  description:
    "Track credit cards, billing cycles, spend ledgers, and friend balances — built for India.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col font-sans">
        <TooltipProvider>
          <AuthProvider>
            <AuthHashCatcher />
            {children}
          </AuthProvider>
        </TooltipProvider>
      </body>
    </html>
  );
}
