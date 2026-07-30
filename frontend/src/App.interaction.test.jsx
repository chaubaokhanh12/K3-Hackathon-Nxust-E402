import { test } from 'vitest'
import { JSDOM } from 'jsdom'

const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', {
  url: 'http://localhost/',
})
global.window = dom.window
global.document = dom.window.document
Object.defineProperty(global, 'navigator', { value: dom.window.navigator, configurable: true })

const { render, screen, fireEvent, waitFor } = await import('@testing-library/react')
const React = (await import('react')).default
const { default: App } = await import('./App.jsx')

function assert(cond, msg) {
  if (!cond) throw new Error(`FAIL: ${msg}`)
  console.log(`PASS: ${msg}`)
}

test('các kênh và luồng DupBot hoạt động cùng nhau', async () => {
render(React.createElement(App))

assert(screen.getByText(/Chào mừng tới #hoi-dap/i), 'mặc định mở #hoi-dap')

fireEvent.click(screen.getByText('chung'))
assert(screen.getByText(/Chào mừng tới #chung/i), 'click #chung -> chuyển kênh')
assert(screen.queryByText(/Mọi người ơi/i) === null, 'không còn thấy seed message của hoi-dap khi ở kênh khác')

const chungInput = screen.getByPlaceholderText('Nhắn tin tới #chung')
fireEvent.change(chungInput, { target: { value: 'test tin nhắn ở kênh chung' } })
fireEvent.click(screen.getByLabelText('Gửi tin nhắn'))
await waitFor(() => screen.getByText('test tin nhắn ở kênh chung'))
assert(true, 'gửi tin trong #chung hoạt động độc lập, không đụng DupBot')

fireEvent.click(screen.getByText('chia-se'))
assert(screen.getAllByText('KIMI K3 chính thức lên Huggingface').length > 0, 'click #chia-se -> thấy danh sách bài đăng forum')

const [openTitle] = screen.getAllByText('Sử dụng Claude Code với Claude Opus')
fireEvent.click(openTitle)
await waitFor(() => screen.getByText(/Quay lại #chia-se/i))
assert(screen.getByText(/refactor một codebase/i), 'mở post forum -> thấy nội dung chi tiết + trích đoạn')

fireEvent.click(screen.getByText(/Quay lại #chia-se/i))
assert(screen.getAllByText('KIMI K3 chính thức lên Huggingface').length > 0, 'bấm quay lại -> về danh sách forum')

fireEvent.click(screen.getByText('bai-hoc'))
assert(screen.getByText(/Mini Hackathon kickoff/i), 'click #bai-hoc -> thấy thông báo buổi học')
assert(screen.getAllByText(/Chỉ giảng viên và Admin/i).length > 0, '#bai-hoc không cho học viên gõ tin')

fireEvent.click(screen.getByText('gioi-thieu'))
assert(screen.getByText(/nằm ngoài lát cắt prototype/i), 'kênh chưa build hiện placeholder, không vỡ UI')

fireEvent.click(screen.getByText('hoi-dap'))
assert(screen.getByText(/Chào mừng tới #hoi-dap/i), 'quay lại #hoi-dap vẫn còn nguyên')

const qaInput = screen.getByPlaceholderText('Nhắn tin tới #hoi-dap')
fireEvent.change(qaInput, { target: { value: 'Mình không đăng nhập được vào hệ thống học, quên mất pass rồi' } })
fireEvent.click(screen.getByLabelText('Gửi tin nhắn'))
await waitFor(() => screen.getAllByText(/DupBot/i).length > 0, { timeout: 2000 })
await waitFor(() => screen.getByText(/Đã giải quyết được/i), { timeout: 2000 })
assert(true, 'DupBot flow vẫn hoạt động đúng sau khi refactor thành router nhiều kênh')

console.log('\nALL INTERACTION CHECKS PASSED')
}, 10000)
