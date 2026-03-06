import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Imprint Chat",
  description: "RAG chatbot for querying Imprint research knowledge base",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
