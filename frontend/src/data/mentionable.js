import { MEMBERS } from './threads.js'
import { GENERAL_SEED } from './generalChat.js'
import { FORUM_POSTS } from './forumPosts.js'
import { LESSON_POSTS } from './lessons.js'

/**
 * Danh sách có thể @tag trong composer. Nhân vật giả trong app nằm rải rác ở
 * nhiều file data khác nhau (threads.js cho #hoi-dap, generalChat.js cho
 * #chung, forumPosts.js cho #chia-se, lessons.js cho #bai-hoc) — gộp lại đây
 * thành một roster chung, dedupe theo tên, để gõ "@" ở bất kỳ kênh nào cũng
 * tag được bất kỳ ai xuất hiện trong app.
 */
const FALLBACK_COLORS = ['#7f77dd', '#5dcaa5', '#f0997b', '#ed93b1', '#85b7eb', '#fac775', '#c0dd97', '#f4c0d1']

function collectNamedPeople() {
  const byName = new Map()
  let colorCursor = 0

  function add(name, color, role) {
    if (!name || byName.has(name)) return
    byName.set(name, {
      id: name,
      name,
      color: color ?? FALLBACK_COLORS[colorCursor++ % FALLBACK_COLORS.length],
      role,
    })
  }

  MEMBERS.online.filter((m) => !m.bot).forEach((m) => add(m.name, m.color, m.role))
  MEMBERS.offline.forEach((m) => add(m.name, m.color, m.role))
  GENERAL_SEED.forEach((m) => add(m.author, m.avatarColor))
  FORUM_POSTS.forEach((p) => {
    add(p.author, p.avatarColor)
    p.replyThread?.forEach((r) => add(r.author, r.avatarColor))
  })
  LESSON_POSTS.forEach((p) => add(p.author, p.avatarColor, p.role))

  return [...byName.values()]
}

export const MENTIONABLE = [
  { id: 'everyone', name: 'everyone', special: true, color: '#f0997b', hint: 'Thông báo toàn kênh' },
  { id: 'LabCoach', name: 'LabCoach', special: true, color: '#5dcaa5', hint: 'Tất cả LabCoach trực' },
  { id: 'Mod', name: 'Mod', special: true, color: '#f4c0d1', hint: 'Đội ngũ kiểm duyệt' },
  ...collectNamedPeople(),
]
