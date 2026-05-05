'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CaretDown, CaretUp } from '@phosphor-icons/react'
import { MetricsDashboard } from '@/components/dashboard/MetricsDashboard'
import { QuickActions } from '@/components/dashboard/QuickActions'
import { DemoOrders } from '@/components/dashboard/DemoOrders'
import { ChatInterface, type ChatInterfaceRef } from '@/components/chat/ChatInterface'
import { fetchMetrics, type Metrics } from '@/lib/api'

import { ThemeToggle } from '@/components/ui/ThemeToggle'

export default function Home() {
  const [metrics, setMetrics] = useState<Metrics>({
    total_conversations: 0,
    resolved_count: 0,
    escalation_count: 0,
  })
  const [showHelp, setShowHelp] = useState(false)
  const chatInterfaceRef = useRef<ChatInterfaceRef>(null)

  useEffect(() => {
    fetchMetrics()
      .then(setMetrics)
      .catch(console.error)
  }, [])

  const refreshMetrics = () => {
    fetchMetrics()
      .then(setMetrics)
      .catch(console.error)
  }

  const handleQuickAction = (query: string) => {
    chatInterfaceRef.current?.sendMessageToBackend(query)
  }

  return (
    <main className="relative min-h-screen bg-base-50 dark:bg-base-950 transition-colors duration-300 overflow-x-clip">
      {/* Background Glowing Orbs */}
      <div className="fixed top-[-200px] left-[-200px] w-[600px] h-[600px] bg-accent/20 dark:bg-accent/10 rounded-full blur-[120px] pointer-events-none z-0" />
      <div className="fixed bottom-[-200px] right-[-200px] w-[600px] h-[600px] bg-base-400/30 dark:bg-base-600/20 rounded-full blur-[120px] pointer-events-none z-0" />
      
      {/* Subtle Dot Grid */}
      <div 
        className="fixed inset-0 pointer-events-none opacity-[0.3] dark:opacity-[0.15] z-0" 
        style={{ 
          backgroundImage: 'radial-gradient(circle at center, #888 1px, transparent 1px)', 
          backgroundSize: '24px 24px',
          maskImage: 'linear-gradient(to bottom, black 0%, transparent 100%)'
        }} 
      />

      <div className="relative z-10 max-w-7xl mx-auto px-4 py-8">
        {/* Hero Section - Asymmetric */}
        <motion.div
          className="flex items-start justify-between gap-12 mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="flex-1">
            <div className="flex items-center gap-4 mb-6">
              <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-base-800 to-base-950 dark:from-white dark:to-base-200 shadow-diffused transform transition-transform duration-500 hover:rotate-180 cursor-pointer">
                <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-accent">
                  {/* Upward chevron / flight path */}
                  <path d="M16 2L2 16H10L16 10L22 16H30L16 2Z" fill="currentColor"/>
                  {/* Suspended core */}
                  <path d="M10 18H22V24L16 30L10 24V18Z" fill="currentColor" opacity="0.6"/>
                  {/* Gravity point */}
                  <circle cx="16" cy="16" r="3" className="text-base-900 dark:text-white" fill="currentColor"/>
                </svg>
              </div>
              <h1 className="text-5xl font-bold tracking-tight text-base-900 dark:text-white">ResolveAI</h1>
            </div>
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-accent text-base-900 rounded-full text-sm font-semibold mb-4">
              <span className="w-2 h-2 bg-base-900 rounded-full animate-blink" />
              Frictionless Support
            </div>
            <p className="text-lg text-base-500 dark:text-base-400">Autonomous Tier-1 Customer Support Agent</p>
          </div>
          <div className="flex-none">
            <ThemeToggle />
          </div>
        </motion.div>

        {/* Main Layout */}
        <div className="grid grid-cols-[2fr_1fr] gap-8">
          {/* Left Column */}
          <div className="space-y-8">
            {/* Quick Actions */}
            <section>
              <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
              <QuickActions onAction={handleQuickAction} />
            </section>

            {/* Chat Interface */}
            <section>
              <h2 className="text-xl font-semibold mb-4">Chat</h2>
              <ChatInterface ref={chatInterfaceRef} onMessageSent={refreshMetrics} />
            </section>
          </div>

          {/* Right Column */}
          <div className="space-y-8">
            {/* Metrics Dashboard */}
            <section>
              <h2 className="text-xl font-semibold mb-4">Dashboard</h2>
              <MetricsDashboard metrics={metrics} />
            </section>

            {/* Demo Orders */}
            <section>
              <h2 className="text-xl font-semibold mb-4">Demo Orders</h2>
              <DemoOrders />
            </section>

            {/* Help Section */}
            <section>
              <button
                onClick={() => setShowHelp(!showHelp)}
                className="flex items-center justify-between w-full text-left text-lg font-semibold mb-4"
              >
                <span>Help & Tips</span>
                {showHelp ? <CaretUp size={20} /> : <CaretDown size={20} />}
              </button>
              <AnimatePresence>
                {showHelp && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3, ease: 'easeInOut' }}
                    className="overflow-hidden"
                  >
                    <div className="info-card mt-2">
                      <p className="text-sm text-base-700 dark:text-base-300 leading-relaxed">
                        <strong>How to use:</strong>
                        <br />
                        - Track orders: Enter order ID
                        <br />
                        - Refunds: Request with reason
                        <br />
                        - Address change: Provide new address
                        <br />
                        - Policies: Ask about policies
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </section>
          </div>
        </div>

        {/* Footer */}
        <motion.footer
          className="mt-16 pt-8 border-t border-base-200 text-center text-sm text-base-500"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          ResolveAI v0.1.0 — Powered by LangGraph & FastAPI
        </motion.footer>
      </div>
    </main>
  )
}
