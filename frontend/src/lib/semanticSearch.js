/**
 * Mô phỏng semantic search cho prototype.
 *
 * Bản production sẽ thay hàm `searchSimilar` bằng một lời gọi thật:
 *   embed(query) -> vector -> vector store (pgvector / Qdrant) -> top-k cosine
 *
 * Bản demo này mô phỏng "hiểu ngữ nghĩa" bằng cách chuẩn hoá từ đồng nghĩa về
 * một khái niệm chung trước khi so khớp — nhờ vậy "quên mật khẩu" và
 * "reset password" cùng rơi vào khái niệm CREDENTIAL + RECOVER, tức là
 * bot vẫn tìm thấy dù không trùng một từ khoá nào.
 *
 * API giữ nguyên chữ ký async để khi nối embedding thật không phải sửa UI.
 */

import { THREADS } from '../data/threads.js'

/** Mỗi dòng là một khái niệm; mọi cách diễn đạt trong dòng được gộp về phần tử đầu. */
const CONCEPT_GROUPS = [
  ['credential', 'mật khẩu', 'matkhau', 'password', 'pass', 'pwd', 'mk', 'passwd'],
  ['recover', 'quên', 'forgot', 'mất', 'khôi phục', 'lấy lại', 'reset', 'đặt lại', 'recovery'],
  ['login', 'đăng nhập', 'dangnhap', 'signin', 'sign', 'log', 'truy cập', 'vào được'],
  ['account', 'tài khoản', 'taikhoan', 'account', 'acc', 'user'],
  ['lms', 'lms', 'hệ thống học', 'vlearn', 'platform', 'nền tảng'],
  ['apikey', 'api key', 'apikey', 'khoá api', 'key', 'token xác thực', 'secret'],
  ['authfail', '401', 'unauthorized', 'incorrect', 'invalid', 'sai key', 'authentication'],
  ['ratelimit', '429', 'rate limit', 'ratelimit', 'quota', 'too many requests', 'giới hạn', 'bị chặn'],
  ['retry', 'retry', 'backoff', 'thử lại', 'gọi lại'],
  ['install', 'cài', 'cài đặt', 'install', 'pip', 'setup', 'thiết lập'],
  ['buildfail', 'build', 'wheel', 'compile', 'visual c++', 'build tools'],
  ['library', 'thư viện', 'package', 'module', 'dependency', 'gói'],
  ['colab', 'colab', 'notebook', 'jupyter', 'runtime'],
  ['disconnect', 'ngắt', 'disconnect', 'mất kết nối', 'timeout', 'dừng', 'tự tắt', 'gián đoạn'],
  ['training', 'train', 'training', 'huấn luyện', 'fine-tune', 'finetune', 'epoch'],
  ['checkpoint', 'checkpoint', 'lưu tiến độ', 'save', 'lưu'],
  ['deadline', 'deadline', 'hạn', 'hạn nộp', 'thời hạn', 'due'],
  ['late', 'muộn', 'trễ', 'late', 'quá hạn', 'chậm'],
  ['submit', 'nộp', 'submit', 'nộp bài', 'submission', 'upload bài'],
  ['grading', 'điểm', 'trừ điểm', 'chấm', 'rubric', 'score', 'grade'],
  ['embedding', 'embedding', 'vector', 'vectơ', 'vector hoá', 'nhúng'],
  ['model', 'model', 'mô hình', 'llm'],
  ['vietnamese', 'tiếng việt', 'vietnamese', 'phobert', 'vi'],
  ['similarity', 'tương tự', 'giống', 'similarity', 'ngữ nghĩa', 'semantic', 'so sánh'],
  ['git', 'git', 'github', 'commit', 'branch', 'nhánh'],
  ['push', 'push', 'đẩy code', 'đẩy lên', 'upload code'],
  ['reject', 'reject', 'từ chối', 'bị chặn lại', 'non-fast-forward', 'conflict', 'xung đột'],
  ['context', 'context window', 'context', 'ngữ cảnh'],
  ['tokenlimit', 'token limit', 'maximum context', 'quá dài', 'vượt giới hạn', 'context length'],
  ['chunking', 'chunk', 'chunking', 'chia nhỏ', 'cắt tài liệu', 'split'],
  ['prompt', 'prompt', 'câu lệnh', 'input'],
  ['docker', 'docker', 'container', 'compose', 'image'],
  ['port', 'port', 'cổng', '8000', '3000', '5000'],
  ['occupied', 'đã bị chiếm', 'already in use', 'already allocated', 'trùng', 'bị giữ', 'chiếm dụng'],
  ['error', 'lỗi', 'error', 'bug', 'fail', 'failed', 'báo lỗi', 'exception', 'crash'],
  ['howto', 'làm sao', 'thế nào', 'cách', 'how', 'phải làm gì', 'hướng dẫn'],
]

const STOPWORDS = new Set([
  'là', 'và', 'của', 'cho', 'với', 'thì', 'mà', 'nhưng', 'này', 'đó', 'kia',
  'em', 'mình', 'tôi', 'bạn', 'ạ', 'ơi', 'nhé', 'nha', 'vậy', 'ah', 'à',
  'có', 'không', 'được', 'bị', 'đang', 'đã', 'sẽ', 'rồi', 'ai', 'gì', 'sao',
  'ở', 'trong', 'trên', 'từ', 'khi', 'lúc', 'một', 'các', 'những', 'anh', 'chị',
  'giúp', 'hỏi', 'cả', 'nào', 'the', 'a', 'an', 'is', 'to', 'i', 'my', 'me',
])

/** Cụm nhiều từ phải thay trước khi tách token, xếp dài trước để không cắt nhầm. */
const PHRASE_MAP = []
const WORD_MAP = new Map()

for (const [concept, ...variants] of CONCEPT_GROUPS) {
  for (const variant of variants) {
    if (variant.includes(' ')) PHRASE_MAP.push([variant, concept])
    else WORD_MAP.set(variant, concept)
  }
}
PHRASE_MAP.sort((a, b) => b[0].length - a[0].length)

function normalize(text) {
  return text
    .toLowerCase()
    .replace(/[?!.,;:()[\]{}"'`*_/\\]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

/** Chuyển câu thành tập khái niệm — bước này thay cho vector embedding. */
export function toConceptSet(text) {
  let s = normalize(text)
  const concepts = new Set()

  for (const [phrase, concept] of PHRASE_MAP) {
    if (s.includes(phrase)) {
      concepts.add(concept)
      s = s.replaceAll(phrase, ' ')
    }
  }

  for (const token of s.split(' ')) {
    if (!token || STOPWORDS.has(token) || token.length < 2) continue
    concepts.add(WORD_MAP.get(token) ?? token)
  }
  return concepts
}

/** Cosine similarity trên vector nhị phân của tập khái niệm. */
function cosine(a, b) {
  if (!a.size || !b.size) return 0
  let overlap = 0
  for (const item of a) if (b.has(item)) overlap += 1
  return overlap / Math.sqrt(a.size * b.size)
}

/** Gộp tiêu đề + các cách diễn đạt khác của thread thành một "document vector". */
function threadConcepts(thread) {
  if (!thread._concepts) {
    thread._concepts = toConceptSet([thread.title, ...thread.keywords].join(' '))
  }
  return thread._concepts
}

export const CONFIDENCE = {
  HIGH: 'high',   // đủ chắc để đề xuất trực tiếp
  LOW: 'low',     // gần đúng, phải nói rõ là chưa chắc
  NONE: 'none',   // không có gì đủ liên quan -> chuyển Labcoach ngay
}

const HIGH_THRESHOLD = 0.42 // đủ chắc để đề xuất trực tiếp
const LOW_THRESHOLD = 0.2 // dưới ngưỡng này thì coi như không tìm thấy
const RELATED_FLOOR = 0.15 // ngưỡng tuyệt đối để vào danh sách kèm theo
const RELATED_RATIO = 0.4 // và phải đạt tối thiểu 40% điểm của kết quả tốt nhất

/**
 * Tìm thread tương tự.
 * @param {string} query câu hỏi học viên vừa đăng
 * @param {{ topK?: number }} options
 * @returns {Promise<{ confidence: string, matches: Array }>}
 */
export async function searchSimilar(query, { topK = 3 } = {}) {
  await new Promise((r) => setTimeout(r, 900)) // mô phỏng độ trễ gọi embedding

  const queryConcepts = toConceptSet(query)

  const ranked = THREADS.map((thread) => {
    const score = cosine(queryConcepts, threadConcepts(thread))
    return { ...thread, score, similarity: Math.round(score * 100) }
  }).sort((a, b) => b.score - a.score)

  // Độ tin cậy chỉ tính trên kết quả tốt nhất — các thread sau chỉ là gợi ý kèm theo.
  const best = ranked[0]?.score ?? 0

  // Loại các thread quá yếu so với kết quả đầu, tránh gợi ý nhiễu cho học viên.
  const scored = ranked
    .filter((t) => t.score >= RELATED_FLOOR && t.score >= best * RELATED_RATIO)
    .slice(0, topK)

  const confidence =
    best >= HIGH_THRESHOLD ? CONFIDENCE.HIGH : best >= LOW_THRESHOLD ? CONFIDENCE.LOW : CONFIDENCE.NONE

  return { confidence, matches: confidence === CONFIDENCE.NONE ? [] : scored }
}
