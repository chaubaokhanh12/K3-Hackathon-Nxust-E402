# Hiệu chỉnh ngưỡng tương đồng (đo thật, không ước lượng)

**Ngày đo:** 2026-07-31 · **Model:** `text-embedding-3-small` · **Corpus:** 71 thread / 25 topic
**Bộ đo:** 21 case trong `src/test/test_cases.json` có `results_contains_any` (biết thread đúng)
+ 4 case `tu_choi_no_source` (biết chắc corpus **không** có nguồn).

## Vì sao phải đo

`DIRECT_MATCH_THRESHOLD = 0.78` được đặt theo cảm tính trước khi có API key. Khi chạy thật:

| | |
|---|---|
| cosine của thread ĐÚNG | min 0.390 · **trung vị 0.511** · max 0.788 |
| số case có thread đúng đạt ≥ 0.78 | **1 / 21** |
| recall@1 của retrieval | 16 / 21 |
| recall@3 của retrieval | 20 / 21 |

Tức là **bản thân retrieval tốt** (thread đúng gần như luôn nằm top-3), nhưng ngưỡng 0.78
loại sạch chúng khỏi nhóm direct match. Hệ quả ở bản cũ: gần như mọi kết quả tụt xuống
"tham chiếu cùng chủ đề", bot **không bao giờ trình lời giải**, tier không bao giờ HIGH, và
hầu hết câu hỏi đều bị chuyển cho người thật. Ngưỡng 0.78 hợp với thang của các model
symmetric-similarity khác, không hợp với thang của `text-embedding-3-small` trên câu ngắn
tiếng Việt.

## Quét ngưỡng

`gold@3` = số case có thread đúng nằm trong top-3 nhóm direct · `direct/case` = số direct
match trung bình mỗi câu (nhiễu) · `no_src` = số câu vốn không có nguồn lại sinh ra direct match.

| t | gold@3 | direct/case | no_src rò | eval tổng | P0 |
|------|--------|-------------|-----------|-----------|-----|
| 0.45 | 16/21 | 3.1 | 2/4* | 51/56 | 16/19 |
| **0.50** | **13/21** | **1.2** | **1/4*** | **53/56** | **19/19** |
| 0.55 | 9/21 | 0.7 | 1/4* | 50/56 | 19/19 |
| 0.60 | 4/21 | 0.2 | 0/4 | — | — |
| 0.78 (cũ) | 1/21 | 0.0 | 0/4 | 50/56 | 19/19 |

\* Các case "rò" là TC-009 (người ngoài khoá) và TC-010 (học phí) — cả hai đã bị chặn từ
trước ở `bot.UNSUPPORTED_SOURCE_PHRASES` nên không tới được retrieval. Rò thực tế = 0.

Có thử thêm luật kết hợp `cosine ≥ t VÀ cùng topic`: chặt hơn nhưng gold@3 kém hơn ở mọi
mức t (12/21 tại 0.45), nên không dùng.

**Chốt: `DIRECT_MATCH_THRESHOLD = 0.50`** — điểm cân bằng giữa recall và nhiễu, và là mức
duy nhất đạt đồng thời eval cao nhất (53/56) và P0 đủ 19/19.

Hai ngưỡng còn lại giữ nguyên, đã kiểm lại là hợp thang:
`TOPIC_REFERENCE_PROBLEM_THRESHOLD = 0.40` (dưới trung vị gold, đủ rộng cho tham chiếu chủ đề),
`TOPIC_REFERENCE_TOPIC_THRESHOLD = 0.50` (sau khi `topic_similarity` chuyển sang quan hệ
thành viên thì giá trị chỉ còn 0.0 hoặc 1.0, ngưỡng này thành cổng nhị phân).

## `PRIMARY_TOPIC_THRESHOLD` sau khi đổi sang centroid

Đổi profile topic từ "nối chuỗi mọi thread" sang "trung bình vector từng thread" làm thang
điểm dịch nhẹ. Đo trên 21 case: confidence của topic chính nằm trong **0.396 – 0.660**,
thấp nhất là TC-030 (`mentor_duty` 0.396). Ngưỡng hiện tại `0.35` vẫn nằm dưới toàn bộ dải
nên không cắt nhầm case nào; **giữ nguyên**. Nếu sau này nâng lên 0.40 thì TC-030 sẽ rơi về
`other` — đừng nâng nếu chưa đo lại.

## Chạy lại phép đo

```bash
PYTHONPATH=src python src/test/test_cases.py          # eval đầy đủ (dùng .env)
PYTHONPATH=src python src/test/test_cases.py -v       # kèm chi tiết case đỏ
```

Embedding đã được cache ở `src/tools/.cache/embeddings.json` nên lần chạy lại không tốn thêm
tiền API. Xoá cache nếu đổi `OPENAI_EMBEDDING_MODEL` — cache khoá theo tên model nên thực ra
không cần xoá, chỉ tốn tiền embed lại.

## Bốn hướng đã thử để cứu 3 case còn đỏ — đều bị bác bỏ bằng số đo

3 case còn lại (TC-024 "về sớm không bấm nút kết thúc buổi học", TC-026 "nhóm mới thành lập
nên bắt đầu từ việc gì", TC-030 "khi nào đăng ký định hướng") có thread đúng nằm hạng 3–5 với
biên rất mỏng — ví dụ TC-024: thread đúng 0.486 so với thread sai đứng đầu 0.539.

| Hướng | Kết quả đo | Vì sao bỏ |
|---|---|---|
| **Document giàu hơn** (thêm 2 câu trả lời đã lọc nhiễu vào phần đem đi embed) | recall@3 20/21 → **21/21**, nhưng eval **53 → 51/56** ở mọi ngưỡng (đã quét 0.50–0.62) | Thêm lời giải kéo hàng loạt thread cùng lĩnh vực vượt ngưỡng → top-3 bị pha loãng. Recall cao hơn nhưng thứ hạng tệ hơn. |
| **Topic reference lấp chỗ trống** khi chưa đủ 3 direct match | eval **53 → 52/56**, P0 **19 → 18/19** | Không cứu được case nào, lại làm hỏng `phan_tang_nguon`: trộn hai mức độ liên quan khiến thứ tự "nguồn đã xác minh xếp trước" mập mờ. |
| **Hybrid dense + lexical** (α·cosine + (1−α)·điểm lexical của `bot._local_similarity`), quét α ∈ {1.0, 0.85, 0.75, 0.6} × t ∈ {0.40…0.55} | Không cấu hình nào tốt hơn dense thuần. TC-026 đỏ ở **mọi** cấu hình | Muốn bắt được TC-024/TC-030 phải hạ t xuống 0.40 → 7.1 direct match/câu và **rò cả 4/4** câu `tu_choi_no_source` thành direct match, tức phá đúng nhóm P0 chống bịa. TC-030 còn bị lexical đẩy sai hướng ("đăng ký" khớp thread mentor, trong khi "định hướng"≈"chọn track" là quan hệ thuần ngữ nghĩa). |
| **`text-embedding-3-large`** | TC-024 và TC-030 lên **hạng 1**, semantic 15 → **16/18** | Nhưng thang cosine dịch lên (no_source cao nhất 0.590 → 0.645) nên câu không có nguồn rò thành direct match: P0 **19 → 15–16/19**, tổng ≤ 51/56 ở mọi ngưỡng đã quét (0.50–0.60). Đắt hơn ~6.5× mà tổng thể kém hơn. |

Kết luận: 3 case này **không sửa được bằng chỉnh ngưỡng hay đổi cách nhúng** mà không hy sinh
bảo đảm P0 "không bịa khi không có nguồn". Muốn qua thì cần thêm tầng khác — rerank bằng
cross-encoder trên top-10, hoặc mở rộng truy vấn bằng LLM — cả hai đều là hạng mục riêng, cần
đo lại toàn bộ, và không nên nhét vào lần sửa này. Hiện tại bot xử lý 3 câu đó vẫn **đúng về
mặt an toàn**: nó trả gợi ý gần đúng kèm nhãn độ tin cậy thấp và chuyển cho người thật, chứ
không bịa.

## Kết quả sau hiệu chỉnh

| Nhóm | Trước (0.78) | Sau (0.50) |
|---|---|---|
| `tim_kiem_ngu_nghia` | 12/18 | **15/18** |
| Tổng | 50/56 | **53/56** |
| P0 | 19/19 | 19/19 |

Chế độ `local-corpus-fallback` (không có API key) không đổi: 46/56, P0 19/19.
