import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'FinAlly — AI Trading Workstation',
  description: 'Bloomberg-terminal-aesthetic AI trading workstation',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-bg-primary text-text-primary min-h-screen">
        {children}
      </body>
    </html>
  )
}
