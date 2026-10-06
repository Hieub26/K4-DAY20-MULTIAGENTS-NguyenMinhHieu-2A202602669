Lần lặp: `results`, `results-rep2`, `results-rep3`

| Điều kiện | Tác vụ | Lần 1 | Lần 2 | Lần 3 | Trung bình | Thấp nhất - cao nhất | Check đổi kết quả giữa các lần |
|---|---|---|---|---|---|---|---|
| baseline | code-eval | 7/11 | 7/11 | 7/11 | 7.00 | 7 - 7 | không |
| baseline | data-eval | 5/9 | 5/9 | 5/9 | 5.00 | 5 - 5 | không |
| baseline | logs-eval | 6/10 | 6/10 | 6/10 | 6.00 | 6 - 6 | không |
| subagents | code-eval | 7/11 | 7/11 | 8/11 | 7.33 | 7 - 8 | `rule_type_hints` |
| subagents | data-eval | 4/9 | 5/9 | 5/9 | 4.67 | 4 - 5 | `march_orders_utc` |
| subagents | logs-eval | 6/10 | 6/10 | 6/10 | 6.00 | 6 - 6 | không |
| skills-auto | code-eval | 10/11 | 10/11 | 10/11 | 10.00 | 10 - 10 | không |
| skills-auto | data-eval | 6/9 | 6/9 | 6/9 | 6.00 | 6 - 6 | không |
| skills-auto | logs-eval | 8/10 | 8/10 | 8/10 | 8.00 | 8 - 8 | không |

| Điều kiện | Tổng check đạt mỗi lần lặp | Trung bình | Dao động | Kỹ thuật mỗi lần | Quy ước mỗi lần | Token trung bình mỗi lần chạy (từng lần lặp) |
|---|---|---|---|---|---|---|
| baseline | 18, 18, 18 | 18.00 | 18 - 18 | 18/18, 18/18, 18/18 | 0/12, 0/12, 0/12 | 35,836, 43,698, 42,566 |
| subagents | 17, 18, 19 | 18.00 | 17 - 19 | 17/18, 18/18, 18/18 | 0/12, 0/12, 1/12 | 98,021, 130,535, 128,746 |
| skills-auto | 24, 24, 24 | 24.00 | 24 - 24 | 18/18, 18/18, 18/18 | 6/12, 6/12, 6/12 | 66,991, 57,437, 56,525 |
