'use client'

import { motion } from 'framer-motion'
import { MetricCard } from '@/components/ui/MetricCard'

interface MetricsDashboardProps {
  metrics: {
    total_conversations: number
    resolved_count: number
    escalation_count: number
  }
}

export function MetricsDashboard({ metrics }: MetricsDashboardProps) {
  const total = metrics.total_conversations
  const resolved = metrics.resolved_count
  const escalations = metrics.escalation_count
  const resolutionRate = total > 0 ? (resolved / total * 100) : 0

  return (
    <motion.div
      className="grid grid-cols-2 gap-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      {/* Large Card - Total Conversations */}
      <MetricCard
        label="Total Conversations"
        value={total.toLocaleString()}
        trend="+12% from last week"
        large
        showProgress
        progressValue={resolutionRate}
      />
      
      {/* Small Card - Resolved */}
      <MetricCard
        label="Resolved"
        value={resolved.toLocaleString()}
        color="text-accent"
      />
      
      {/* Small Card - Escalations */}
      <MetricCard
        label="Escalations"
        value={escalations.toLocaleString()}
        color="text-red-500"
      />
    </motion.div>
  )
}