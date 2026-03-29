import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ChatGPT Sessions",
  description: "Frontend for Spring Boot + MongoDB + MinIO"
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
