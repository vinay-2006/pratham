import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@xyflow/react/dist/style.css";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PRATHAM System Atlas",
  description: "Interactive Architecture & Workflow Explorer",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex bg-[#0a0a0a] text-[#ededed]">
        <Sidebar />
        <main className="flex-1 ml-64 min-h-screen overflow-x-hidden relative">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900/20 via-[#0a0a0a] to-[#0a0a0a] -z-10 pointer-events-none" />
          {children}
        </main>
      </body>
    </html>
  );
}
