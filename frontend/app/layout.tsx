import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Interview Prep Copilot",
  description: "AI interview workspace for role-fit analysis, mock interviews, and voice coaching.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body>
        <div className="appBackdrop" />
        <div className="appBackdropGlow appBackdropGlowLeft" />
        <div className="appBackdropGlow appBackdropGlowRight" />
        <div className="appChrome">{children}</div>
      </body>
    </html>
  );
}
