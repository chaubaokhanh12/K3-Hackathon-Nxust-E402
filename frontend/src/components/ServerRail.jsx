const SERVERS = [
  { id: 'ai', label: 'AI', active: true, tooltip: 'AI Thực Chiến' },
  { id: 'hv', label: 'HV', tooltip: 'Cộng đồng học viên' },
  { id: 'gv', label: 'GV', tooltip: 'Phòng giảng viên' },
]

export default function ServerRail() {
  return (
    <nav
      aria-label="Danh sách server"
      className="flex w-[72px] shrink-0 flex-col items-center gap-2 bg-dc-rail py-3"
    >
      {SERVERS.map((s, i) => (
        <div key={s.id} className="group relative flex w-full justify-center">
          <span
            className={`absolute left-0 top-1/2 -translate-y-1/2 rounded-r bg-white transition-all ${
              s.active ? 'h-10 w-1' : 'h-2 w-1 opacity-0 group-hover:opacity-100'
            }`}
          />
          <button
            title={s.tooltip}
            className={`flex h-12 w-12 items-center justify-center text-[15px] font-semibold transition-all ${
              s.active
                ? 'rounded-2xl bg-dc-blurple text-white'
                : 'rounded-3xl bg-dc-sidebar text-dc-text hover:rounded-2xl hover:bg-dc-blurple hover:text-white'
            }`}
          >
            {s.label}
          </button>
          {i === 0 && <span className="pointer-events-none absolute -bottom-2 h-0.5 w-8 rounded bg-dc-border" />}
        </div>
      ))}
    </nav>
  )
}
