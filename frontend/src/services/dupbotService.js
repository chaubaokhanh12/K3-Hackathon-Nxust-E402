/**
 * Lớp service — điểm nối duy nhất giữa UI và "backend".
 *
 * Hiện tại mỗi hàm chạy trên mock data (semanticSearch.js + state cục bộ).
 * Khi build app thật, chỉ cần thay THÂN HÀM bằng fetch tới API thật —
 * chữ ký (tham số vào, Promise trả ra) giữ nguyên nên App.jsx và mọi
 * component không cần sửa gì.
 *
 * Bật cờ USE_MOCK = false (hoặc set VITE_USE_MOCK=false trong .env) khi
 * đã có backend thật để chuyển sang gọi API.
 */

import { searchSimilar } from '../lib/semanticSearch.js'

export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

/**
 * Tìm thread tương tự cho một câu hỏi mới.
 * Thật: POST {API_BASE}/threads/search { query, topK } -> { confidence, matches }
 */
export async function findSimilarThreads(query, { topK = 3 } = {}) {
  if (USE_MOCK) return searchSimilar(query, { topK })

  const res = await fetch(`${API_BASE}/threads/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, topK }),
  })
  if (!res.ok) throw new Error(`findSimilarThreads failed: ${res.status}`)
  return res.json()
}

/**
 * Học viên bấm "Đã giải quyết được".
 * Thật: PATCH {API_BASE}/threads/{threadId}/status { status: 'resolved' }
 */
export async function markThreadResolved(threadId) {
  if (USE_MOCK) return { ok: true, threadId, status: 'resolved' }

  const res = await fetch(`${API_BASE}/threads/${threadId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'resolved' }),
  })
  if (!res.ok) throw new Error(`markThreadResolved failed: ${res.status}`)
  return res.json()
}

/**
 * Học viên bấm "Chưa đúng ý tôi" — tag LabCoach kèm ngữ cảnh.
 * Thật: POST {API_BASE}/threads/{threadId}/escalate { query, rejectedThreadIds, reason }
 * Backend nên tag LabCoach thật (Discord mention / webhook) và ghi vào hàng chờ.
 */
export async function escalateToLabCoach(threadId, { query, rejected, reason }) {
  if (USE_MOCK) {
    return {
      ok: true,
      threadId,
      status: 'escalated',
      queuePosition: 1,
      slaMinutes: 25,
    }
  }

  const res = await fetch(`${API_BASE}/threads/${threadId}/escalate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, rejectedThreadIds: rejected.map((t) => t.id), reason }),
  })
  if (!res.ok) throw new Error(`escalateToLabCoach failed: ${res.status}`)
  return res.json()
}

/**
 * Đăng câu hỏi mới của học viên vào kênh.
 * Thật: POST {API_BASE}/channels/{channelId}/messages { author, body }
 * Mock chỉ echo lại — App.jsx tự thêm vào state, service này là chỗ để
 * sau này ghi vào DB/Discord thật.
 */
export async function postMessage(channelId, message) {
  if (USE_MOCK) return { ok: true, id: message.id ?? crypto.randomUUID() }

  const res = await fetch(`${API_BASE}/channels/${channelId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(message),
  })
  if (!res.ok) throw new Error(`postMessage failed: ${res.status}`)
  return res.json()
}
