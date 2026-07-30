import { useEffect, useRef, useState } from 'react'
import UserMessage from './UserMessage.jsx'
import SimpleComposer from './SimpleComposer.jsx'
import { GENERAL_SEED } from '../data/generalChat.js'
import { MessageCircle } from './Icons.jsx'

const CURRENT_USER = { name: 'Punne', avatarColor: '#ed93b1' }

let seq = 0
const nextId = () => `chung-${++seq}`

/** Kênh chat thường — không có bot, chỉ để chứng minh sidebar điều hướng được nhiều kênh. */
export default function GeneralChannel() {
  const [messages, setMessages] = useState(GENERAL_SEED.map((m) => ({ id: nextId(), ...m })))
  const scrollRef = useRef(null)

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages])

  function handleSend(text) {
    setMessages((prev) => [
      ...prev,
      {
        id: nextId(),
        author: CURRENT_USER.name,
        avatarColor: CURRENT_USER.avatarColor,
        time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
        body: text,
      },
    ])
  }

  return (
    <>
      <div ref={scrollRef} className="dc-scroll min-h-0 flex-1 overflow-y-auto">
        <div className="px-4 pb-4 pt-8">
          <div className="mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-dc-input">
            <MessageCircle size={32} className="text-white" />
          </div>
          <h2 className="text-[28px] font-bold text-white">Chào mừng tới #chung</h2>
          <p className="mt-1 max-w-xl text-[15px] leading-relaxed text-dc-muted">
            Kênh trò chuyện tự do của cả khoá, không liên quan trực tiếp tới bài học.
          </p>
        </div>

        {messages.map((m) => (
          <UserMessage key={m.id} {...m} />
        ))}
        <div className="h-4" />
      </div>

      <SimpleComposer placeholder="Nhắn tin tới #chung" onSend={handleSend} />
    </>
  )
}
