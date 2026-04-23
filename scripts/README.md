# Scripts

该目录存放非主服务入口脚本：

- 数据导入脚本（如 `data2neon.py`）
- 评估脚本（如 `run_validation*.py`、`run_summary_eval.py`）
- 辅助验证脚本（如 `validate_priority1.py`、`test_query.py`）

说明：
- 这些脚本不属于 API 服务主链路
- 运行前请先配置 `.env` 或环境变量（尤其是 `DATABASE_URL`、`OPENAI_API_KEY`）
