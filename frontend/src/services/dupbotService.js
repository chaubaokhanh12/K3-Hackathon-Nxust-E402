/**
 * Lớp service — điểm nối duy nhất giữa UI và "backend".
 *
 * Hiện tại mỗi hàm chạy trên mock data (semanticSearch.js + state cục bộ).
 * Khi build app thật, chỉ cần thay THÂN HÀM bằng fetch tới API thật —
 * chữ ký (tham số vào, Promise trả ra) giữ nguyên nên App.jsx và mọi
 * component không cần sửa gì.
 *
 * Backend thật là mặc định. Test có thể dùng mock bằng VITE_USE_MOCK=true.
 */

import { searchSimilar } from '../lib/semanticSearch.js'

const mockSetting = import.meta.env.VITE_USE_MOCK
export const USE_MOCK = mockSetting === 'true' || (!mockSetting && import.meta.env.MODE === 'test')
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

const COPY = {
  high: {
    headline: 'Mình tìm thấy câu hỏi tương tự đã có lời giải',
    note: 'Đọc trước các thread này, phần lớn trường hợp là cùng một nguyên nhân.',
  },
  low: {
    headline: 'Mình chỉ tìm được kết quả gần đúng',
    note: 'Độ khớp không cao nên đây chỉ là tài liệu tham khảo cùng chủ đề.',
  },
  none: {
    headline: 'Chưa có thread nào tương tự trong lịch sử kênh',
    note: 'Đây là câu hỏi mới. Mình đã chuyển trực tiếp cho LabCoach, bạn không cần làm gì thêm.',
  },
}

function normalizeMockResult(result) {
  const suggestions = result.matches.map((thread, index) => ({
    thread_id: thread.id,
    rank: index + 1,
    title: thread.title,
    similarity: thread.similarity,
    relevance: 'direct',
    excerpt: thread.excerpt,
    thread_url: thread.url,
    source_tier: 'VERIFIED',
    author_name: thread.answeredBy,
    author_role: 'LabCoach',
    replies: thread.replies,
    answered_at: thread.answeredAt,
  }))
  const renderButtons = result.confidence !== 'none'
  return {
    ...result,
    ...COPY[result.confidence],
    suggestions,
    render_buttons: renderButtons,
    buttons: renderButtons ? [{ id: 'resolve' }, { id: 'escalate' }] : [],
    escalated_to_labcoach: result.confidence === 'none',
    retrieval_mode: 'browser-mock',
  }
}

async function readJson(res, operation) {
  const body = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = body?.detail ? `: ${body.detail}` : ''
    throw new Error(`${operation} thất bại (${res.status})${detail}`)
  }
  return body
}

/**
 * Tìm thread tương tự cho một câu hỏi mới.
 * Thật: POST {API_BASE}/threads/search -> guardrail-safe BotResponse.
 */
export async function findSimilarThreads(query, { topK = 3 } = {}) {
  if (USE_MOCK) return normalizeMockResult(await searchSimilar(query, { topK }))

  const res = await fetch(`${API_BASE}/threads/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, topK }),
  })
  return readJson(res, 'Tìm thread tương tự')
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
  return readJson(res, 'Đánh dấu đã giải quyết')
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
    body: JSON.stringify({
      query,
      rejectedThreadIds: rejected.map((t) => t.thread_id ?? t.id),
      reason,
    }),
  })
  return readJson(res, 'Chuyển LabCoach')
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
  return readJson(res, 'Đăng câu hỏi')
}
