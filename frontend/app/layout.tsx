import "./globals.css";
import type { Metadata } from "next";
import { FeatureFlagProvider } from "../lib/feature-flags/provider";

export const metadata: Metadata = {
  title: "ChatGPTSessions",
  description: "Frontend for FastAPI or Spring Boot with MongoDB, MinIO, and Ollama"
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-Hant">
      <body>
        <FeatureFlagProvider context={{ environment: "development" }}>
          {children}
        </FeatureFlagProvider>
      </body>
    </html>
  );
}
