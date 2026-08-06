# 專案啟動指南

這份文件說明如何在本機啟動整個專案，包含基礎服務、後端、前端，以及如何在 `FastAPI` 與 `Spring Boot` 後端之間切換。

## 架構與預設連接埠

- Frontend: Next.js, `http://localhost:3000`
- FastAPI backend: `http://localhost:8000`
- Spring Boot backend: `http://localhost:8080`
- MongoDB: `mongodb://localhost:27017`
- MinIO API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`
- LLM provider: OpenCode Zen (FastAPI) / Ollama (Spring Boot)

## 先決條件

請先確認本機有這些工具：

- Docker 與 Docker Compose
- Node.js 18+
- Java 17+
- Python 3.11+ 或相近版本
- OpenCode Zen API key (for FastAPI) and Ollama (for Spring Boot)

## 1. 啟動基礎服務

專案的 MongoDB 與 MinIO 由 Docker Compose 提供：

```bash
cd /Users/yu-hsin.chen/Documents/projects/fast-minio
docker compose up -d
```

啟動後可檢查：

- MongoDB: `localhost:27017`
- MinIO Console: [http://localhost:9001](http://localhost:9001)
- 預設帳密: `minioadmin / minioadmin`

## 2. 設定 LLM 供應商

### FastAPI: OpenCode Zen

FastAPI 後端使用 OpenCode Zen。啟動前請設定以下環境變數：

```bash
export LLM_BASE_URL=https://opencode.ai/zen/v1
export LLM_MODEL=kimi-k2.7-code
export LLM_API_KEY=your-api-key
```

### Spring Boot: Ollama

Spring Boot 後端仍使用 Ollama。請先確認 Ollama 正在執行，並已下載預設模型 `gemma3:4b`：

```bash
ollama list
ollama pull gemma3:4b
```

如果 Ollama 尚未啟動，可在另一個終端機確認服務可用：

```bash
curl http://localhost:11434/api/tags
```

## 3. 啟動後端

這個專案目前有兩個可選後端，你可以擇一啟動，也可以兩個都啟動後在前端切換。

### 選項 A: FastAPI

```bash
cd /Users/yu-hsin.chen/Documents/projects/fast-minio/fastapi_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

FastAPI 預設設定：

- MongoDB: `mongodb://localhost:27017/chatgpt`
- MinIO bucket: `chatgpt`
- LLM base URL: `https://opencode.ai/zen/v1`
- LLM model: `kimi-k2.7-code`

如果需要自訂，可用環境變數覆蓋：

```bash
export MONGO_URI=mongodb://localhost:27017
export MONGO_DATABASE=chatgpt
export MINIO_ENDPOINT=http://localhost:9000
export MINIO_ACCESS_KEY=minioadmin
export MINIO_SECRET_KEY=minioadmin
export MINIO_BUCKET=chatgpt
export LLM_BASE_URL=https://opencode.ai/zen/v1
export LLM_MODEL=kimi-k2.7-code
export LLM_API_KEY=your-api-key
```

健康檢查：

```bash
curl http://localhost:8000/health
```

### 選項 B: Spring Boot

```bash
cd /Users/yu-hsin.chen/Documents/projects/fast-minio
./mvnw spring-boot:run
```

Spring Boot 預設設定位於 [application.yml](/Users/yu-hsin.chen/Documents/projects/fast-minio/src/main/resources/application.yml)。

健康檢查可先用任一既有 API 驗證，例如：

```bash
curl "http://localhost:8080/api/sessions?userId=u1"
```

## 4. 啟動前端

```bash
cd /Users/yu-hsin.chen/Documents/projects/fast-minio/frontend
npm install
npm run dev
```

啟動後開啟 [http://localhost:3000](http://localhost:3000)。

## 5. 切換後端

前端已支援兩種切換方式。

### 方式 A: 在 UI 直接切換

首頁左上方有 `後端目標` 下拉選單，可以在這兩個後端之間切換：

- `FastAPI`
- `Spring Boot`

切換時前端會清空目前已載入的 sessions 與 messages，避免混用不同後端資料。

### 方式 B: 用環境變數指定預設值

前端支援以下環境變數：

- `NEXT_PUBLIC_DEFAULT_BACKEND=fastapi`
- `NEXT_PUBLIC_FASTAPI_API_BASE=http://localhost:8000`
- `NEXT_PUBLIC_SPRING_API_BASE=http://localhost:8080`

範例設定可參考 [frontend/.env.example](/Users/yu-hsin.chen/Documents/projects/fast-minio/frontend/.env.example)。

如果你想讓前端預設連到 FastAPI，可在前端目錄放入：

```bash
NEXT_PUBLIC_DEFAULT_BACKEND=fastapi
NEXT_PUBLIC_FASTAPI_API_BASE=http://localhost:8000
NEXT_PUBLIC_SPRING_API_BASE=http://localhost:8080
```

如果想預設連到 Spring Boot，改成：

```bash
NEXT_PUBLIC_DEFAULT_BACKEND=spring
NEXT_PUBLIC_FASTAPI_API_BASE=http://localhost:8000
NEXT_PUBLIC_SPRING_API_BASE=http://localhost:8080
```

修改前端環境變數後，請重新啟動 `npm run dev`。

## 6. 建議啟動順序

最穩定的順序如下：

1. 啟動 `docker compose up -d`
2. 確認 LLM 供應商設定：FastAPI 使用 OpenCode Zen API key；Spring Boot 確認 Ollama 可用且模型 `gemma3:4b` 已存在
3. 啟動 `FastAPI` 或 `Spring Boot`
4. 啟動 `frontend`
5. 開啟前端並確認 `後端目標` 是否指向你要的 backend

## 7. 常見問題

### 前端顯示讀取失敗或送出失敗

先檢查：

- 對應後端是否真的啟動
- UI 選到的 backend 是否正確
- 該 backend 的 port 是否和前端設定一致

### 串流 API 報錯

請檢查：

- 若使用 FastAPI：`LLM_BASE_URL`、`LLM_MODEL`、`LLM_API_KEY` 是否正確
- 若使用 Spring Boot：Ollama 是否在 `http://localhost:11434` 且 `gemma3:4b` 是否存在
- session 是否真的存在於目前使用中的 backend

### MinIO 相關錯誤

請確認：

- Docker Compose 已啟動
- `chatgpt` bucket 能由後端自動建立
- `MINIO_ENDPOINT`、帳號密碼與後端設定一致

### MongoDB 相關錯誤

請確認 Docker Compose 的 `mongodb` 容器正常執行：

```bash
docker ps
```

## 8. 相關檔案

- 前端入口: [frontend/app/page.tsx](/Users/yu-hsin.chen/Documents/projects/fast-minio/frontend/app/page.tsx)
- FastAPI 入口: [fastapi_backend/app/main.py](/Users/yu-hsin.chen/Documents/projects/fast-minio/fastapi_backend/app/main.py)
- Spring Boot 設定: [src/main/resources/application.yml](/Users/yu-hsin.chen/Documents/projects/fast-minio/src/main/resources/application.yml)
- Docker Compose: [docker-compose.yml](/Users/yu-hsin.chen/Documents/projects/fast-minio/docker-compose.yml)
