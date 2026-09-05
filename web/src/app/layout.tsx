import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Reiterate",
  description: "A focused interface for working with Reiterate.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
