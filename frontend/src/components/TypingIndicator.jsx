export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 px-4 pb-1 text-[13px] text-dc-muted">
      <span className="flex gap-1">
        {[0, 150, 300].map((delay) => (
          <span
            key={delay}
            className="h-1.5 w-1.5 animate-bounce rounded-full bg-dc-muted"
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </span>
      <span>
        <strong className="font-semibold text-dc-text">DupBot</strong> đang tìm trong lịch sử kênh…
      </span>
    </div>
  )
}
