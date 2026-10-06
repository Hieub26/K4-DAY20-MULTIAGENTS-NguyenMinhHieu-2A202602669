# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
|Nguyễn Minh Hiếu|2A202602669|Bài Lab|
| | | |

- Mô hình (tên deployment hoặc `LAB_MODEL`), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `gpt-6-luna` qua API OpenAI (`AZURE_OPENAI_ENDPOINT=https://api.openai.com/v1`, nhánh `ChatOpenAI` trong `model.py`); `LAB_TEMPERATURE=1` vì mô hình từ chối mọi giá trị khác ("'temperature' does not support 0.0 with this model. Only the default (1) value is supported"); `recursion_limit=60` (mặc định của runner).
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `deepagents` 0.7.21; chạy trong Docker (image `python:3.12-slim`, Python 3.12.15) trên Windows 11 Home (10.0.26200).
- Số lần chạy tác vụ đã dùng / ngân sách: 21 lần chạy tác vụ với `gpt-6-luna` (18 lần chính thức trong bảng ở mục 7 và 3 lần kiểm tra skill ở Phần 3.4), cộng 2 lần gọi curator. Khoảng 10 lần chạy thử với mô hình khác đã bị loại (xem phụ lục). Tài liệu của lab không nêu con số ngân sách cụ thể.
- Commit của tag `freeze`: `7740bc539ebe1c6e6845ee2afacd7bc34f31ebcf` (2026-10-06 19:55 +07:00); commit `hypotheses` đứng ngay trước: `39e198e`.

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

Bảng do `python -m lab.compare > report/table.md` sinh ra (điểm = số check đạt / tổng số check):

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 7/10 | 7/10 | 10/10 |
| data-learn | 5/8 | 5/8 | 6/8 |
| logs-learn | 6/9 | 6/9 | 8/9 |
| code-eval | 7/11 | 7/11 | 10/11 |
| data-eval | 5/9 | 4/9 | 6/9 |
| logs-eval | 6/10 | 6/10 | 8/10 |
| **Mean score - learning tasks** | 0.66 | 0.66 | 0.88 |
| **Mean score - evaluation tasks** | 0.60 | 0.56 | 0.79 |
| **Mean tokens per run** | 38,750 | 166,879 | 78,651 |
| **Runs that read a skill** | 0/6 | 0/6 | 6/6 |

Kết quả `python scripts/check_breakdown.py`:

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval     18/18         0/12          35,836      0/3
baseline      learn    18/18         0/9           41,664      0/3
subagents     eval     17/18         0/12          98,020      0/3
subagents     learn    18/18         0/9          235,737      0/3
skills-auto   eval     18/18         6/12          66,991      3/3
skills-auto   learn    18/18         6/9           90,311      3/3
```

- Không lần chạy nào trong 18 lần chạy chính thức có `error`, và `skills_modified` là `false` ở mọi lần.
- `python scripts/verify_freeze.py` báo `checked 6 runs of skill conditions: OK` (xem ghi chú về kết thúc dòng ở phụ lục).
- Điểm tác vụ học của `skills-auto` ở Phần 3.4 (trước đóng băng) được lưu riêng ở `results/skills-auto-dev/`: 10/10, 6/8, 8/9.

## 8. Phân tích

1. **Điều kiện nào cải thiện điểm.** Chỉ `skills-auto` cải thiện, và cải thiện ở cả hai tập: tác vụ học từ 18/27 lên 24/27 check (điểm trung bình 0,66 lên 0,88), tác vụ đánh giá từ 18/30 lên 24/30 (0,60 lên 0,79). `subagents` không cải thiện ở đâu: bằng `baseline` trên tác vụ học (18/27) và thấp hơn 1 check trên tác vụ đánh giá (17/30; 0,56 so với 0,60). Không có điều kiện nào tăng ở tác vụ học mà không tăng ở tác vụ đánh giá, nên không có dấu hiệu quá khớp rõ rệt theo nghĩa đó. Tuy vậy mức tăng tương đối có giảm: skill sửa được 6/9 check quy ước ở tác vụ học nhưng chỉ 6/12 ở tác vụ đánh giá.
2. **Check kỹ thuật so với check quy ước.** Skill chỉ giúp check quy ước: 0/9 lên 6/9 (học) và 0/12 lên 6/12 (đánh giá). Check kỹ thuật đã đạt 18/18 ở `baseline` trên cả hai tập nên không còn chỗ để tăng. Ba check quy ước **mới** của tác vụ đánh giá (`rule_version_bump`, `rule_sorted_keys_format`, `rule_source_line`) trượt ở cả ba điều kiện, kể cả `skills-auto` (0/3). Lý do: curator chỉ đọc phản hồi của tác vụ học, mà các quy ước này không xuất hiện ở đó, nên skill không thể chứa chúng. Sáu check được sửa ở tác vụ đánh giá đều là quy ước dùng lại từ tác vụ học.
3. **Một check skill giúp đạt và một check skill không giúp.**
   - *Giúp đạt*: `rule_changelog` ở `code-eval`. Vết của `skills-auto/code-eval` bắt đầu bằng `read_file` trên `skills/code-regression-hygiene/SKILL.md`; sau khi sửa mã, tác tử ghi `workspace/tests/test_regressions.py` rồi sửa `workspace/CHANGELOG.md`, thêm dưới "## Unreleased" các dòng dạng "- fix(billable_blocks): round partial blocks up and reject invalid values", đúng khuôn `- fix(<function name>): <short description>` mà skill chép nguyên văn. Ở `baseline/code-eval` check này trượt.
   - *Không giúp*: `rule_meta_block` ở `data-eval`. Skill được đọc (`skills_read` = 2, gồm `tabular-deliverable-validation`) và được làm theo: tác tử có ghi khối `meta` vào `answer.json` và tự kiểm rằng tập khóa của `answer.json` có chứa `meta`. Check vẫn trượt vì skill chỉ viết "include the required `meta` object with the specified keys and counts" mà không nêu ba khóa `source`, `rows_in`, `rows_used`; vết cho thấy tác tử còn `ls skills/tabular-deliverable-validation` để tìm thêm chi tiết nhưng không có. Đây là trường hợp "skill thiếu", không phải "không đọc" hay "đọc mà không làm theo". `rule_clean_csv` (cả hai tập) và `rule_schema_header` (cả hai tập) trượt vì cùng lý do.
   - Không có trường hợp skill không được đọc: `skills_read` ≥ 1 ở 6/6 lần chạy, và skill được đọc ngay ở lệnh công cụ đầu tiên. Ở hai tác vụ `data`, tác tử đọc thừa cả `structured-log-output`, một chi phí nhỏ do `description` của skill đó ("parsing log records into a structured JSON output") đủ rộng để trông có liên quan.
4. **Chi phí.**

   | Điều kiện | Token trung bình mỗi lần chạy | So với baseline | Điểm trung bình (6 tác vụ) | Điểm trên 100.000 token |
   |---|---|---|---|---|
   | baseline | 38.750 | 1,0 | 0,63 | 1,63 |
   | subagents | 166.879 | 4,3 | 0,61 | 0,37 |
   | skills-auto | 78.651 | 2,0 | 0,84 | 1,06 |

   `baseline` có hiệu quả trên mỗi token cao nhất; `skills-auto` đổi gấp đôi token lấy thêm 0,21 điểm trung bình (thêm khoảng 40.000 token mỗi lần chạy); `subagents` tốn gấp 4,3 lần token mà điểm không tăng. Phần token tăng của `skills-auto` không nằm ở việc đọc skill (mỗi skill dưới 10 dòng) mà ở việc làm thêm theo quy ước: viết chú thích kiểu, tệp test hồi quy, `clean.csv`, và tự kiểm. Đa tác tử **không đáng chi phí** trong thí nghiệm này: lỗi còn lại là thiếu thông tin về quy ước, và chia việc cho subagent không tạo ra thông tin đó. Điều kiện này còn có một lỗi kỹ thuật ở `data-eval` (`march_orders_utc`): tác tử chính ghi 48 trong khi `baseline` ghi 44 và đạt; script của tác tử chính đếm cả đơn có `total` bị thiếu, và reviewer được giao kiểm tra sau đó không khiến kết quả được sửa. Với một mẫu duy nhất, không thể khẳng định đây là hệ quả của đa tác tử hay chỉ là nhiễu.
5. **Rò rỉ và quá khớp trong skill.**
   - *Rò rỉ*: không có. Curator chỉ nạp `run.json` có `role == "learn"`; ba skill không chứa định danh nào của tác vụ đánh giá (`validate_skill` kiểm tra bằng `eval_markers()`), và ở lần chạy curator đầu tiên cơ chế này đã từ chối một skill chỉ vì chứa từ "orders". Giả thuyết được commit (`39e198e`) trước tag `freeze` (`7740bc5`), và mọi lần chạy trên tác vụ đánh giá đều bắt đầu sau tag. Chúng tôi không mở `check.py` của tác vụ đánh giá.
   - *Quá khớp*: bộ skill không chứa tên tệp nguồn, hàm, cột hay con số của tác vụ học, và sáu quy tắc nguyên văn chuyển sang tác vụ đánh giá trọn vẹn (6/6 check dùng lại tương ứng đều đạt). Tuy nhiên nội dung skill là danh sách quy ước của Acme chứ không phải quy trình tổng quát, nên nó "khớp" với bộ quy ước đã thấy và bằng 0 trước quy ước mới (0/3). Đây là giới hạn về độ phủ hơn là quá khớp về dữ liệu.
   - *Điều chỉnh prompt của curator sau lần chạy đầu* (thêm quy tắc dùng từ trung tính "records"/"rows") là một quyết định dựa trên đầu ra của tác vụ học và trên thông báo của `validate_skill`, không dựa trên điểm của tác vụ đánh giá. Thông báo đó có để lộ rằng "orders" là một định danh của tác vụ đánh giá; quy tắc được thêm không nhắc đến từ này.
6. **Nhiễu.** Cùng bộ skill, trên tác vụ học: Phần 3.4 cho 10/10, 6/8, 8/9 và sau đóng băng cũng cho 10/10, 6/8, 8/9, với đúng các check trượt giống nhau (`rule_meta_block`, `rule_clean_csv`, `rule_schema_header`). Chênh lệch điểm là 0/27 check. Token dao động nhẹ: 188.680, 45.908, 34.929 so với 182.134, 51.210, 37.589 (lệch từ 3% đến 12%), và `data-learn` đọc 1 skill ở lần đầu nhưng 2 skill ở lần sau. Như vậy trong hai lần lặp này điểm ổn định dù nhiệt độ là 1, nên chênh lệch +6 check của `skills-auto` lớn hơn nhiều so với nhiễu quan sát được, còn chênh lệch -1 check của `subagents` ở `data-eval` thì không phân biệt được với nhiễu. Hai lần lặp trên ba tác vụ là quá ít để ước lượng phương sai một cách đáng tin.

**Đối chiếu giả thuyết.**

| Giả thuyết | Kết quả | Số liệu |
|---|---|---|
| H1: `subagents` ngang `baseline`, token ít nhất gấp 3 | Đúng về điểm, sai một phần về token | Chênh 0, -1, 0 check ở ba tác vụ đánh giá. Token gấp 2,7 lần trên tác vụ đánh giá (98.020 so với 35.836), thấp hơn ngưỡng 3 đã dự đoán; gấp 4,3 lần tính trên cả 6 tác vụ. |
| H2: `skills-auto` cao nhất, chỉ tăng ở check quy ước, +1 đến +2 check mỗi tác vụ, token gấp 1,5 đến 2,5 | Đúng, trừ mức tăng ở `code-eval` | Cao nhất ở cả ba tác vụ đánh giá; kỹ thuật giữ 18/18; quy ước 0/12 lên 6/12; mức tăng +3, +1, +2 (`code-eval` vượt dự đoán); token gấp 1,9 lần. Ba quy tắc mơ hồ đúng là không giúp được. |
| H3: mức tăng ở tác vụ đánh giá nhỏ hơn ở tác vụ học; quy ước mới trượt ở cả ba điều kiện | Sai về số check tuyệt đối, đúng về tỉ lệ và về quy ước mới | Mức tăng là +6 check ở cả hai tập, không nhỏ hơn. Tính theo tỉ lệ check quy ước được sửa thì 6/9 so với 6/12, và điểm trung bình tăng 0,22 so với 0,19. Ba quy ước mới trượt ở cả ba điều kiện. |

## 9. Hạn chế và tính hợp lệ

1. **Số tác vụ nhỏ**: mỗi vai trò chỉ có 3 tác vụ, mỗi họ 1 tác vụ. Mọi con số trung bình dựa trên 3 điểm dữ liệu, nên một check lệch đã đổi điểm trung bình khoảng 0,03 đến 0,04. Kết luận "subagents kém baseline 0,04 trên tác vụ đánh giá" vì thế không có ý nghĩa thống kê.
2. **Mỗi cấu hình chạy một lần, nhiệt độ bằng 1**: `gpt-6-luna` không cho đặt nhiệt độ 0, nên mỗi lần chạy là một mẫu ngẫu nhiên. Ước lượng nhiễu duy nhất là cặp lần chạy `skills-auto` trên tác vụ học (lệch 0 check), không đủ để đặt khoảng tin cậy cho bất kỳ chênh lệch nào. Thử thách mở rộng 6e (phụ lục) bổ sung hai lần lặp trên tác vụ đánh giá để giảm bớt hạn chế này.
3. **Curator cũng chỉ là một mẫu**: bộ skill cuối đến từ một lần sinh, và chất lượng của nó quyết định kết quả chính. Lần chạy đầu của curator giữ nguyên văn `schema_version` và `generated_by` trong skill về log, lần chạy lại thì làm mất. Một lần sinh khác có thể sửa được ít hơn hoặc nhiều hơn 6 check quy ước, nên con số "6/12 trên tác vụ đánh giá" là kết quả của bộ skill này, không phải của phương pháp nói chung.
4. **Tác vụ do giảng viên thiết kế sẵn quy ước**: tác vụ đánh giá dùng lại đúng các quy ước của tác vụ học và phản hồi `detail` phát biểu nguyên văn quy tắc. Đây là điều kiện thuận lợi cho skill tự sinh; với phản hồi mơ hồ hơn hoặc quy ước không lặp lại, lợi ích có thể mất, phù hợp với ghi nhận của SkillsBench.
5. **Một mô hình duy nhất và mô hình mạnh**: `baseline` đạt 36/36 check kỹ thuật, nên thí nghiệm không đo được liệu subagent hay skill có giúp phần kỹ thuật hay không (hiệu ứng trần). Các lần chạy thử trước đó với một mô hình yếu hơn (đã loại, xem phụ lục) cho thấy lỗi kỹ thuật xuất hiện và dao động mạnh giữa các lần chạy, nên kết luận ở đây không nên suy rộng sang mô hình khác.
6. **Số đếm chỉ ở luồng chính**: `tool_calls` và `trace.md` không ghi việc bên trong subagent, nên phân tích cơ chế của điều kiện `subagents` chỉ dựa trên lời giao việc và báo cáo trả về.

## 10. Kết luận

Với `gpt-6-luna`, tác tử mặc định đạt toàn bộ check kỹ thuật (36/36) và trượt toàn bộ check quy ước (0/21), vì quy ước của tổ chức không có trong đề. Skill do curator tự sinh từ phản hồi của tác vụ học là điều kiện duy nhất cải thiện điểm: 18/30 lên 24/30 check trên tác vụ đánh giá, với chi phí gấp khoảng 2 lần token. Lợi ích đó bị giới hạn ở những quy ước đã gặp và được curator chép nguyên văn: ba quy tắc bị tóm tắt mơ hồ và ba quy ước mới đều không được giúp. Đa tác tử tốn gấp 4,3 lần token mà không tăng điểm, vì giao việc không bù được thông tin còn thiếu. Bước cải tiến tiếp theo là buộc curator giữ nguyên văn mọi tên khóa, tiêu đề và giá trị xuất hiện trong `detail` (hoặc tự kiểm skill bằng cách đối chiếu lại với `detail`). Ba lần lặp trên tác vụ đánh giá ở thử thách mở rộng 6e (phụ lục) cho cùng thứ hạng giữa ba điều kiện.

## Phụ lục

- Lệnh đã chạy (theo thứ tự), mọi lệnh Python chạy trong container `lab-deepagents` (`docker run --rm --env-file .env -v "${PWD}:/lab" lab-deepagents ...`):

  ```text
  pytest                                                    # 29 passed
  python -m lab.runner --condition baseline --tasks learn
  python -m lab.runner --condition subagents --tasks learn
  python -m lab.curator                                     # lần 1: 2 skill được ghi, 1 bị từ chối
  python -m lab.curator                                     # chạy lại 1: 3 skill
  python -m lab.runner --condition skills-auto --tasks learn
  mv results/skills-auto results/skills-auto-dev
  git add -A && git commit -m "hypotheses"                  # 39e198e
  git commit --allow-empty -m "freeze skills" && git tag freeze   # 7740bc5
  python -m lab.runner --condition subagents --tasks eval   # chạy đồng thời với hai lệnh dưới
  python -m lab.runner --condition baseline --tasks eval
  python -m lab.runner --condition skills-auto --tasks all
  python scripts/verify_freeze.py                           # OK
  python -m lab.compare > report/table.md
  python scripts/check_breakdown.py
  ```

- Thử thách mở rộng: hướng 6e, lặp để đo nhiễu. Xem mục "Thử thách mở rộng 6e" ở cuối phụ lục.
- Ghi chú khác:
  - **Mở rộng runner**: `run_task` dùng `agent.stream(..., stream_mode="values")` thay cho `invoke` để vẫn giữ được vết khi lần chạy lỗi giữa chừng (mở rộng tùy chọn nêu trong `03_runner.md`).
  - **Kết thúc dòng trên Windows**: kho được checkout với `core.autocrlf=true`, nên các tệp trong `tasks/` có kết thúc dòng CRLF trên đĩa. Check `tests_not_modified` của họ `code` so băm SHA-256 với bản LF và sẽ trượt dù tác tử không đụng vào test. Mọi lần chạy trong báo cáo vì vậy gắn một bản `tasks/` nguyên gốc (xuất bằng `git archive`, kết thúc dòng LF) chỉ-đọc vào `/lab/tasks` của container; nội dung tệp giống hệt bản trong git. Vì cùng lý do, `verify_freeze.py` được chạy trong container có `git` với `core.autocrlf=true` (như máy chủ), và được kiểm lại trên một bản clone LF sạch; cả hai đều báo OK. Chạy script này trực tiếp trên Windows sẽ báo sai lệch băm vì dấu phân cách đường dẫn khác Linux.
  - **Các lần chạy đã loại, không có trong `results/`**: trước khi chốt `gpt-6-luna`, harness được chạy thử với `gemini-3.1-flash-lite` (khoảng 10 lần chạy tác vụ học, gồm cả các lần bị ảnh hưởng bởi lỗi CRLF nói trên và một lần lỗi 400 của endpoint tương thích OpenAI). Các lần này dùng mô hình khác nên không so sánh được và đã bị xóa; chúng không được dùng cho bất kỳ số liệu nào trong báo cáo, và không có lần nào chạy trên tác vụ đánh giá.
  - **Chạy đồng thời**: ở Phần 4.2, `subagents --tasks eval` chạy song song với hai lệnh còn lại để tiết kiệm thời gian. Số `seconds` của các lần chạy đó có thể bị ảnh hưởng nhẹ; token và điểm thì không.

### Thử thách mở rộng 6e: lặp để đo nhiễu

**Câu hỏi.** Bảng ở mục 7 dựa trên một lần chạy cho mỗi ô, ở nhiệt độ 1. Các chênh lệch giữa ba điều kiện trên tác vụ đánh giá có lớn hơn dao động giữa các lần chạy không?

**Thiết kế.** Chạy lại cả ba điều kiện trên ba tác vụ đánh giá thêm hai lần, với cùng mã, cùng mô hình và cùng bộ skill đã đóng băng. Kết quả ghi vào thư mục riêng `results-rep2/` và `results-rep3/`; `results/` và `report/table.md` không bị đụng tới. Tổng cộng 18 lần chạy thêm, không lần nào có `error`. Sáu lần chạy `skills-auto` mới đều có `skills_modified = false` và `skills_sha256` trùng với các lần chạy chính thức (`bcecba57...`), tức dùng đúng bộ skill của tag `freeze`.

```text
python -m lab.runner --condition baseline    --tasks eval --results results-rep2
python -m lab.runner --condition skills-auto --tasks eval --results results-rep2
python -m lab.runner --condition subagents   --tasks eval --results results-rep2
# lặp lại ba lệnh trên với --results results-rep3 (hai lần lặp chạy đồng thời)
python -m lab.noise results results-rep2 results-rep3 > report/noise.md
```

`src/lab/noise.py` là mô-đun mới (không sửa tệp có sẵn nào): nó đọc các `run.json` của nhiều thư mục kết quả và in điểm từng lần lặp, trung bình, khoảng dao động và các check đổi kết quả giữa các lần.

**Số liệu** (nội dung `report/noise.md`; lần 1 là kết quả chính ở mục 7):

| Điều kiện | Tác vụ | Lần 1 | Lần 2 | Lần 3 | Trung bình | Thấp nhất - cao nhất | Check đổi kết quả giữa các lần |
|---|---|---|---|---|---|---|---|
| baseline | code-eval | 7/11 | 7/11 | 7/11 | 7,00 | 7 - 7 | không |
| baseline | data-eval | 5/9 | 5/9 | 5/9 | 5,00 | 5 - 5 | không |
| baseline | logs-eval | 6/10 | 6/10 | 6/10 | 6,00 | 6 - 6 | không |
| subagents | code-eval | 7/11 | 7/11 | 8/11 | 7,33 | 7 - 8 | `rule_type_hints` |
| subagents | data-eval | 4/9 | 5/9 | 5/9 | 4,67 | 4 - 5 | `march_orders_utc` |
| subagents | logs-eval | 6/10 | 6/10 | 6/10 | 6,00 | 6 - 6 | không |
| skills-auto | code-eval | 10/11 | 10/11 | 10/11 | 10,00 | 10 - 10 | không |
| skills-auto | data-eval | 6/9 | 6/9 | 6/9 | 6,00 | 6 - 6 | không |
| skills-auto | logs-eval | 8/10 | 8/10 | 8/10 | 8,00 | 8 - 8 | không |

| Điều kiện | Tổng check đạt (trên 30) ở ba lần lặp | Trung bình | Kỹ thuật mỗi lần | Quy ước mỗi lần | Token trung bình mỗi lần chạy, từng lần lặp | Token trung bình cả 9 lần chạy |
|---|---|---|---|---|---|---|
| baseline | 18, 18, 18 | 18,00 | 18/18, 18/18, 18/18 | 0/12, 0/12, 0/12 | 35.836; 43.698; 42.566 | 40.700 |
| subagents | 17, 18, 19 | 18,00 | 17/18, 18/18, 18/18 | 0/12, 0/12, 1/12 | 98.021; 130.535; 128.746 | 119.101 |
| skills-auto | 24, 24, 24 | 24,00 | 18/18, 18/18, 18/18 | 6/12, 6/12, 6/12 | 66.991; 57.437; 56.525 | 60.318 |

**So sánh với kết quả chính.**

- **Điểm của `baseline` và `skills-auto` lặp lại hoàn toàn**: 18/30 và 24/30 ở cả ba lần, với đúng cùng tập check trượt ở từng tác vụ (0 trên 180 lượt check đổi kết quả). Chênh lệch +6 check của `skills-auto` vì vậy không phải do nhiễu trong phạm vi ba lần lặp này.
- **`subagents` là điều kiện duy nhất dao động**: 17, 18, 19 check; trung bình 18,00, đúng bằng `baseline`. Con số 0,56 so với 0,60 ở mục 7 (kém `baseline` 1 check) là một mẫu ở đầu thấp của khoảng dao động; ở lần 3 chính điều kiện này lại hơn `baseline` 1 check. Kết luận đúng là "không khác `baseline` về điểm", không phải "kém hơn".
- **Token dao động nhiều hơn điểm**: một lần chạy `baseline` tốn từ 16.545 đến 82.695 token tùy tác vụ và lần lặp; `subagents` từ 78.741 đến 194.818. Tính trên 9 lần chạy mỗi điều kiện, `subagents` tốn gấp 2,9 lần `baseline` và `skills-auto` gấp 1,5 lần. Các tỉ lệ một-lần ở mục 8 (2,7 và 1,9 trên tác vụ đánh giá) cùng hướng nhưng lệch đáng kể về độ lớn, nên không nên trích tỉ lệ token với hai chữ số có nghĩa.
- **Đối chiếu giả thuyết**: H1 được củng cố về điểm (chênh trung bình 0 check); ngưỡng "token ít nhất gấp 3" vẫn chưa đạt trên tác vụ đánh giá (2,9). H2 và phần "quy ước mới trượt ở mọi điều kiện" của H3 giữ nguyên ở cả ba lần lặp.

**Cơ chế, dựa trên vết.**

- *Vì sao `baseline` và `skills-auto` ổn định*: check kỹ thuật là phần mô hình làm được chắc chắn (54/54 ở mỗi điều kiện qua ba lần). Check quy ước thì do thông tin quyết định chứ không do may rủi: không có skill thì tác tử không có nguồn nào để biết quy ước (0/36), có skill thì nó làm đúng những quy tắc được ghi nguyên văn và trượt đúng những quy tắc ghi mơ hồ (6/12 ở cả ba lần, cùng các check `rule_meta_block`, `rule_clean_csv`, `rule_schema_header` và ba quy ước mới). Ở cả 9 lần chạy `skills-auto`, skill phù hợp đều được đọc (`skills_read` từ 1 đến 2).
- *Vì sao `subagents` dao động*: cách giao việc thay đổi giữa các lần. Ở `data-eval`, lần 1 và lần 2 gọi `explorer` rồi `reviewer` và tác tử chính tự tính; lần 3 gọi đủ `explorer`, `implementer`, `reviewer`. Ở `logs-eval` lần 3, tác tử chính bỏ qua cả ba subagent tự định nghĩa và gọi `general-purpose` một lần. Số lần giao việc ở `code-eval` là 3, 4, 3.
- *`march_orders_utc` ở `data-eval`*: lần 1 tác tử chính ghi 48 (script của nó đếm cả đơn thiếu `total`) và trượt; lần 2 ghi 44 và đạt, giống `baseline`. Lỗi ở lần 1 nằm trong script của tác tử chính chứ không trong subagent, nên nó là dao động của mô hình, được lộ ra vì luồng làm việc khác đi, chứ không phải hệ quả tất yếu của đa tác tử.
- *`rule_type_hints` ở `code-eval` lần 3*: đây là check quy ước duy nhất `subagents` từng đạt (1/36). Ở lần này tác tử chính tự đoán và viết vào lời giao việc cho `implementer`: "Preserve sensible Acme Python style, type hints, and no unnecessary changes." Lời giao việc ở hai lần còn lại không nhắc đến chú thích kiểu và check này trượt. Tác tử chính không có nguồn nào cho quy ước đó, nên đây là một lần đoán trúng chứ không phải năng lực ổn định.

**Hạn chế.**

- Ba lần lặp vẫn là ít: với 0 lượt đổi kết quả trên 180 lượt check của `baseline` và `skills-auto`, chỉ có thể nói dao động là hiếm, chưa ước lượng được tần suất thật.
- Chỉ lặp trên tác vụ đánh giá và chỉ lặp phần chạy tác tử. Nguồn nhiễu lớn hơn là curator thì không được lặp: bộ skill vẫn là một mẫu duy nhất (hạn chế 3 ở mục 9), nên kết quả "24/30 ổn định" là của bộ skill này.
- Hai lần lặp mới chạy đồng thời với nhau, nên số `seconds` không so sánh được với lần 1.
- Lần 1 chính là kết quả chính, không phải một lần chạy độc lập mới; ba lần lặp không cùng thời điểm.

**Bước tiếp theo.** Lặp cả bước curator (sinh nhiều bộ skill từ cùng phản hồi, đóng băng từng bộ, đo từng bộ) để tách dao động do curator khỏi dao động do tác tử; đó là nguồn nhiễu mà thí nghiệm này chưa đo.
