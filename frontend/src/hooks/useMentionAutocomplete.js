import { useState } from 'react'
import { MENTIONABLE } from '../data/mentionable.js'
import { mentionToken } from '../lib/mentions.js'

/**
 * Gõ "@" trong ô nhập -> mở dropdown gợi ý thành viên, chọn -> chèn token
 * "@[Tên]" vào đúng vị trí con trỏ. Dùng chung cho MessageComposer và
 * SimpleComposer nên tách thành hook riêng thay vì lặp lại logic.
 *
 * @param {string} value giá trị hiện tại của input (controlled)
 * @param {(next: string) => void} setValue
 * @param {React.RefObject<HTMLInputElement>} inputRef
 */
export function useMentionAutocomplete({ value, setValue, inputRef }) {
  const [query, setQuery] = useState(null) // null = không active
  const [triggerIndex, setTriggerIndex] = useState(-1)
  const [activeIndex, setActiveIndex] = useState(0)

  const options =
    query === null
      ? []
      : MENTIONABLE.filter((m) => m.name.toLowerCase().includes(query.toLowerCase())).slice(0, 6)

  const active = query !== null && options.length > 0

  function detectTrigger(text, cursor) {
    const uptoCursor = text.slice(0, cursor)
    const atIndex = uptoCursor.lastIndexOf('@')
    if (atIndex === -1) {
      setQuery(null)
      return
    }
    const between = uptoCursor.slice(atIndex + 1)
    // Khoảng trắng hoặc "]" cắt đứt trigger — coi như người dùng đã gõ xong.
    if (/[\s\]]/.test(between)) {
      setQuery(null)
      return
    }
    const precedingChar = atIndex > 0 ? text[atIndex - 1] : ' '
    if (precedingChar !== ' ' && atIndex !== 0) {
      setQuery(null)
      return
    }
    setQuery(between)
    setTriggerIndex(atIndex)
    setActiveIndex(0)
  }

  function handleChange(e) {
    const val = e.target.value
    setValue(val)
    detectTrigger(val, e.target.selectionStart)
  }

  function selectMember(member) {
    if (!member || triggerIndex === -1) return
    const cursor = inputRef.current?.selectionStart ?? value.length
    const before = value.slice(0, triggerIndex)
    const after = value.slice(cursor)
    const inserted = `${mentionToken(member.name)} `
    const next = `${before}${inserted}${after}`
    setValue(next)
    setQuery(null)
    // setTimeout thay vì requestAnimationFrame — chạy được cả trong môi trường
    // test không có rAF (jsdom thuần), vẫn đủ để đợi React commit xong DOM.
    setTimeout(() => {
      const pos = before.length + inserted.length
      inputRef.current?.setSelectionRange(pos, pos)
      inputRef.current?.focus()
    }, 0)
  }

  /** Gọi trước logic onKeyDown của composer — trả true nếu đã "nuốt" phím. */
  function handleKeyDown(e) {
    if (!active) return false
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((i) => (i + 1) % options.length)
      return true
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((i) => (i - 1 + options.length) % options.length)
      return true
    }
    if (e.key === 'Enter' || e.key === 'Tab') {
      e.preventDefault()
      selectMember(options[activeIndex])
      return true
    }
    if (e.key === 'Escape') {
      e.preventDefault()
      setQuery(null)
      return true
    }
    return false
  }

  function close() {
    setQuery(null)
  }

  return { active, options, activeIndex, setActiveIndex, handleChange, handleKeyDown, selectMember, close }
}
