import type { Metadata, Viewport } from "next";

import { Providers } from "@/app/providers";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Answerly",
    template: "%s | Answerly",
  },
  description: "AI-powered knowledge base management and customer support platform",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      dir="ltr"
      className="h-full antialiased"
      suppressHydrationWarning
    >
      <body
        className="min-h-full bg-slate-50 text-slate-950 relative"
        suppressHydrationWarning
      >
        <div className="pointer-events-none fixed inset-0 overflow-hidden z-[-1]">
          <div className="absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full bg-green-300/30 blur-3xl opacity-60 mix-blend-multiply" />
          <div className="absolute top-1/3 -left-40 w-[400px] h-[400px] rounded-full bg-pink-300/30 blur-3xl opacity-60 mix-blend-multiply" />
          <div className="absolute -bottom-40 right-1/4 w-[600px] h-[600px] rounded-full bg-blue-300/30 blur-3xl opacity-60 mix-blend-multiply" />
        </div>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
