'use client'

import { motion } from 'framer-motion'

interface Order {
  id: string
  status: string
  amount: number
  refund_ok?: boolean
  addr_ok?: boolean
}

export function DemoOrders() {
  const orders: Order[] = [
    { id: 'DEMO-001', status: 'delivered', amount: 45.99, refund_ok: true },
    { id: 'DEMO-002', status: 'delivered', amount: 89.50, refund_ok: true },
    { id: 'DEMO-003', status: 'pending', amount: 150.00, addr_ok: true },
    { id: 'DEMO-008', status: 'delivered', amount: 175.00, refund_ok: false },
  ]

  const statusColors: Record<string, string> = {
    delivered: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400',
    pending: 'bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400',
    shipped: 'bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400',
    processing: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-400',
  }

  return (
    <div className="space-y-3">
      {orders.map((order, idx) => (
        <motion.div
          key={order.id}
          className="order-item flex justify-between items-center p-4 bg-white dark:bg-base-900 border border-base-200 dark:border-base-800 rounded-lg cursor-pointer"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.1, duration: 0.3 }}
          whileHover={{ x: 4, borderColor: '#10b981' }}
        >
          <div>
            <span className="font-mono font-semibold">{order.id}</span>
            <span className="text-base-500 ml-2">${order.amount.toFixed(2)}</span>
          </div>
          <div className="flex gap-2 flex-wrap">
            <span className={`status-badge ${statusColors[order.status]}`}>
              {order.status}
            </span>
            {order.refund_ok && (
              <span className="status-badge bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400 animate-pulse-slow">
                Refund OK
              </span>
            )}
            {order.addr_ok && (
              <span className="status-badge bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400">
                Addr OK
              </span>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  )
}