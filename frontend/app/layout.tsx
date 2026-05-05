import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "StudyWise AI",
  description: "Citation-backed AI study assistant for uploaded learning materials.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
