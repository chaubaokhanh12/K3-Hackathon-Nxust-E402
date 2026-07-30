import { useRef, useState } from 'react'
import { PlusCircle, Gift, Emoji, ArrowRight } from './Icons.jsx'
import MentionSuggestions from './MentionSuggestions.jsx'
import { useMentionAutocomplete } from '../hooks/useMentionAutocomplete.js'

/** Composer dùng cho các kênh không có DupBot — chỉ echo tin nhắn vào state cục bộ. */
export default function SimpleComposer({ placeholder, onSend, disabled }) {
  const [value, setValue] = useState('')
  const inputRef = useRef(null)
  const mention = useMentionAutocomplete({ value, setValue, inputRef })

  function submit() {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  return (
    <div className="shrink-0 px-4 pb-6 pt-1">
      <div className="relative flex items-center gap-3 rounded-lg bg-dc-input px-4">
        <MentionSuggestions
          options={mention.options}
          activeIndex={mention.activeIndex}
          onSelect={mention.selectMember}
          onHover={mention.setActiveIndex}
        />
        <button className="text-dc-muted hover:text-dc-text" aria-label="Thêm tệp">
          <PlusCircle size={22} />
        </button>
        <input
          ref={inputRef}
          value={value}
          disabled={disabled}
          onChange={mention.handleChange}
          onBlur={mention.close}
          onKeyDown={(e) => {
            if (mention.handleKeyDown(e)) return
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              submit()
            }
          }}
          placeholder={placeholder}
          className="flex-1 bg-transparent py-3 text-[15px] text-dc-text outline-none placeholder:text-dc-muted disabled:opacity-50"
        />
        <button className="text-dc-muted hover:text-dc-text" aria-label="Quà"><Gift size={22} /></button>
        <button className="text-dc-muted hover:text-dc-text" aria-label="Emoji"><Emoji size={22} /></button>
        <button
          onClick={submit}
          disabled={disabled || !value.trim()}
          aria-label="Gửi tin nhắn"
          className="flex items-center gap-1 rounded bg-dc-blurple px-2.5 py-1.5 text-[13px] font-medium text-white transition-colors hover:bg-dc-blurpleHover disabled:cursor-not-allowed disabled:opacity-40"
        >
          Gửi <ArrowRight size={15} />
        </button>
      </div>
    </div>
  )
}
