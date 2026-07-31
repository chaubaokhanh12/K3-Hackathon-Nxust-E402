import { test } from 'vitest'
import { JSDOM } from 'jsdom'

const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', {
  url: 'http://localhost/',
})
global.window = dom.window
global.document = dom.window.document
Object.defineProperty(global, 'navigator', { value: dom.window.navigator, configurable: true })

const { render, screen, cleanup } = await import('@testing-library/react')
const React = (await import('react')).default
const { default: GeneratedAnswer } = await import('./GeneratedAnswer.jsx')

function assert(cond, msg) {
  if (!cond) throw new Error(`FAIL: ${msg}`)
  console.log(`PASS: ${msg}`)
}

const SUGGESTIONS = [
  { thread_id: '111', rank: 1, title: 'Thread một' },
  { thread_id: '222', rank: 2, title: 'Thread hai' },
]

test('câu trả lời tổng hợp hiển thị kèm số nguồn', () => {
  render(
    React.createElement(GeneratedAnswer, {
      answer: { text: 'Xoá cache [#111] rồi login lại [#222].', model: 'gpt-4o-mini' },
      suggestions: SUGGESTIONS,
    }),
  )

  assert(screen.getByText(/DupBot tổng hợp/i), 'có nhãn cho biết đây là nội dung do bot viết')
  assert(screen.getByText(/gpt-4o-mini/), 'nói rõ model đã dùng')
  assert(screen.getByTitle('Nguồn: thread #1'), 'trích nguồn [#111] -> số thứ tự 1')
  assert(screen.getByTitle('Nguồn: thread #2'), 'trích nguồn [#222] -> số thứ tự 2')
  assert(document.body.textContent.includes('Xoá cache'), 'giữ nguyên nội dung câu trả lời')
  assert(!document.body.textContent.includes('[#111]'), 'không hiện thread id thô')
  cleanup()
})

test('không render gì khi backend không tổng hợp', () => {
  const { container } = render(
    React.createElement(GeneratedAnswer, { answer: null, suggestions: SUGGESTIONS }),
  )
  assert(container.innerHTML === '', 'generated_answer = null -> không chiếm chỗ')
  cleanup()
})

test('bỏ nhãn nguồn lạ thay vì hiện id thô', () => {
  render(
    React.createElement(GeneratedAnswer, {
      answer: { text: 'Thử xem [#999].', model: null },
      suggestions: SUGGESTIONS,
    }),
  )
  assert(document.body.textContent.includes('Thử xem'), 'vẫn hiện phần chữ')
  assert(!document.body.textContent.includes('999'), 'id không khớp thread nào thì không hiện')
  cleanup()
})
