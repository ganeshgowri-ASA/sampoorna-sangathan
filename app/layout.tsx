import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SampoornaSangathan | Unified Organisation OS',
  description: 'AI-Native Enterprise Platform - HRMS, CRM, Office Suite, Finance, Inventory & Projects',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  )
}
