import { Hash, MessageCircle, Trophy, Book } from './Icons.jsx'
import { CHANNEL_GROUPS } from '../data/channels.js'
import { FORUM_POSTS } from '../data/forumPosts.js'

const ICON_BY_KEY = {
  chat: MessageCircle,
  trophy: Trophy,
  book: Book,
  hash: Hash,
}

function ChannelIcon({ iconKey, ...rest }) {
  const Icon = ICON_BY_KEY[iconKey] ?? Hash
  return <Icon {...rest} />
}

export default function ChannelSidebar({ activeChannelId, onSelectChannel, resolvedCount }) {
  return (
    <div className="flex w-60 shrink-0 flex-col bg-dc-sidebar">
      <button className="flex h-12 items-center justify-between px-4 text-[15px] font-semibold text-white shadow-[0_1px_0_rgba(0,0,0,0.2)] hover:bg-dc-hover">
        AI Thực Chiến
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      <div className="dc-scroll flex-1 overflow-y-auto px-2 pt-4">
        {CHANNEL_GROUPS.map((group) => (
          <div key={group.name} className="mb-4">
            <div className="px-2 pb-1 text-[11px] font-bold uppercase tracking-wide text-dc-muted">
              {group.name}
            </div>
            {group.channels.map((c) => {
              const active = c.id === activeChannelId
              return (
                <div key={c.id}>
                  <button
                    onClick={() => onSelectChannel(c.id)}
                    className={`group flex w-full items-center gap-1.5 rounded px-2 py-[6px] text-left text-[15px] transition-colors ${
                      active ? 'bg-dc-active text-white' : 'text-dc-muted hover:bg-dc-hover hover:text-dc-text'
                    }`}
                  >
                    <ChannelIcon iconKey={c.icon} size={18} className="shrink-0 opacity-70" />
                    <span className="truncate">{c.label}</span>
                    {c.id === 'hoi-dap' && resolvedCount > 0 ? (
                      <span className="ml-auto rounded-full bg-dc-green px-1.5 text-[11px] font-bold text-white">
                        {resolvedCount}
                      </span>
                    ) : (
                      c.badge > 0 && (
                        <span className="ml-auto shrink-0 text-[11px] font-medium text-dc-link">
                          {c.badge} Mới
                        </span>
                      )
                    )}
                  </button>

                  {c.kind === 'forum' && (
                    <div className="ml-[26px] border-l border-dc-border pl-2.5">
                      {FORUM_POSTS.slice(0, 3).map((post) => (
                        <button
                          key={post.id}
                          onClick={() => onSelectChannel(c.id, post.id)}
                          className="block w-full truncate py-[3px] text-left text-[12px] text-dc-muted hover:text-dc-text"
                          title={post.title}
                        >
                          {post.title}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        ))}

        <div className="mb-4">
          <div className="px-2 pb-1 text-[11px] font-bold uppercase tracking-wide text-dc-muted">
            Bots
          </div>
          <button
            onClick={() => onSelectChannel('hoi-dap')}
            className="flex w-full items-center gap-2 rounded px-2 py-[6px] text-left text-[15px] text-dc-muted hover:bg-dc-hover hover:text-dc-text"
          >
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-dc-green opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-dc-green" />
            </span>
            DupBot
            <span className="ml-auto rounded bg-dc-blurple px-1 text-[10px] font-bold text-white">BOT</span>
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2 bg-[#232428] px-2 py-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#ed93b1] text-[11px] font-bold text-[#4b1528]">
          PN
        </div>
        <div className="min-w-0 flex-1">
          <div className="truncate text-[13px] font-semibold text-white">Punne</div>
          <div className="truncate text-[11px] text-dc-muted">Học viên · K12</div>
        </div>
      </div>
    </div>
  )
}
