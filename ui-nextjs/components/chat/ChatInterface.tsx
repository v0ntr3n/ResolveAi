'use client'

import { useState, useRef, useEffect, useImperativeHandle, forwardRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { PaperPlaneRight, Spinner, Sparkle } from '@phosphor-icons/react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { sendMessage, type ChatResponse } from '@/lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatInterfaceRef {
  sendMessageToBackend: (message: string) => Promise<void>
}

interface ChatInterfaceProps {
  onMessageSent?: () => void
}

export const ChatInterface = forwardRef<ChatInterfaceRef, ChatInterfaceProps>(
  ({ onMessageSent }, ref) => {
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const sendMessageToBackend = async (message: string) => {
      if (!message.trim() || isLoading) return

      const userMessage = message.trim()
      setMessages(prev => [...prev, { role: 'user', content: userMessage }])
      setIsLoading(true)

      try {
        const response = await sendMessage(userMessage)
        setMessages(prev => [...prev, { role: 'assistant', content: response.response }])
        onMessageSent?.()
      } catch (error) {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: 'Sorry, I could not process your request. Please try again.' 
        }])
      } finally {
        setIsLoading(false)
      }
    }

    useImperativeHandle(ref, () => ({
      sendMessageToBackend
    }))

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault()
      if (!input.trim() || isLoading) return

      const message = input.trim()
      setInput('')
      await sendMessageToBackend(message)
    }

    return (
      <div className="flex flex-col h-[600px] bg-white dark:bg-base-900 rounded-2xl border border-base-200 dark:border-base-800 overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-hide">
          <AnimatePresence>
            {messages.length === 0 && !isLoading && (
              <motion.div
                className="text-center text-base-500 py-12"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <p className="text-lg mb-2">Start a conversation</p>
                <p className="text-sm">Use Quick Actions or type your question below</p>
              </motion.div>
            )}
            
            {messages.map((msg, idx) => (
              <motion.div
                key={idx}
                className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
              >
                {msg.role === 'user' ? (
                  <div className="bg-base-100 dark:bg-base-800 text-base-900 dark:text-base-50 px-5 py-3 rounded-3xl rounded-tr-sm max-w-[80%] shadow-sm dark:shadow-none">
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                ) : (
                  <div className="flex gap-4 max-w-[90%]">
                    <div className="flex-shrink-0 mt-1">
                      <Sparkle weight="fill" className="text-accent" size={24} />
                    </div>
                    <div className="prose prose-sm max-w-none prose-p:text-base-700 dark:prose-p:text-base-300 prose-p:leading-relaxed prose-headings:text-base-900 dark:prose-headings:text-base-50 prose-strong:text-base-900 dark:prose-strong:text-base-50 prose-ul:text-base-700 dark:prose-ul:text-base-300 prose-ol:text-base-700 dark:prose-ol:text-base-300 prose-li:text-base-700 dark:prose-li:text-base-300 prose-code:text-accent prose-pre:bg-base-100 dark:prose-pre:bg-base-800 text-base-700 dark:text-base-300">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                          ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>,
                          li: ({ children }) => <li className="ml-2">{children}</li>,
                          strong: ({ children }) => <strong className="font-semibold text-base-900 dark:text-base-50">{children}</strong>,
                          code: ({ className, children }) => {
                            const isInline = !className
                            return isInline ? (
                              <code className="bg-base-100 dark:bg-base-800 text-accent px-1.5 py-0.5 rounded text-sm font-mono">{children}</code>
                            ) : (
                              <code className="block bg-base-100 dark:bg-base-800 p-3 rounded-lg text-sm font-mono overflow-x-auto text-base-900 dark:text-base-100">{children}</code>
                            )
                          },
                          h1: ({ children }) => <h1 className="text-xl font-bold mb-3 mt-4 first:mt-0">{children}</h1>,
                          h2: ({ children }) => <h2 className="text-lg font-bold mb-2 mt-3 first:mt-0">{children}</h2>,
                          h3: ({ children }) => <h3 className="text-base font-bold mb-2 mt-2 first:mt-0">{children}</h3>,
                          a: ({ href, children }) => (
                            <a href={href} className="text-accent hover:underline" target="_blank" rel="noopener noreferrer">
                              {children}
                            </a>
                          ),
                          blockquote: ({ children }) => (
                            <blockquote className="border-l-4 border-accent pl-4 my-3 text-base-600 dark:text-base-400 italic">
                              {children}
                            </blockquote>
                          ),
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}
              </motion.div>
            ))}
            
            {isLoading && (
              <motion.div
                className="flex gap-1 p-4"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <div className="w-2 h-2 bg-base-400 rounded-full animate-typing" style={{ animationDelay: '0s' }} />
                <div className="w-2 h-2 bg-base-400 rounded-full animate-typing" style={{ animationDelay: '0.2s' }} />
                <div className="w-2 h-2 bg-base-400 rounded-full animate-typing" style={{ animationDelay: '0.4s' }} />
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="p-4 border-t border-base-200 dark:border-base-800">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your question..."
              className="flex-1 px-4 py-3 rounded-xl border-2 border-base-200 dark:border-base-700 bg-transparent focus:border-accent dark:focus:border-accent focus:outline-none transition-colors"
              disabled={isLoading}
            />
            <motion.button
              type="submit"
              disabled={isLoading}
              className="px-6 py-3 bg-accent text-white rounded-xl font-semibold hover:bg-accent-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {isLoading ? <Spinner className="animate-spin" size={20} /> : <PaperPlaneRight size={20} />}
            </motion.button>
          </div>
        </form>
      </div>
    )
  }
)

ChatInterface.displayName = 'ChatInterface'
