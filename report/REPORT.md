# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
|Nguyễn Minh Hiếu|2A202602669|Bài Lab|
| | | |

- Mô hình (tên deployment hoặc `LAB_MODEL`), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `gpt-6-luna` qua API OpenAI (`AZURE_OPENAI_ENDPOINT=https://api.openai.com/v1`, nhánh `ChatOpenAI` trong `model.py`); `LAB_TEMPERATURE=1` vì mô hình từ chối mọi giá trị khác ("'temperature' does not support 0.0 with this model. Only the default (1) value is supported"); `recursion_limit=60` (mặc định của runner).
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `deepagents` 0.7.21; chạy trong Docker (image `python:3.12-slim`, Python 3.12.15) trên Windows 11 Home (10.0.26200).
- Số lần chạy tác vụ đã dùng / ngân sách:
- Commit của tag `freeze`:

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

Các giả thuyết dưới đây được viết khi mới chỉ có kết quả trên tác vụ học (mục 4, 5, 6); chưa có lần chạy nào trên tác vụ đánh giá và chưa mở `check.py` của tác vụ đánh giá.

- H1 (subagents so với baseline): trên tác vụ đánh giá, `subagents` đạt điểm trung bình ngang `baseline` (chênh không quá 1 check mỗi tác vụ) nhưng tốn ít nhất gấp 3 lần token. Căn cứ: trên tác vụ học hai điều kiện có điểm giống hệt (18/27 check) với cùng 9 check `rule_` thất bại, trong khi token gấp 5,7 lần (mục 5). Lỗi thuộc nhóm E là do thiếu thông tin về quy ước, và giao việc cho subagent không tạo ra thông tin mới. Chi phí cao của đa tác tử khớp với ghi nhận của Anthropic về hệ thống nghiên cứu đa tác tử (khoảng 15 lần token so với hội thoại thường).
- H2 (skills-auto so với baseline): `skills-auto` đạt điểm cao nhất trong ba điều kiện trên tác vụ đánh giá, và toàn bộ phần tăng nằm ở check quy ước `rule_`; check kỹ thuật không đổi vì `baseline` đã đạt 18/18 trên tác vụ học. Mức tăng dự đoán là 1 đến 2 check mỗi tác vụ, chỉ ở những quy ước mà skill phát biểu nguyên văn; các quy tắc skill viết mơ hồ (tên khóa của `meta`, tiêu đề cột `clean.csv`, giá trị `schema_version` và `generated_by`) sẽ không giúp được. Token dự đoán gấp 1,5 đến 2,5 lần `baseline`. Căn cứ: ở Phần 3.4, cùng bộ skill này nâng điểm tác vụ học từ 18/27 lên 24/27 và 3 check còn trượt đúng là 3 chỗ skill mơ hồ (mục 6). SkillsBench ghi nhận skill do mô hình tự sinh trung bình không có lợi; chúng tôi dự đoán kết quả khác ở đây vì phản hồi `detail` của bot đã phát biểu nguyên văn quy tắc, curator chỉ cần chép lại.
- H3 (tác vụ học so với tác vụ đánh giá): mức tăng của `skills-auto` so với `baseline` trên tác vụ đánh giá nhỏ hơn trên tác vụ học (ở tác vụ học là +6 check, từ 18/27 lên 24/27). Mỗi tác vụ đánh giá có thêm một quy ước mới mà skill không thể chứa, nên ít nhất 1 check `rule_` mỗi tác vụ đánh giá vẫn trượt ở cả ba điều kiện. Căn cứ: skill chỉ được rút ra từ phản hồi của tác vụ học; SkillEvolBench ghi nhận lợi ích trên tác vụ học thường không chuyển hết sang tác vụ mới (quá khớp).

## 3. Làm quen Deep Agents (Phần 0.3)

Nguồn: đầu ra của `python scripts/tour.py` (mô hình giả, không tốn token).

1. Tác tử mặc định có 9 công cụ. Công cụ tệp: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`. Công cụ shell: `execute`. Công cụ giao việc cho subagent: `task`. Chỉ `execute` cho phép chạy lệnh; mô tả của nó ghi rõ công cụ này chỉ dùng được trên backend cài đặt `SandboxBackendProtocol`, nếu không sẽ trả về lỗi.
2. Mô tả của `task` giới thiệu `general-purpose` là tác tử đa dụng để nghiên cứu câu hỏi phức tạp, tìm tệp và nội dung, và thực hiện tác vụ nhiều bước; nó có cùng bộ công cụ với tác tử chính ("This agent has access to all tools as the main agent"). Subagent này không nhìn thấy hội thoại của tác tử chính: mỗi lần gọi là phi trạng thái, nó chỉ thấy lời nhắc được giao và trả về một báo cáo cuối duy nhất ("the agent sees only the prompt you give it and returns a single final report"). Vì vậy mọi quy tắc của đề phải được chép vào lời giao việc, nếu không subagent sẽ không biết.
3. System prompt mặc định là chuỗi rỗng (`''`), nên hướng dẫn hành vi nằm trong mô tả công cụ:
   - Từ `task`: "Put full detail in the prompt and state exactly what it should return".
   - Từ `execute`: "You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search."

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

Nguồn: `results/baseline/{code,data,logs}-learn/run.json` và `trace.md` (mô hình `gpt-6-luna`). Tổng cộng 9 check thất bại trên 27 check (điểm 7/10, 5/8, 6/9); không lần chạy nào có `error`.

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| code-learn | `rule_type_hints` | E | "RULE: every public function (name not starting with '_') in the package has type annotations on all parameters and on the return value." |
| code-learn | `rule_regression_tests` | E | "RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3); the file must pass." Vết: tác tử tự kiểm bằng script `python - <<'PY'` tạm thời, không ghi tệp test nào. |
| code-learn | `rule_changelog` | E | "RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' as a bullet '- fix(<function name>): <short description>'". Vết: tác tử có đọc `workspace/CHANGELOG.md` nhưng không sửa. |
| data-learn | `rule_money_in_cents` | E | "RULE: money values in answer.json are integer cents (1606.67 USD is written 160667)." Tác tử ghi `"north_q1_revenue": 3130.24`. |
| data-learn | `rule_meta_block` | E | "RULE: answer.json has an object `meta` = {"source": ..., "rows_in": ..., "rows_used": ...}". `answer.json` chỉ có 5 khóa đề yêu cầu. |
| data-learn | `rule_clean_csv` | E | "RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents". Vết chỉ có một lệnh `write_file`, cho `answer.json`. |
| logs-learn | `rule_service_names` | E | "RULE: service names in the output are lower-case with '-' replaced by '_' (payment-service -> payment_service)." |
| logs-learn | `rule_sorted_errors` | E | "RULE: `errors` is sorted by service, then by timestamp_utc, ascending." |
| logs-learn | `rule_schema_header` | E | "RULE: the top-level object has "schema_version": 2 and "generated_by": "log-triage"." |

Nhận xét:

- **Nhóm E chiếm toàn bộ: 9/9 check thất bại**, và đó cũng là toàn bộ 9 check quy ước (0/9 đạt). Cả ba đề đều nhắc rằng kết quả được "Acme's review bot" kiểm tra theo quy ước của Acme, nhưng không tệp nào trong workspace ghi các quy ước đó. Tác tử đã đọc README ở cả ba tác vụ mà vẫn không thể biết, nên đây là thiếu thông tin chứ không phải thiếu cẩn thận.
- **Bằng chứng phủ định cho nhóm A đến D**: `scripts/check_breakdown.py` báo check kỹ thuật đạt 18/18.
  - Nhóm A: vết cho thấy tác tử đọc `workspace/README.md` ở cả ba tác vụ trước khi sửa hoặc tính, và đọc đủ ba tệp nguồn có docstring ở `code-learn`; `low_stock_follows_docstring` và `csv_quoting_follows_docstring` (lỗi chỉ thấy khi đối chiếu docstring) đều đạt.
  - Nhóm B: `code-learn` chạy `cd workspace && python -m pytest tests -q` sau khi sửa rồi chạy thêm script khẳng định; `logs-learn` đọc lại `errors.json` sau khi ghi.
  - Nhóm C: `parse_price_all_formats` và `other_caller_fixed` đều đạt, tức lỗi được sửa ở hàm dùng chung `parse_price` chứ không vá ở nơi gọi.
  - Nhóm D: `data-learn` đạt 5/5 check kỹ thuật (dòng trùng, giá trị `-999`, ba định dạng ngày, múi giờ) và `logs-learn` đạt 6/6 (stack trace nhiều dòng, dòng lặp, múi giờ).
  - Nhóm F: `final_message` của cả ba lần chạy chỉ nhắc các tệp có thật (`answer.json`, `errors.json`, ba tệp trong `inventory/`).
- **Skill có thể phòng ngừa nhóm E**: mỗi quy ước là một quy tắc ngắn, ổn định, và `detail` của check đã nêu nguyên văn, nên curator có đủ nguyên liệu để viết thành skill. Giới hạn dự kiến: skill chỉ chứa quy ước đã gặp ở tác vụ học, nên không thể giúp ở quy ước mới của tác vụ đánh giá.

## 5. Điều kiện `subagents` (Phần 2.3)

Nguồn: `results/subagents/{code,data,logs}-learn/run.json` và `trace.md`, so với `results/baseline/` của cùng tác vụ.

- Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế): ba subagent theo chuỗi đọc, làm, kiểm, tương ứng với các nhóm lỗi A, C và B trong bảng phân loại.
  - `explorer`: chỉ đọc README, CHANGELOG, docstring, mẫu dữ liệu và báo cáo sự thật kèm trích dẫn; không sửa tệp. Nhằm vào nhóm A (bỏ qua đặc tả) và D (bỏ sót dữ liệu bẩn).
  - `implementer`: thực hiện thay đổi đã được mô tả rõ, sửa ở nguyên nhân gốc, chạy lại test hoặc script và báo cáo tệp thật sự đã đổi. Nhằm vào nhóm C và F.
  - `reviewer`: kiểm tra độc lập sau khi làm xong, đối chiếu từng yêu cầu, không sửa tệp. Nhằm vào nhóm B (không kiểm chứng).
- `subagent_calls` ở từng tác vụ và nhận xét (kể cả trường hợp bằng 0): tác tử chính giao việc ở cả ba tác vụ, tổng cộng 12 lần.

  | Tác vụ | `subagent_calls` | Chuỗi gọi | Điểm (baseline) |
  |---|---|---|---|
  | code-learn | 7 | explorer, rồi 3 vòng implementer và reviewer | 7/10 (7/10) |
  | data-learn | 3 | explorer, implementer, reviewer | 5/8 (5/8) |
  | logs-learn | 2 | implementer, implementer | 6/9 (6/9) |

  Điểm không đổi ở cả ba tác vụ và các check thất bại trùng hoàn toàn với baseline: 9 check quy ước `rule_`. Check kỹ thuật đạt 18/18 ở cả hai điều kiện, nên đa tác tử không còn gì để cải thiện ở phần kỹ thuật, và cũng không cung cấp thông tin mới về quy ước Acme.
- Thông tin thiếu hoặc thừa khi giao việc (nếu có giao việc):
  - **Đủ về kỹ thuật**: lời giao việc chép lại quy tắc của đề và đường dẫn tương đối, ví dụ ở `code-learn`: "do not modify any files in workspace/tests/; docstrings are the full specification"; ở `data-learn`: "Amount -999 is missing, never included in revenue ... normalize timestamp instants to UTC before Q1 membership".
  - **Thiếu về quy ước**: các lời giao việc có nhắc "Acme conventions" nhưng không kèm nội dung, vì chính tác tử chính cũng không biết. Subagent chỉ thấy lời nhắc được gửi nên không thể bù phần này.
  - **Thông tin sai làm hẹp phạm vi**: ở `data-learn`, tác tử chính tự thêm "Output JSON with exactly these keys (README specifies no additional output fields)". README không hề nói vậy, còn đề ghi "plus whatever the Acme reporting conventions require". Lời giao việc này loại bỏ luôn khả năng implementer thêm khối `meta` hay ghi `clean.csv`.
  - **Thừa**: ở `code-learn`, reviewer nêu các trường hợp ngoài đặc tả (độ chính xác `Decimal` thấp của ngữ cảnh, ký tự CR/LF trong tên CSV), dẫn đến hai vòng implementer và reviewer thêm mà không đổi kết quả check nào.
  - **Kiểm tra báo cáo của subagent có tác dụng**: ở `logs-learn`, sau lần giao việc đầu, tác tử chính tự đọc lại `errors.json`, phát hiện sai tên trường và giao lại: "do not use fields `timestamp`, `traceback`, `occurrences`". Ở `data-learn`, tác tử chính tự chạy script tính lại sau báo cáo của reviewer.
- Ảnh hưởng đến token và thời gian: đa tác tử tốn gấp 5,7 lần token và 8,2 lần thời gian mà điểm không đổi.

  | Tác vụ | Token baseline | Token subagents | Tỉ lệ | Giây baseline | Giây subagents |
  |---|---|---|---|---|---|
  | code-learn | 73.359 | 460.243 | 6,3 | 58,1 | 528,3 |
  | data-learn | 26.976 | 101.139 | 3,7 | 19,6 | 122,5 |
  | logs-learn | 24.658 | 145.830 | 5,9 | 15,8 | 118,3 |
  | Trung bình | 41.664 | 235.737 | 5,7 | 31,2 | 256,4 |

  Số lần gọi công cụ ở luồng chính gần như bằng nhau (25, 7, 8 so với 21, 7, 5), nên phần token tăng thêm nằm trong các subagent; `trace.md` không ghi việc bên trong subagent nên không tách được chi tiết hơn.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator, số skill bị xóa và lý do: curator chạy 2 lần (1 lần đầu và 1 lần chạy lại, trong giới hạn 2 lần chạy lại). Không sửa tay skill nào.
  - **Lần 1**: mô hình viết 3 skill nhưng chỉ 2 được ghi. Skill về dữ liệu dạng bảng bị `validate_skill` từ chối với thông báo "mentions evaluation material: orders": từ "orders" (đơn hàng) của tác vụ học trùng với một định danh của tác vụ đánh giá. Đây là cơ chế chống rò rỉ hoạt động đúng thiết kế, dù ở đây là báo động nhầm.
  - **Chạy lại 1**: thiếu skill cho họ `data` nghĩa là 3 check quy ước của họ này chắc chắn không được giúp, nên chúng tôi thêm vào prompt của curator một quy tắc tổng quát hóa ("Use domain-neutral wording: call the things in the data 'records' or 'rows'"), xóa 2 skill của lần 1 (để bộ skill đến từ một lần chạy duy nhất, tránh trùng lặp) và chạy lại. Lần này cả 3 skill đều hợp lệ. Prompt không chứa định danh nào của tác vụ đánh giá.
  - Lần chạy lại thứ hai không dùng: bộ skill hiện tại không có hướng dẫn sai hay gây hại, chỉ thiếu chi tiết ở vài quy tắc, và việc chọn lại cho đến khi đẹp sẽ làm lệch thí nghiệm.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `code-regression-hygiene` | Tổng quát cho mọi tác vụ sửa lỗi gói Python theo quy ước Acme. Không nêu tên hàm, tệp nguồn hay con số của tác vụ học; các tên xuất hiện (`tests/test_regressions.py`, `CHANGELOG.md`, `## Unreleased`, `- fix(<function name>): ...`) đều là chính quy ước. | Đúng và đầy đủ: cả ba quy tắc khớp nguyên văn `detail` của `rule_type_hints`, `rule_regression_tests`, `rule_changelog`, kể cả ngưỡng "at least three". | 5 dòng thân, dạng danh sách mệnh lệnh có bước tự kiểm. `description`: "Use when fixing bugs in a code package that requires tests, annotations, and a changelog." Nêu đúng tình huống kích hoạt. `skills_read` = 1 ở `code-learn`; điểm 7/10 lên 10/10. |
| `tabular-deliverable-validation` | Tổng quát về cách diễn đạt, nhưng quá trừu tượng: mất các chi tiết làm nên quy ước. | Không sai nhưng thiếu. Quy tắc 2 nói "include the required `meta` object with the specified keys and counts" mà không nêu ba khóa `source`, `rows_in`, `rows_used`. Quy tắc 3 nói "use the required header order" mà không nêu tiêu đề `order_id,timestamp_utc,region,amount_cents`. Quy tắc 4 nói "the required UTC format" mà không nêu `YYYY-MM-DDTHH:MM:SSZ`. Chỉ quy tắc "money values as integer cents" là đủ để làm theo. | 6 dòng thân. `description`: "Use when analyzing tabular records and producing structured answer and cleaned-data files." Đủ rộng. `skills_read` = 1 ở `data-learn`; điểm 5/8 lên 6/8 (chỉ `rule_money_in_cents` đạt thêm). |
| `structured-log-output` | Tổng quát cho tác vụ phân tích log thành JSON; các tên `errors`, `timestamp_utc` là khóa của định dạng đầu ra. | Hai quy tắc đúng và đủ (tên dịch vụ chữ thường, đổi `-` thành `_`; sắp xếp theo service rồi `timestamp_utc`). Quy tắc 1 thiếu: "Include every required top-level field with its exact required value" mà không nêu `"schema_version": 2` và `"generated_by": "log-triage"`. | 5 dòng thân. `description`: "Use when parsing log records into a structured JSON output." Nêu đúng tình huống. `skills_read` = 1 ở `logs-learn`; điểm 6/9 lên 8/9 (`rule_schema_header` vẫn trượt). |

Kiểm tra việc dùng skill ở Phần 3.4 (`results/skills-auto-dev/`, chỉ tác vụ học):

| Tác vụ | Baseline | skills-auto (Phần 3.4) | `skills_read` | Token baseline | Token skills-auto |
|---|---|---|---|---|---|
| code-learn | 7/10 | 10/10 | 1 | 73.359 | 188.680 |
| data-learn | 5/8 | 6/8 | 1 | 26.976 | 45.908 |
| logs-learn | 6/9 | 8/9 | 1 | 24.658 | 34.929 |

- **Skill được đọc đúng lúc và đúng cái**: ở cả ba tác vụ, lệnh công cụ đầu tiên là `read_file` trên đúng một `SKILL.md` phù hợp với họ tác vụ; hai skill còn lại không bị đọc thừa. `skills_modified` là `false` ở cả ba lần chạy.
- **Skill được làm theo, kể cả chỗ mơ hồ**: ở `data-learn`, tác tử có tạo khối `meta` và ghi `clean.csv` theo skill, nhưng phải tự đoán nội dung. Vết cho thấy nó tìm thêm thông tin (`ls skills/tabular-deliverable-validation`, `grep "Acme"` trong workspace) mà không thấy, rồi ghi `meta` với các khóa `input_rows`, `distinct_orders`, `known_amount_orders`, ... và `clean.csv` với tiêu đề `order_id,date,region,amount`. Cả hai sai so với quy ước nên `rule_meta_block` và `rule_clean_csv` vẫn trượt. Ở `logs-learn`, đầu ra không có `schema_version` hay `generated_by`.
- **Kết luận cho bước tiến hóa**: 6/9 check quy ước được sửa, đúng bằng số quy tắc mà skill chép nguyên văn; 3 check còn lại trượt đúng ở 3 chỗ curator tóm tắt quá mức. Lỗi nằm ở curator (làm mất chi tiết), không phải ở việc tác tử bỏ qua skill.

## 7. Kết quả so sánh (Phần 4.3, 4.4)

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
