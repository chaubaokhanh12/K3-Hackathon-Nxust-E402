import { FORUM_POSTS } from '../data/forumPosts.js'
import { Reply, ArrowRight, Trophy, Plus } from './Icons.jsx'

function initials(name) {
  return name.split(' ').slice(-2).map((w) => w[0]).join('').toUpperCase()
}

function PostCard({ post, onOpen }) {
  return (
    <button
      onClick={() => onOpen(post.id)}
      className="w-full rounded-lg border border-dc-border bg-[#2b2d31] p-3.5 text-left transition-colors hover:border-dc-muted"
    >
      <div className="flex items-start gap-3">
        <div
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[12px] font-bold text-black/70"
          style={{ backgroundColor: post.avatarColor }}
        >
          {initials(post.author)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="rounded bg-dc-mention px-1.5 py-px text-[11px] font-medium text-[#c9cdfb]">
              {post.tag}
            </span>
            <span className="text-[12px] text-dc-muted">{post.time}</span>
          </div>
          <h3 className="mt-1 text-[15px] font-semibold text-white">{post.title}</h3>
          <p className="mt-1 line-clamp-2 text-[13px] leading-relaxed text-dc-muted">{post.excerpt}</p>
          <div className="mt-2 flex items-center gap-3 text-[12px] text-dc-muted">
            <span>{post.author}</span>
            <span className="flex items-center gap-1"><Reply size={13} /> {post.replies} trả lời</span>
            <span>{post.views} lượt xem</span>
          </div>
        </div>
      </div>
    </button>
  )
}

function PostDetail({ post, onBack }) {
  return (
    <div className="px-4 py-4">
      <button
        onClick={onBack}
        className="mb-4 flex items-center gap-1.5 text-[13px] text-dc-muted hover:text-dc-text"
      >
        <ArrowRight size={15} className="rotate-180" /> Quay lại #chia-se
      </button>

      <div className="rounded-lg border border-dc-border bg-[#2b2d31] p-4">
        <div className="flex items-center gap-2">
          <span className="rounded bg-dc-mention px-1.5 py-px text-[11px] font-medium text-[#c9cdfb]">{post.tag}</span>
          <span className="text-[12px] text-dc-muted">{post.time}</span>
        </div>
        <h2 className="mt-2 text-[22px] font-bold text-white">{post.title}</h2>
        <div className="mt-1 flex items-center gap-2 text-[13px] text-dc-muted">
          <div
            className="flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold text-black/70"
            style={{ backgroundColor: post.avatarColor }}
          >
            {initials(post.author)}
          </div>
          {post.author}
        </div>
        <p className="mt-3 text-[15px] leading-relaxed text-dc-text">{post.excerpt}</p>
      </div>

      {post.replyThread.length > 0 && (
        <div className="mt-4 space-y-3">
          <div className="text-[12px] font-bold uppercase tracking-wide text-dc-muted">
            {post.replyThread.length} trả lời
          </div>
          {post.replyThread.map((r, i) => (
            <div key={i} className="flex gap-3 px-1">
              <div
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-black/70"
                style={{ backgroundColor: r.avatarColor }}
              >
                {initials(r.author)}
              </div>
              <div>
                <div className="text-[14px] font-semibold text-white">{r.author}</div>
                <div className="text-[14px] leading-relaxed text-dc-text">{r.body}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function ForumChannel({ openPostId, onOpenPost }) {
  const openPost = FORUM_POSTS.find((p) => p.id === openPostId)

  return (
    <div className="dc-scroll min-h-0 flex-1 overflow-y-auto">
      {openPost ? (
        <PostDetail post={openPost} onBack={() => onOpenPost(null)} />
      ) : (
        <div className="px-4 py-4">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Trophy size={22} className="text-dc-muted" />
              <h2 className="text-[18px] font-bold text-white">Bài đăng trong #chia-se</h2>
            </div>
            <button className="flex items-center gap-1 rounded bg-dc-blurple px-3 py-1.5 text-[13px] font-medium text-white hover:bg-dc-blurpleHover">
              <Plus size={15} /> Đăng bài
            </button>
          </div>

          <div className="space-y-2.5">
            {FORUM_POSTS.map((post) => (
              <PostCard key={post.id} post={post} onOpen={onOpenPost} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
