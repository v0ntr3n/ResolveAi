'use client'

import { motion } from 'framer-motion'
import { Package, Money, MapPin, Book } from '@phosphor-icons/react'
import { QuickActionButton } from '@/components/ui/QuickActionButton'

interface QuickActionsProps {
  onAction: (query: string) => void
}

export function QuickActions({ onAction }: QuickActionsProps) {
  const actions = [
    { label: 'Track Order', icon: <Package size={24} />, query: 'Where is my order DEMO-001?' },
    { label: 'Request Refund', icon: <Money size={24} />, query: 'Refund order DEMO-002 because it is damaged' },
    { label: 'Change Address', icon: <MapPin size={24} />, query: 'Change address for DEMO-003 to 123 Main Street' },
    { label: 'Policy Info', icon: <Book size={24} />, query: 'What is the refund policy?' },
  ]

  return (
    <motion.div
      className="grid grid-cols-2 gap-3"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      {actions.map((action, idx) => (
        <QuickActionButton
          key={idx}
          label={action.label}
          icon={action.icon}
          onClick={() => onAction(action.query)}
        />
      ))}
    </motion.div>
  )
}
