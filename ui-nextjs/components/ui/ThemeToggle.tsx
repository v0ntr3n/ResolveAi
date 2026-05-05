'use client'

import * as React from 'react'
import { Moon, Sun } from '@phosphor-icons/react'
import { useTheme } from 'next-themes'
import { motion } from 'framer-motion'

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = React.useState(false)

  React.useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return <div className="w-10 h-10" />
  }

  const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)

  return (
    <motion.button
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      className="p-2 rounded-full bg-base-200 dark:bg-base-800 text-base-600 dark:text-base-300 hover:bg-base-300 dark:hover:bg-base-700 transition-colors"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      aria-label="Toggle theme"
    >
      {isDark ? (
        <Sun size={20} weight="bold" />
      ) : (
        <Moon size={20} weight="bold" />
      )}
    </motion.button>
  )
}
