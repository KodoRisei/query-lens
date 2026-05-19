import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QueryLens — AI-powered SQL Review",
  description:
    "Deterministic SQL analysis augmented by AI. Detect anti-patterns, visualize execution plans, and get intelligent rewrite suggestions.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
