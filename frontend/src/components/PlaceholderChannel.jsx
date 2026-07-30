import { Hash } from './Icons.jsx'

/**
 * Kênh có thật ngoài Discord của khoá nhưng nằm ngoài lát cắt prototype này.
 * Hiện rõ ranh giới non-goal thay vì giả vờ đã build — bấm vẫn không vỡ UI.
 */
export default function PlaceholderChannel({ label }) {
  return (
    <div className="flex min-h-0 flex-1 flex-col items-center justify-center px-6 text-center">
      <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-dc-input">
        <Hash size={28} className="text-dc-muted" />
      </div>
      <p className="text-[15px] font-semibold text-white">#{label} nằm ngoài lát cắt prototype này</p>
      <p className="mt-1 max-w-sm text-[13px] leading-relaxed text-dc-muted">
        Kênh này có thật trên Discord của khoá nhưng nhóm chỉ build đầy đủ DupBot cho #hoi-dap
        trong phạm vi demo. Bấm #chung, #chia-se hoặc #bai-hoc ở sidebar để xem thêm kênh có data giả.
      </p>
    </div>
  )
}
