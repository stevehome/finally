'use client'

import type { Portfolio } from '@/types/market'
import { usePortfolioHistory } from '@/hooks/usePortfolioHistory'
import Heatmap from './Heatmap'
import PnlChart from './PnlChart'
import PositionsTable from './PositionsTable'

interface PortfolioPanelsProps {
  portfolio: Portfolio | null
}

export default function PortfolioPanels({ portfolio }: PortfolioPanelsProps) {
  const { snapshots } = usePortfolioHistory()

  if (!portfolio) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        color: '#8b949e',
        fontSize: 11,
      }}>
        Loading portfolio…
      </div>
    )
  }

  return (
    <div style={{
      display: 'grid',
      gridTemplateRows: '45% 55%',
      height: '100%',
      overflow: 'hidden',
      backgroundColor: '#0d1117',
    }}>
      {/* Heatmap — top section */}
      <div style={{ borderBottom: '1px solid #30363d', overflow: 'hidden' }}>
        <div style={{
          padding: '4px 8px',
          fontSize: 10,
          color: '#8b949e',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          borderBottom: '1px solid #21262d',
        }}>
          Positions
        </div>
        <div style={{ height: 'calc(100% - 24px)', overflow: 'hidden' }}>
          <Heatmap portfolio={portfolio} />
        </div>
      </div>

      {/* Bottom row: PnlChart + PositionsTable */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', overflow: 'hidden' }}>
        <div style={{ borderRight: '1px solid #30363d', overflow: 'hidden' }}>
          <div style={{
            padding: '4px 8px',
            fontSize: 10,
            color: '#8b949e',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            borderBottom: '1px solid #21262d',
          }}>
            P&amp;L
          </div>
          <div style={{ height: 'calc(100% - 24px)' }}>
            <PnlChart snapshots={snapshots} />
          </div>
        </div>

        <div style={{ overflow: 'hidden' }}>
          <div style={{
            padding: '4px 8px',
            fontSize: 10,
            color: '#8b949e',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            borderBottom: '1px solid #21262d',
          }}>
            Holdings
          </div>
          <div style={{ height: 'calc(100% - 24px)' }}>
            <PositionsTable portfolio={portfolio} />
          </div>
        </div>
      </div>
    </div>
  )
}
