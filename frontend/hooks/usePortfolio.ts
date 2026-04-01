'use client'

import { useState, useEffect, useCallback } from 'react'
import type { Portfolio } from '@/types/market'

export function usePortfolio() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)

  const fetch_ = useCallback(() => {
    fetch('/api/portfolio')
      .then(r => r.json())
      .then((data: Portfolio) => setPortfolio(data))
      .catch(() => {})
  }, [])

  useEffect(() => {
    fetch_()
    const interval = setInterval(fetch_, 5000)
    return () => clearInterval(interval)
  }, [fetch_])

  return { portfolio, refetch: fetch_ }
}
