# Code Review: MCP Server 新增變更

> **日期**: 2026-07-11
> **範圍**: `fastapi_backend/` 中新增的 MCP Server 相關檔案
> **審查者**: Sisyphus

---

## 目錄

1. [變更概述](#1-變更概述)
2. [Bug 等級](#2-bug-等級)
   - [2.1 `pytest-asyncio` 未加入 `requirements.txt`](#21-pytest-asyncio-未加入-requirementstxt)
   - [2.2 SSE parser 會丟棄多行 `data:` 欄位](#22-sse-parser-會丟棄多行-data-欄位)
   - [2.3 `send_message` 異常處理未排除 `ToolError`](#23-send_message-異常處理未排除-toolerror)
3. [問題與不一致](#3-問題與不一致)
   - [3.1 `list_sessions` 缺少輸入驗證](#31-list_sessions-缺少輸入驗證)
   - [3.2 Dockerfile.mcp 中 `COPY` 指令重複](#32-dockerfilemcp-中-copy-指令重複)
   - [3.3 測試輔助函式 `_call_tool` 回傳型別有誤](#33-測試輔助函式-_call_tool-回傳型別有誤)
   - [3.4 `services_available` 過度跳過純驗證測試](#34-services_available-過度跳過純驗證測試)
4. [程式碼風格](#4-程式碼風格)
   - [4.1 棄用的 `asyncio.get_event_loop()`](#41-棄用的-asyncioget_event_loop)
5. [總結與建議優先級](#5-總結與建議優先級)

---

## 1. 變更概述

此 Changeset 為聊天應用的 FastAPI 後端新增一個**獨立的 MCP (Model Context Protocol) 伺服器**，使 AI Agent（Claude Code / Desktop 等）可透過 Streamable HTTP transport 直接操作聊天 Session、訊息與背景任務。

### 新增檔案

| 檔案 | 說明 |
|------|------|
| `fastapi_backend/mcp_server/server.py` (653 行) | MCP 伺服器本體 - 工具、資源、生命週期、Middleware |
| `fastapi_backend/mcp_server/README.md` (176 行) | 部署與使用文件 |
| `fastapi_backend/mcp_server/__init__.py` | Package init |
| `fastapi_backend/Dockerfile.mcp` (32 行) | 獨立容器映像建置檔 |
| `fastapi_backend/pytest.ini` (3 行) | Pytest 設定 (`asyncio_mode = auto`) |
| `fastapi_backend/tests/conftest.py` (48 行) | 測試共用 Fixture |
| `fastapi_backend/tests/test_mcp_tools.py` (243 行) | MCP 工具整合測試 |
| `fastapi_backend/scripts/test_mcp.sh` | 快速測試腳本 |

### 修改檔案

| 檔案 | 異動 |
|------|------|
| `fastapi_backend/requirements.txt` | 新增 `fastmcp>=2.0,<3.0` + `starlette` 版本固定 |

---

## 2. Bug 等級

### 2.1 `pytest-asyncio` 未加入 `requirements.txt`

**嚴重度**: ⚠️ Medium

**檔案**: `fastapi_backend/pytest.ini`, `fastapi_backend/tests/test_mcp_tools.py`

**說明**: `pytest.ini` 設定 `asyncio_mode = auto`，測試檔案也大量使用 `async def` 測試方法。此為 `pytest-asyncio` 套件的設定選項，但 `requirements.txt` 中並未包含 `pytest-asyncio`。

在乾淨環境執行 `pip install -r requirements.txt` 後，pytest 會忽略 `asyncio_mode` 設定，且 async 測試方法會產生 `coroutine was never awaited` 錯誤或直接跳過。

此外，`conftest.py` 中定義了 `anyio_backend` fixture，暗示測試原始設計也預期 `anyio` / `pytest-anyio` 支援，同樣未列於相依套件中。

**建議**:
```txt
# requirements.txt
pytest-asyncio>=0.24,<1.0
# 或若需 anyio fixture 支援:
# pytest-anyio>=0.1,<1.0
```

---

### 2.2 SSE parser 會丟棄多行 `data:` 欄位

**嚴重度**: 🔴 Latent — 目前不會觸發，但若 payload 格式改變則會靜默產出損壞資料

**檔案**: `fastapi_backend/mcp_server/server.py:279-296`

**說明**: `_consume_sse_stream()` 在解析 SSE 事件時，對於每個 `data:` 行**直接覆寫** `data_str` 變數，而非累加：

```python
# 現有實作 (L284-288)
for line in lines:
    if line.startswith("event: "):
        evt = line[7:]
    elif line.startswith("data: "):
        data_str = line[6:]   # ← 覆寫而非累加
```

後端的 `format_sse()`（定義於 `app/services/chat.py`）為了符合 SSE 規範，當 payload 含有換行時會將其拆分為多個 `data:` 行。例如：

```
event: done
data: {"key": "line1
data: line2"}
```

以目前實作，`data_str` 最終只會拿到 `"line2"}`，JSON 解析會失敗。

**目前安全的原因**: `model_dump_json()` 和 `json.dumps()` 預設產生單行 compact JSON，故此 bug 尚未被觸發。但這是脆弱的假設。

**建議**: 改為累加後以換行符號合併：

```python
data_lines: list[str] = []
for line in lines:
    if line.startswith("event: "):
        evt = line[7:]
    elif line.startswith("data: "):
        data_lines.append(line[6:])
data_str = "\n".join(data_lines)
```

---

### 2.3 `send_message` 異常處理未排除 `ToolError`

**嚴重度**: 🟡 Low — 目前未觸發，但與 `send_message_streaming` 不一致

**檔案**: `fastapi_backend/mcp_server/server.py:396-404`

**說明**: `send_message_streaming` (L449) 正確地先 re-raise `ToolError`：

```python
except ToolError:
    raise
except Exception as exc:
    raise _to_tool_error(exc)
```

但 `send_message` (L401-404) 沒有：

```python
except HTTPException as exc:
    raise _to_tool_error(exc)
except Exception as exc:
    raise _to_tool_error(exc)     # ← 若拋出 ToolError 會被雙層包裝
```

若未來任何程式路徑在 `try` 區塊內拋出 `ToolError`，它會被 `_to_tool_error()` 再包一層，產生誤導性錯誤訊息。

**建議**: 在泛用 `except Exception` 前加入 `except ToolError: raise`。

---

## 3. 問題與不一致

### 3.1 `list_sessions` 缺少輸入驗證

**嚴重度**: 🟡 Low

**檔案**: `fastapi_backend/mcp_server/server.py:215-230`

**說明**: 所有其他工具 (`create_session`, `send_message`, `get_task_status` 等) 都會對必要字串參數進行 `if not x.strip(): raise ToolError(...)` 驗證。但 `list_sessions` resource 直接將 `user_id` 傳入資料庫查詢：

```python
async def list_sessions(user_id: str) -> str:
    _ = await authenticate()
    try:
        database = get_database()
        sessions = await get_sessions_by_user(database, user_id)
        ...
```

Agent 傳入空字串時，MongoDB 會回傳空陣列而非明確錯誤。

**建議**: 比照 `list_messages` 加入驗證：

```python
if not user_id.strip():
    raise ToolError("user_id 不能為空白")
```

### 3.2 Dockerfile.mcp 中 `COPY` 指令重複

**嚴重度**: 🟢 Cosmetic

**檔案**: `fastapi_backend/Dockerfile.mcp:24-25`

```dockerfile
COPY fastapi_backend/ .               # ← 已包含 mcp_server/
COPY fastapi_backend/mcp_server/ ./mcp_server/   # ← 多餘
```

第一行 `COPY fastapi_backend/ .` 已將整個 `fastapi_backend/` 目錄樹（包含 `mcp_server/`）複製進 `/app/`。第二行是無作用的疊加，僅增加一層不必要的 image layer。

**建議**: 移除第 25 行。

### 3.3 測試輔助函式 `_call_tool` 回傳型別有誤

**嚴重度**: 🟢 Cosmetic

**檔案**: `fastapi_backend/tests/test_mcp_tools.py:219`

```python
async def _call_tool(tool_name: str, arguments: dict) -> dict:
```

當 response body 不是合法 JSON 時，函式在第 243 行回傳原始 `body`（型別為 `str`），與型別標註 `-> dict` 不一致。

**建議**: 修正型別標註為 `dict | str`，或直接讓非 JSON 回傳拋錯。

### 3.4 `services_available` 過度跳過純驗證測試

**嚴重度**: 🟡 Low

**檔案**: `fastapi_backend/tests/conftest.py:39-43`

```python
services_available = pytest.mark.skipif(
    not (_mongodb_reachable() and _ollama_reachable()),
    reason="MongoDB and/or Ollama are not running locally. ...",
)
```

此 marker 同時要求 MongoDB 與 Ollama 皆可連線。然而 `test_empty_user_id_returns_error`、`test_empty_content_returns_error` 等測試**僅驗證輸入驗證邏輯**——它們在存取資料庫或 Ollama 之前就會拋出 `ToolError`。

即使兩個服務都未啟動，這些測試仍應可通過，但被不合理地跳過了。

**建議**: 考慮拆分 marker：`mongo_available` 用於需要 MongoDB 的測試、`services_available` 用於需要全套服務的測試；或直接從純驗證測試移除 decorator。

---

## 4. 程式碼風格

### 4.1 棄用的 `asyncio.get_event_loop()`

**嚴重度**: 🟢 Cosmetic

**檔案**: `fastapi_backend/mcp_server/server.py:532,538,583,589`

```python
deadline = asyncio.get_event_loop().time() + timeout_seconds
```

四個呼叫點都在 `async` 函式內，執行中的 event loop 必然存在。`asyncio.get_event_loop()` 自 Python 3.10 起在無法明確判定 loop 的情境已被標記為 deprecated。Dockerfile 使用 `python:3.12-slim`，建議改為：

```python
deadline = asyncio.get_running_loop().time() + timeout_seconds
```

---

## 5. 總結與建議優先級

| 優先級 | 類別 | 項目 | 檔案 | 影響 |
|--------|------|------|------|------|
| **High** | Bug | `pytest-asyncio` 未加入 `requirements.txt` | `requirements.txt` | 測試無法在乾淨環境執行 |
| **Medium** | Bug (Latent) | SSE parser 丟棄多行 data | `server.py:279-296` | 非 compact JSON 時靜默損壞資料 |
| **Medium** | Bug | `send_message` 未排除 `ToolError` | `server.py:401-404` | 潛在異常雙層包裝 |
| **Low** | 不一致 | `list_sessions` 缺少輸入驗證 | `server.py:215-230` | 空字串無錯誤提示 |
| **Low** | 測試 | `services_available` 過度跳過 | `tests/conftest.py:39-43` | 純驗證測試被不合理跳過 |
| **Low** | 測試 | `_call_tool` 回傳型別不一致 | `tests/test_mcp_tools.py:219` | Linter 警告 |
| **Cosmetic** | Docker | 重複 `COPY` 指令 | `Dockerfile.mcp:25` | 不必要的 image layer |
| **Cosmetic** | 風格 | 棄用的 `get_event_loop()` | `server.py:532,538,583,589` | 無實際影響 |

### 需要立即處理的項目

1. **將 `pytest-asyncio` 加入 `requirements.txt`** — 否則測試基礎流程無法運作。
2. **修正 SSE parser 的 `data` 行累加邏輯** — 避免未來非 compact JSON 格式時靜默損壞。

其餘為低優先級的一致性與風格改進。
