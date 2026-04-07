# Fast MinIO Chat Demo

這是一個可切換雙後端的聊天示範專案，整合了：

- Frontend: Next.js
- Backend: FastAPI 或 Spring Boot
- Database: MongoDB
- Object Storage: MinIO
- LLM: Ollama

目前前端已支援在 UI 內切換 `FastAPI` 與 `Spring Boot` 後端，方便開發、比較與遷移。

## 快速入口

- 完整啟動教學: [docs/start-project.md](/Users/yu-hsin.chen/Documents/projects/fast-minio/docs/start-project.md)
- FastAPI 後端說明: [fastapi_backend/README.md](/Users/yu-hsin.chen/Documents/projects/fast-minio/fastapi_backend/README.md)

## 專案結構

```text
fast-minio/
├── frontend/          # Next.js 前端
├── fastapi_backend/   # FastAPI 後端
├── src/               # Spring Boot 後端
├── docs/              # 專案文件
└── docker-compose.yml # MongoDB / MinIO
```

## 最短啟動路線

1. 啟動基礎服務

```bash
cd /Users/yu-hsin.chen/Documents/projects/fast-minio
docker compose up -d
```

2. 確認 Ollama 與模型

```bash
ollama list
ollama pull gemma3:4b
```

3. 啟動其中一個後端

FastAPI:

```bash
cd /Users/yu-hsin.chen/Documents/projects/fast-minio/fastapi_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Spring Boot:

```bash
cd /Users/yu-hsin.chen/Documents/projects/fast-minio
./mvnw spring-boot:run
```

4. 啟動前端

```bash
cd /Users/yu-hsin.chen/Documents/projects/fast-minio/frontend
npm install
npm run dev
```

5. 打開前端

- [http://localhost:3000](http://localhost:3000)

## 後端切換

你可以用兩種方式切換前端連線的 backend：

- 在 UI 的 `後端目標` 下拉選單切換
- 在前端環境變數設定預設值

前端支援的環境變數如下：

```bash
NEXT_PUBLIC_DEFAULT_BACKEND=fastapi
NEXT_PUBLIC_FASTAPI_API_BASE=http://localhost:8000
NEXT_PUBLIC_SPRING_API_BASE=http://localhost:8080
```

範例檔案可參考：

- [frontend/.env.example](/Users/yu-hsin.chen/Documents/projects/fast-minio/frontend/.env.example)

更多細節與常見問題請直接看：

- [docs/start-project.md](/Users/yu-hsin.chen/Documents/projects/fast-minio/docs/start-project.md)
