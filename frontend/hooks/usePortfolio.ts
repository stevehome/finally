'use client'

import { useState, useEffect } from 'react'
import type { Portfolio } from '@/types/market'

export function usePortfolio() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)

  useEffect(() => {
    const fetch_ = () =>
      fetch('/api/portfolio')
        .then(r => r.json())
        .then((data: Portfolio) => setPortfolio(data))
        .catch(() => {})

    fetch_()
    const interval = setInterval(fetch_, 5000)
    return () => clearInterval(interval)
  }, [])

  return portfolio
}
