'use client'

import { motion } from 'framer-motion'
import { TrendUp } from '@phosphor-icons/react'

interface MetricCardProps {
  label: string
  value: number | string
  trend?: string
  color?: string
  large?: boolean
  showProgress?: boolean
  progressValue?: number
}

export function MetricCard({
  label,
  value,
  trend,
  color = 'text-base-900',
  large = false,
  showProgress = false,
  progressValue = 0
}: MetricCardProps) {
  return (
    <div className={`bento-card ${large ? 'row-span-2 p-8' : ''}`}>
      <div className="metric-label">{label}</div>
      <div className={`metric-value ${color} mt-2`}>{value}</div>
      
      {trend && (
        <div className="mt-3 inline-flex items-center gap-1.5 rounded bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">
          <TrendUp size={12} weight="bold" />
          <span>{trend}</span>
        </div>
      )}
      
      {showProgress && (
        <div className="mt-6">
          <div className="metric-label">Resolution Rate</div>
          <div className="mt-2 flex items-center gap-4">
            <div className="flex-1 h-2 bg-base-200 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-accent rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progressValue}%` }}
                transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              />
            </div>
            <span className="text-sm font-semibold text-base-900">{progressValue.toFixed(1)}%</span>
          </div>
        </div>
      )}
    </div>
  )
}
