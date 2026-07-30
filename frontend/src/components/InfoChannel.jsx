import { LESSON_POSTS } from '../data/lessons.js'
import { Book, Pin } from './Icons.jsx'

const ROLE_STYLE = {
  LABCOACH: 'bg-[#1f3d2b] text-[#3ba55d]',
  ADMIN: 'bg-[#4a1b0c] text-[#f0997b]',
}

function initials(name) {
  return name
    .split(' ')
    .filter((w) => !/^(labcoach|admin)$/i.test(w))
    .slice(-2)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
}

export default function InfoChannel() {
  return (
    <>
      <div className="dc-scroll min-h-0 flex-1 overflow-y-auto">
        <div className="px-4 pb-4 pt-8">
          <div className="mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-dc-input">
            <Book size={32} className="text-white" />
          </div>
          <h2 className="text-[28px] font-bold text-white">Chào mừng tới #bai-hoc</h2>
          <p className="mt-1 max-w-xl text-[15px] leading-relaxed text-dc-muted">
            Thông báo tiến độ và tài liệu mỗi buổi học. Chỉ giảng viên và Admin đăng được ở kênh này.
          </p>
        </div>

        <div className="space-y-2.5 px-4 pb-4">
          {LESSON_POSTS.map((post) => (
            <div key={post.id} className="flex gap-3 rounded-lg border border-dc-border bg-[#2b2d31] p-3.5">
              <div
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[12px] font-bold text-black/70"
                style={{ backgroundColor: post.avatarColor }}
              >
                {initials(post.author)}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[15px] font-semibold text-white">{post.author}</span>
                  <span className={`rounded px-1.5 py-px text-[10px] font-bold uppercase ${ROLE_STYLE[post.role] ?? ''}`}>
                    {post.role}
                  </span>
                  <Pin size={13} className="text-dc-muted" />
                  <span className="text-[12px] text-dc-muted">{post.time}</span>
                </div>
                <h3 className="mt-1 text-[15px] font-semibold text-dc-text">{post.title}</h3>
                <p className="mt-0.5 text-[14px] leading-relaxed text-dc-muted">{post.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="shrink-0 px-4 pb-6 pt-1">
        <div className="rounded-lg bg-dc-input px-4 py-3 text-center text-[13px] text-dc-muted">
          Chỉ giảng viên và Admin có thể đăng trong kênh này
        </div>
      </div>
    </>
  )
}
