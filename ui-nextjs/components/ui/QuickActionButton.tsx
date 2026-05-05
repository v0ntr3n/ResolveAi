'use client'

import { motion } from 'framer-motion'

interface QuickActionButtonProps {
  label: string
  icon: React.ReactNode
  onClick: () => void
}

export function QuickActionButton({ label, icon, onClick }: QuickActionButtonProps) {
  return (
    <motion.button
      onClick={onClick}
      className="quick-action-btn relative overflow-hidden group"
      whileHover={{ y: -1 }}
      whileTap={{ scale: 0.98 }}
    >
      {/* Animated background */}
      <div className="absolute inset-0 bg-accent -translate-x-full transition-transform duration-300 transition-premium group-hover:translate-x-0" />
      
      {/* Content */}
      <div className="relative z-10 flex items-center gap-3">
        <div className="flex items-center justify-center w-10 h-10 bg-base-100 dark:bg-base-800 rounded-lg text-base-600 dark:text-base-300 transition-colors duration-300 group-hover:bg-white/10 group-hover:text-white">
          {icon}
        </div>
        <span className="font-semibold text-base-900 dark:text-base-50 transition-colors duration-300 group-hover:text-white">
          {label}
        </span>
      </div>
    </motion.button>
  )
}
