import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SupportFlow | Operations Workspace",
  description: "Explore support ticket signals, account health, and grounded AI triage.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0b111d] text-slate-100 antialiased">{children}</body>
    </html>
  );
}
