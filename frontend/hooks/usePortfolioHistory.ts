'use client'

import { useState, useEffect } from 'react'

export type PortfolioSnapshot = {
  total_value: number
  recorded_at: string
}

export function usePortfolioHistory() {
  const [snapshots, setSnapshots] = useState<PortfolioSnapshot[]>([])

  useEffect(() => {
    fetch('/api/portfolio/history')
      .then(r => r.json())
      .then((data: { snapshots: PortfolioSnapshot[] }) => setSnapshots(data.snapshots))
      .catch(() => {})
  }, [])

  return { snapshots }
}
