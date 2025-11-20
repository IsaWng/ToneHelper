# ToneHelper / 礼貌表达助手

ToneHelper 是一个用于把短句或段落改写成更温和、更口语或更简洁语气的轻量服务。后端基于 FastAPI 提供 `/api/rewrite` 接口，可直接对接前端页面（`frontend/home.html`），也支持通过 Docker 或 Docker Compose 部署。若提供 `OPENAI_API_KEY`，服务会优先调用 OpenAI Responses API；否则自动退回到内置的 mock 规则，仍能提供基础体验。

## 功能总览
- 支持中文、英文、西班牙文，能自动探测语言或手动锁定。
- 每次返回 3 个候选改写，并附带生成原因 (`reason`)。
- `/health` 端点便于做健康检查与查看当前是否启用 OpenAI。
- `frontend/home.html` 前端示例包含输入限制、快捷键、历史记录与占位生成逻辑，可在本地直接双击预览。
- 附带 `Dockerfile` 与 `docker-compose.yml`，便于容器化部署。

## 目录结构
```
ToneHelper/
├── backend/            # FastAPI 服务源码及工具
│   ├── app.py          # FastAPI create_app 工厂
│   ├── config.py       # 配置与常量
│   ├── mock_engine.py  # Mock 生成逻辑
│   ├── models.py       # Pydantic 模型
│   ├── openai_provider.py
│   ├── services.py     # 业务服务
│   └── text_utils.py
├── frontend/
│   └── home.html       # 前端静态页面
├── main.py             # Uvicorn 入口
├── app.py              # 早期 Flask 版本示例（未在 docker-compose 中启用）
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 环境变量

| 变量名 | 说明 | 默认值 |
| --- | --- | --- |
| `OPENAI_API_KEY` | （可选）用于启用 OpenAI Responses API；为空时使用本地 mock | 空 |
| `PUERTO` | `app.py` Flask 版本监听端口 | 8080 |
| `MODELO_POR_DEFECTO` | Flask 版本使用的模型名称 | `gpt-5-nano` |

> FastAPI 版本 (`main.py`) 默认监听 `0.0.0.0:8000`。如需修改，可在启动 `uvicorn` 时传入 `--port`。

## 本地运行（FastAPI）
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-xxx   # 可选
uvicorn main:app --host 0.0.0.0 --port 8000
```
启动后：
- 访问 `http://localhost:8000/health` 查看健康状态。
- 将 `frontend/home.html` 中的 `window.API_ENDPOINT` 改成 `http://localhost:8000/api/rewrite`（仓库已默认设置），直接用浏览器打开文件即可调用。

## Docker / Compose

```bash
docker build -t tonehelper .
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-xxx tonehelper
```

或使用 Compose：
```bash
docker compose up --build
```
如果需要 OpenAI，请在根目录创建 `.env` 并填入 `OPENAI_API_KEY=...`（已在 `docker-compose.yml` 中通过 `env_file` 引用）。

## API 说明

### `GET /health`
返回示例：
```json
{
  "ok": true,
  "use_openai": false
}
```

### `POST /api/rewrite`
请求体（限制：20–300 字符）：
```json
{
  "text": "请把周五前的需求排期发我，最好今天确认。",
  "tone": "softer",          // softer | colloquial | concise
  "lang": "auto"             // auto | zh | en | es
}
```

响应体：
```json
{
  "rewrites": [
    { "text": "请把周五前的需求排期发我，感谢理解。", "reason": "语气缓和" },
    { "text": "如果方便的话，把周五前的排期发我，好吗？", "reason": "保留边界" },
    { "text": "麻烦今天确认并发我周五前的排期。", "reason": "减少冲突" }
  ]
}
```

- `tone` 与 `lang` 会影响 mock 及 OpenAI 的提示词。
- 如果启用了 OpenAI，但响应格式不符合预期，会自动回退到 mock 以保证可用性。

## 前端示例（`frontend/home.html`）
- 支持 Cmd/Ctrl+Enter 触发生成、Esc 清空。
- 内置输入计数器（最多 300 字符）与简单的本地历史记录（LocalStorage）。
- 在没有后端时，会自动调用前端 mock 逻辑，方便静态 Demo。
- 发布到静态托管（Vercel、Netlify 等）时，只需把 `window.API_ENDPOINT` 指向你的 API 地址即可。

## 其他说明
- `app.py` 展示了使用 Flask + OpenAI Responses API 的另一种实现，便于与现有 Flask 项目集成；功能与 FastAPI 版本类似，但未包含 mock 回退。
- 如需扩展更多语气/语言，可分别在 `mock_*.py` 逻辑与 OpenAI 提示词中添加，并同步更新前端按钮与校验。

欢迎根据业务需要定制提示词、增加鉴权或接入数据库，以构建更完善的 Tone Helper。
