import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ChatGPT Sessions",
  description: "Frontend for FastAPI or Spring Boot with MongoDB, MinIO, and Ollama"
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-Hant">
      <body>{children}</body>
    </html>
  );
}
