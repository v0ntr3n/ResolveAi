'use client'

import { motion } from 'framer-motion'

interface BentoCardProps {
  children: React.ReactNode
  className?: string
  large?: boolean
}

export function BentoCard({ children, className = '', large = false }: BentoCardProps) {
  return (
    <motion.div
      className={`bento-card ${large ? 'row-span-2 p-8' : ''} ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -2 }}
    >
      {children}
    </motion.div>
  )
}
