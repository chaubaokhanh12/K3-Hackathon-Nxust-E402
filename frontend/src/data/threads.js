/**
 * Kho thread #hoi-dap đã có lời giải.
 * Đây là dữ liệu giả mô phỏng lịch sử kênh hỏi đáp — không phải data thật của học viên.
 *
 * Mỗi thread có:
 *  - title:      câu hỏi gốc học viên đặt
 *  - excerpt:    trích đoạn câu trả lời được chấp nhận (bot hiển thị luôn, không chỉ đưa link)
 *  - answeredBy: người trả lời
 *  - keywords:   các cách diễn đạt khác của cùng vấn đề, dùng để mô phỏng vector embedding
 */

export const THREADS = [
  {
    id: 'T-1042',
    title: 'Mình quên mật khẩu đăng nhập LMS, phải làm sao để khôi phục?',
    author: 'Bảo Ngọc',
    answeredBy: 'LabCoach Minh',
    answeredAt: '2 ngày trước',
    replies: 4,
    reactions: 7,
    url: 'https://discord.com/channels/000/hoi-dap/1042',
    excerpt:
      'Vào Account Settings → Security → Forgot password, nhập email đã đăng ký khoá. Link reset có hiệu lực 15 phút. Nếu không thấy mail thì kiểm tra tab Spam, hoặc ping mình kèm email để mình reset tay.',
    keywords: [
      'quên mật khẩu',
      'reset password',
      'đổi pass',
      'không đăng nhập được lms',
      'khôi phục tài khoản',
      'lấy lại mật khẩu',
    ],
  },
  {
    id: 'T-0987',
    title: 'API key OpenAI của em báo lỗi 401 Incorrect API key provided',
    author: 'Trung Kiên',
    answeredBy: 'LabCoach Duy',
    answeredAt: '5 ngày trước',
    replies: 9,
    reactions: 14,
    url: 'https://discord.com/channels/000/hoi-dap/987',
    excerpt:
      '401 gần như luôn là key sai chỗ chứ không phải key hỏng. Ba nguyên nhân thường gặp: (1) copy thiếu ký tự đầu sk-, (2) để key trong .env nhưng quên load_dotenv(), (3) biến môi trường tên OPENAI_KEY thay vì OPENAI_API_KEY. In ra os.getenv("OPENAI_API_KEY")[:8] để kiểm tra key có tới được code không.',
    keywords: [
      'api key lỗi',
      'invalid api key',
      '401 unauthorized',
      'key không hoạt động',
      'authentication failed',
      'openai key sai',
    ],
  },
  {
    id: 'T-1101',
    title: 'Gọi API nhiều bị 429 Too Many Requests, xử lý thế nào ạ?',
    author: 'Hải Yến',
    answeredBy: 'LabCoach Duy',
    answeredAt: '1 ngày trước',
    replies: 6,
    reactions: 11,
    url: 'https://discord.com/channels/000/hoi-dap/1101',
    excerpt:
      '429 là rate limit, không phải bug code. Cách xử lý chuẩn là exponential backoff: retry sau 1s, 2s, 4s, 8s và có jitter. Thư viện tenacity làm sẵn việc này. Nếu bạn đang loop qua 1.000 dòng data thì thêm asyncio.Semaphore(5) để giới hạn số request đồng thời.',
    keywords: [
      'rate limit',
      '429 too many requests',
      'bị chặn khi gọi api',
      'quota exceeded',
      'gọi api quá nhiều',
      'retry backoff',
    ],
  },
  {
    id: 'T-0899',
    title: 'pip install sentence-transformers lỗi Microsoft Visual C++ 14.0 required',
    author: 'Quốc Anh',
    answeredBy: 'LabCoach Minh',
    answeredAt: '1 tuần trước',
    replies: 12,
    reactions: 19,
    url: 'https://discord.com/channels/000/hoi-dap/899',
    excerpt:
      'Lỗi này là do pip đang build package từ source trên Windows. Hai cách: (1) cài Microsoft C++ Build Tools rồi mở lại terminal, (2) nhanh hơn — dùng wheel có sẵn: pip install --only-binary :all: sentence-transformers. Khuyến nghị tạo venv riêng cho khoá để không đụng vào Python hệ thống.',
    keywords: [
      'pip install lỗi',
      'không cài được package',
      'build wheel failed',
      'visual c++ required',
      'lỗi cài thư viện',
      'setup môi trường windows',
    ],
  },
  {
    id: 'T-1055',
    title: 'Colab tự ngắt kết nối giữa lúc đang train, mất hết checkpoint',
    author: 'Thanh Hà',
    answeredBy: 'LabCoach Trang',
    answeredAt: '3 ngày trước',
    replies: 7,
    reactions: 9,
    url: 'https://discord.com/channels/000/hoi-dap/1055',
    excerpt:
      'Colab free ngắt sau ~90 phút không tương tác và tối đa 12 giờ mỗi session. Việc cần làm trước tiên là mount Google Drive rồi save checkpoint mỗi epoch vào Drive, không lưu trong /content. Sau đó viết code resume từ checkpoint mới nhất để chạy lại không mất tiến độ.',
    keywords: [
      'colab disconnect',
      'mất phiên colab',
      'runtime bị ngắt',
      'train giữa đường bị dừng',
      'mất checkpoint',
      'colab timeout',
    ],
  },
  {
    id: 'T-0964',
    title: 'Nộp bài checkpoint muộn 30 phút thì có bị trừ điểm không ạ?',
    author: 'Minh Tuấn',
    answeredBy: 'Admin Phương',
    answeredAt: '6 ngày trước',
    replies: 3,
    reactions: 22,
    url: 'https://discord.com/channels/000/hoi-dap/964',
    excerpt:
      'Theo rubric mục Phần 1: nộp đúng hạn được 5 điểm, nộp muộn được 0 điểm cho mốc đó — không có trừ theo phút. Deadline lấy theo timestamp trên form nộp, không lấy theo giờ commit. Nếu gặp sự cố kỹ thuật lúc nộp thì chụp màn hình lỗi và ping Admin trước giờ deadline.',
    keywords: [
      'nộp muộn',
      'trễ deadline',
      'quá hạn nộp bài',
      'trừ điểm nộp trễ',
      'late submission',
      'chính sách deadline',
    ],
  },
  {
    id: 'T-1078',
    title: 'Dùng embedding model nào cho tiếng Việt thì tốt ạ?',
    author: 'Phương Linh',
    answeredBy: 'LabCoach Duy',
    answeredAt: '2 ngày trước',
    replies: 15,
    reactions: 27,
    url: 'https://discord.com/channels/000/hoi-dap/1078',
    excerpt:
      'Ba lựa chọn theo thứ tự dễ dùng: (1) OpenAI text-embedding-3-small — rẻ, đa ngôn ngữ, không cần GPU; (2) multilingual-e5-base — chạy local, chất lượng tiếng Việt tốt, nhớ thêm prefix "query: " và "passage: "; (3) PhoBERT — mạnh nhất cho tiếng Việt nhưng phải tự fine-tune cho bài toán similarity.',
    keywords: [
      'embedding tiếng việt',
      'model vector hoá',
      'chọn model embedding',
      'phobert',
      'multilingual embedding',
      'so sánh ngữ nghĩa',
    ],
  },
  {
    id: 'T-0921',
    title: 'Git push bị reject rejected non-fast-forward, em phải làm gì?',
    author: 'Đức Huy',
    answeredBy: 'LabCoach Minh',
    answeredAt: '1 tuần trước',
    replies: 5,
    reactions: 8,
    url: 'https://discord.com/channels/000/hoi-dap/921',
    excerpt:
      'Nghĩa là remote có commit mà local bạn chưa có. Chạy git pull --rebase origin main để xếp commit của bạn lên trên, xử lý conflict nếu có rồi push lại. Tuyệt đối không dùng git push --force trên nhánh chung của nhóm vì sẽ ghi đè commit của người khác.',
    keywords: [
      'git push lỗi',
      'non fast forward',
      'push bị từ chối',
      'conflict khi push',
      'git pull rebase',
      'đẩy code lên github lỗi',
    ],
  },
  {
    id: 'T-1120',
    title: 'Prompt của em vượt context window, báo lỗi maximum context length',
    author: 'Gia Bảo',
    answeredBy: 'LabCoach Trang',
    answeredAt: '20 giờ trước',
    replies: 4,
    reactions: 6,
    url: 'https://discord.com/channels/000/hoi-dap/1120',
    excerpt:
      'Đừng nhồi cả tài liệu vào prompt. Chia document thành chunk 500-800 token có overlap 50 token, embed từng chunk, rồi chỉ đưa top-k chunk liên quan nhất vào prompt. Dùng tiktoken để đếm token trước khi gọi API thay vì đoán theo số ký tự.',
    keywords: [
      'vượt context window',
      'token limit',
      'prompt quá dài',
      'maximum context length exceeded',
      'chia nhỏ tài liệu',
      'chunking document',
    ],
  },
  {
    id: 'T-1003',
    title: 'Docker chạy báo port 8000 is already allocated',
    author: 'Khánh Vy',
    answeredBy: 'LabCoach Minh',
    answeredAt: '4 ngày trước',
    replies: 3,
    reactions: 5,
    url: 'https://discord.com/channels/000/hoi-dap/1003',
    excerpt:
      'Có container cũ vẫn đang giữ port. Chạy docker ps để xem rồi docker stop <id>, hoặc docker compose down để dọn cả stack. Nếu tiến trình không phải Docker thì trên Windows dùng netstat -ano | findstr :8000 để tìm PID. Cách nhanh nhất là map sang port khác: -p 8001:8000.',
    keywords: [
      'port đã bị chiếm',
      'address already in use',
      'docker lỗi port',
      'container không start được',
      'port bị trùng',
    ],
  },
]

/** Thread đang mở sẵn trong kênh khi vào demo. */
export const SEED_MESSAGES = [
  {
    id: 'm1',
    kind: 'user',
    author: 'Thanh Hà',
    avatarColor: '#f0997b',
    time: 'Hôm qua lúc 21:04',
    body: 'Mọi người ơi, Colab của mình cứ tự ngắt giữa lúc train, có ai bị vậy chưa?',
  },
  {
    id: 'm2',
    kind: 'user',
    author: 'LabCoach Trang',
    avatarColor: '#5dcaa5',
    role: 'LABCOACH',
    time: 'Hôm qua lúc 21:11',
    body: 'Mình vừa trả lời chi tiết trong thread T-1055 nhé, bạn xem phần mount Drive để save checkpoint.',
  },
]

/** Danh sách member hiển thị ở cột phải. */
export const MEMBERS = {
  online: [
    { name: 'DupBot', color: '#5865f2', bot: true, status: 'Đang lắng nghe #hoi-dap' },
    { name: 'LabCoach Minh', color: '#5dcaa5', role: 'LABCOACH' },
    { name: 'LabCoach Duy', color: '#85b7eb', role: 'LABCOACH' },
    { name: 'Admin Phương', color: '#f4c0d1', role: 'ADMIN' },
    { name: 'Bảo Ngọc', color: '#85b7eb' },
    { name: 'Thanh Hà', color: '#f0997b' },
  ],
  offline: [
    { name: 'LabCoach Trang', color: '#c0dd97', role: 'LABCOACH' },
    { name: 'Trung Kiên', color: '#fac775' },
    { name: 'Phương Linh', color: '#ed93b1' },
  ],
}
