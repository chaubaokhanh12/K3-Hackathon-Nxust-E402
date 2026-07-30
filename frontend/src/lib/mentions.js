/**
 * Định dạng lưu mention trong text: @[Tên Người] — dùng ngoặc vuông để tên có
 * khoảng trắng ("Bảo Ngọc") vẫn tách được ranh giới rõ ràng, không cần đoán.
 * Khi hiển thị, MentionText.jsx bỏ ngoặc và tô màu pill giống Discord thật.
 */

const MENTION_RE = /@\[([^\]]+)\]/g

export function mentionToken(name) {
  return `@[${name}]`
}

/** Tách text thành mảng { type: 'text' | 'mention', value }. */
export function parseMentionSegments(text) {
  const segments = []
  let lastIndex = 0
  let match

  MENTION_RE.lastIndex = 0
  while ((match = MENTION_RE.exec(text))) {
    if (match.index > lastIndex) {
      segments.push({ type: 'text', value: text.slice(lastIndex, match.index) })
    }
    segments.push({ type: 'mention', value: match[1] })
    lastIndex = MENTION_RE.lastIndex
  }
  if (lastIndex < text.length) {
    segments.push({ type: 'text', value: text.slice(lastIndex) })
  }
  return segments
}
