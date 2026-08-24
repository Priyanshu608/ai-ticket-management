import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Support AI — Operations Studio",
  description: "Intelligent Ticket Triage & TAM Account Health",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090a0f] text-zinc-100 antialiased">{children}</body>
    </html>
  );
}