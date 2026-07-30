import { useEffect, useRef, useState } from 'react'
import ChannelIntro from './ChannelIntro.jsx'
import UserMessage from './UserMessage.jsx'
import BotMessage from './BotMessage.jsx'
import EscalationMessage from './EscalationMessage.jsx'
import SystemMessage from './SystemMessage.jsx'
import TypingIndicator from './TypingIndicator.jsx'
import MessageComposer from './MessageComposer.jsx'
import { SEED_MESSAGES } from '../data/threads.js'
import { CONFIDENCE } from '../lib/semanticSearch.js'
import { findSimilarThreads, markThreadResolved, escalateToLabCoach, postMessage } from '../services/dupbotService.js'

const CHANNEL_ID = 'hoi-dap'
const CURRENT_USER = { name: 'Punne', avatarColor: '#ed93b1' }

let seq = 0
const nextId = () => `msg-${++seq}`

function nowLabel() {
  return `Hôm nay lúc ${new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}`
}

/** Toàn bộ luồng DupBot: đăng câu hỏi -> tìm thread tương tự -> resolve hoặc escalate. */
export default function HoiDapChannel({ onResolvedCountChange, onThreadResolvedChange }) {
  const [messages, setMessages] = useState(SEED_MESSAGES)
  const [thinking, setThinking] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages, thinking])

  async function handleSend(text) {
    const userMsg = {
      id: nextId(),
      kind: 'user',
      author: CURRENT_USER.name,
      avatarColor: CURRENT_USER.avatarColor,
      time: nowLabel(),
      body: text,
    }
    setMessages((prev) => [...prev, userMsg])
    postMessage(CHANNEL_ID, userMsg).catch(() => {})

    setThinking(true)
    let result
    try {
      result = await findSimilarThreads(text, { topK: 3 })
    } catch (err) {
      setThinking(false)
      setMessages((prev) => [
        ...prev,
        { id: nextId(), kind: 'system', variant: 'tag', body: `DupBot gặp lỗi khi tìm kiếm: ${err.message}` },
      ])
      return
    }
    setThinking(false)

    const botId = nextId()
    setMessages((prev) => [
      ...prev,
      {
        id: botId,
        kind: 'bot',
        query: text,
        result,
        status: result.confidence === CONFIDENCE.NONE ? 'escalated' : 'pending',
      },
    ])

    if (result.confidence === CONFIDENCE.NONE) {
      escalate(botId, text, [], 'Không có thread nào vượt ngưỡng tương đồng 20%.')
    }
  }

  async function handleResolve(botId) {
    await markThreadResolved(botId)
    setMessages((prev) => prev.map((m) => (m.id === botId ? { ...m, status: 'resolved' } : m)))
    setMessages((prev) => [
      ...prev,
      {
        id: nextId(),
        kind: 'system',
        variant: 'resolved',
        body: 'DupBot đã gắn nhãn “Đã xử lý” cho thread này và bỏ khỏi hàng chờ của LabCoach.',
      },
    ])
    onThreadResolvedChange(true)
    onResolvedCountChange((c) => c + 1)
  }

  async function handleEscalate(botId, query, matches) {
    setMessages((prev) => prev.map((m) => (m.id === botId ? { ...m, status: 'escalated' } : m)))
    await escalate(botId, query, matches, 'Học viên đã đọc các thread trên và xác nhận không đúng vấn đề của mình.')
  }

  async function escalate(botId, query, rejected, reason) {
    const res = await escalateToLabCoach(botId, { query, rejected, reason })
    setMessages((prev) => [
      ...prev,
      { id: nextId(), kind: 'escalation', query, rejected, reason },
      {
        id: nextId(),
        kind: 'system',
        variant: 'tag',
        body: `Thread được gắn nhãn "Chờ LabCoach" (vị trí #${res.queuePosition} trong hàng chờ).`,
      },
    ])
    onThreadResolvedChange(false)
  }

  return (
    <>
      <div ref={scrollRef} className="dc-scroll min-h-0 flex-1 overflow-y-auto">
        <ChannelIntro />

        {messages.map((m) => {
          if (m.kind === 'user') return <UserMessage key={m.id} {...m} />
          if (m.kind === 'system')
            return (
              <SystemMessage key={m.id} variant={m.variant}>
                {m.body}
              </SystemMessage>
            )
          if (m.kind === 'escalation')
            return <EscalationMessage key={m.id} query={m.query} rejected={m.rejected} reason={m.reason} />
          return (
            <BotMessage
              key={m.id}
              result={m.result}
              status={m.status}
              onResolve={() => handleResolve(m.id)}
              onEscalate={() => handleEscalate(m.id, m.query, m.result.matches)}
            />
          )
        })}

        {thinking && <TypingIndicator />}
        <div className="h-4" />
      </div>

      <MessageComposer onSend={handleSend} disabled={thinking} />
    </>
  )
}
