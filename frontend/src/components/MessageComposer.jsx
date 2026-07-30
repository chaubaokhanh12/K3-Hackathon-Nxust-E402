import { useRef, useState } from 'react'
import { PlusCircle, Gift, Emoji, ArrowRight } from './Icons.jsx'

/** Bốn câu mẫu tương ứng bốn đường đi trải nghiệm, để demo được trong 5 phút. */
const EXAMPLES = [
  {
    path: 'Khớp cao',
    text: 'Mình không đăng nhập được vào hệ thống học, quên mất pass rồi',
  },
  {
    path: 'Khớp cao',
    text: 'Gọi API liên tục bị chặn báo quota exceeded thì fix sao ạ',
  },
  {
    path: 'Chưa chắc',
    text: 'Lỗi khi lưu tiến độ train',
  },
  {
    path: 'Không thấy',
    text: 'Cho em hỏi wifi phòng lab mật khẩu là gì ạ',
  },
]

const PATH_STYLE = {
  'Khớp cao': 'text-[#3ba55d]',
  'Chưa chắc': 'text-dc-yellow',
  'Không thấy': 'text-dc-muted',
}

export default function MessageComposer({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const inputRef = useRef(null)

  function submit(text) {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  /** Bấm chip mẫu = gõ và gửi luôn, cho demo một-cú-click. */
  function sendExample(example) {
    if (disabled) return
    onSend(example)
    setValue('')
    inputRef.current?.focus()
  }

  return (
    <div className="shrink-0 px-4 pb-6 pt-1">
      <div className="flex items-center gap-3 rounded-lg bg-dc-input px-4">
        <button className="text-dc-muted hover:text-dc-text" aria-label="Thêm tệp">
          <PlusCircle size={22} />
        </button>
        <input
          ref={inputRef}
          value={value}
          disabled={disabled}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              submit(value)
            }
          }}
          placeholder="Nhắn tin tới #hoi-dap"
          className="flex-1 bg-transparent py-3 text-[15px] text-dc-text outline-none placeholder:text-dc-muted disabled:opacity-50"
        />
        <button className="text-dc-muted hover:text-dc-text" aria-label="Quà"><Gift size={22} /></button>
        <button className="text-dc-muted hover:text-dc-text" aria-label="Emoji"><Emoji size={22} /></button>
        <button
          onClick={() => submit(value)}
          disabled={disabled || !value.trim()}
          aria-label="Gửi tin nhắn"
          className="flex items-center gap-1 rounded bg-dc-blurple px-2.5 py-1.5 text-[13px] font-medium text-white transition-colors hover:bg-dc-blurpleHover disabled:cursor-not-allowed disabled:opacity-40"
        >
          Gửi <ArrowRight size={15} />
        </button>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <span className="text-[11px] text-dc-muted">Bấm để gửi ngay:</span>
        {EXAMPLES.map((ex) => (
          <button
            key={ex.text}
            onClick={() => sendExample(ex.text)}
            disabled={disabled}
            title={ex.text}
            className="flex max-w-[260px] items-center gap-1.5 rounded border border-dc-border px-2 py-0.5 text-[11px] transition-colors hover:border-dc-muted disabled:cursor-not-allowed disabled:opacity-40"
          >
            <span className={`shrink-0 font-medium ${PATH_STYLE[ex.path]}`}>{ex.path}</span>
            <span className="truncate text-dc-muted">{ex.text}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
