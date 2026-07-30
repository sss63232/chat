# Markdown + KaTeX 渲染設計

日期：2026-07-30
狀態：已確認設計（待實作）

## 目的

讓前端聊天室訊息與獨立測試頁能渲染 Markdown 與 KaTeX 數學公式（inline `$...$` 與 block `$$...$$`）。目前 `frontend/app/page.tsx` 第 418 行以純文字 `<div>{msg.content}</div>` 顯示訊息，完全沒有 Markdown 支援。

## 需求（已與使用者確認）

1. 聊天室訊息改用 Markdown + KaTeX 渲染，**使用者與 AI 助理訊息都渲染**。
2. 新增獨立測試頁 `/markdown-demo`，直接渲染文末「驗收用測試文件」的全文字串，不需要啟動後端就能驗證所有公式。
3. 程式碼區塊加語法高亮，使用 `rehype-highlight`（highlight.js）+ 深色主題，配合聊天室深色 UI。
4. 串流回覆（SSE delta 逐 token 累積）期間不得因不完整的 Markdown / TeX 而 crash。

## 實作路線

採用 **react-markdown 生態系**（方案 A）：

- `react-markdown`（v10 系列）— React 元件化渲染，不用 `dangerouslySetInnerHTML`，預設防 XSS。
- `remark-gfm` — GFM 語法（分隔線、表格、刪除線等）。
- `remark-math` + `rehype-katex` — `$...$` / `$$...$$` 數學語法。
- `rehype-highlight` — 程式碼語法高亮。
- `katex` — 排版引擎與 CSS/字體。

不採用 markdown-it / marked 路線的原因：需要 `dangerouslySetInnerHTML` 或自寫 tokenizer，要自行處理 XSS sanitization，且失去 React 元件模型。

## 架構與元件

### 新增 `frontend/components/markdown-content.tsx`

- `"use client"` 元件，props：`{ content: string }`。
- 內部：`ReactMarkdown`，`remarkPlugins={[remarkGfm, remarkMath]}`，`rehypePlugins={[rehypeKatex, rehypeHighlight]}`。
- `rehype-katex` 選項：`{ throwOnError: false, strict: "ignore" }`。
- 以 `React.memo` 包裝（props 只有 `content`），已完成訊息不因其他 state 變化而重渲染。
- 在此檔案 import `katex/dist/katex.min.css` 與 `highlight.js/styles/github-dark.css`。
- 最外層包一個 `<div className="markdown-body">` 供樣式錨定。

### 修改 `frontend/app/page.tsx`

- 第 418 行 `<div>{msg.content}</div>` 改為 `<MarkdownContent content={msg.content} />`（user / assistant 皆適用）。

### 新增 `frontend/app/markdown-demo/` 測試頁

- `sample.md`：完整存放「驗收用測試文件」原文（見文末）。**不用 TS template literal 存放**，因為文件內含 `` ``` `` 圍欄與大量 LaTeX 反斜線，跳脫會破壞字串。
- `page.tsx`：server component，用 node `fs.readFileSync` 讀取 `sample.md`（`path.join(process.cwd(), "app/markdown-demo/sample.md")`），傳給 `<MarkdownContent>` 渲染。僅作開發/展示用途。

### 修改 `frontend/app/globals.css`

- 新增 `.markdown-body` 區塊樣式：標題間距、清單縮排、引用框、表格、水平線、`pre`/`code` 背景與捲動、`.katex-display` 水平捲動（寬公式如常態分布不撐破訊息框），配色沿用現有 CSS 變數（`--border`、`--accent` 等深色主題）。

## 資料流與串流

- 聊天室：SSE `delta` 事件每收到一個 token 就更新 assistant message `content`，`MarkdownContent` 隨之重渲染。
- remark 對未閉合的 `$$...` 視為純文字，不會拋錯。
- KaTeX 對串流中途的不完整 TeX（例如半個 `\frac`）以紅色原文呈現（`throwOnError: false`），token 補齊後自動正常渲染。
- demo 頁為一次性靜態渲染，無串流議題。

## 錯誤處理

| 情況 | 行為 |
|---|---|
| 不合法 / 不完整 TeX | KaTeX 紅色原文呈現，頁面不 crash |
| 未閉合 `$$` / `$` | 視為純文字顯示 |
| 未知程式語言 code fence | 無高亮，顯示為純文字 code block |
| Markdown 任意輸入 | remark 為 total parser，不拋例外；react-markdown 預設不渲染 raw HTML，無 XSS 面 |

## 驗證方式

前端無測試框架（無 jest/vitest），驗證以 build + 目視為主：

1. `cd frontend && npm install && npm run build` — 型別與 build 必須通過（exit 0）。
2. `npm run dev` 開 `http://localhost:3000/markdown-demo`，逐一目視核對「驗收用測試文件」每個區塊：所有 inline 公式、二次方程式、積分、求和、極限、矩陣、聯立方程、對齊公式、常態分布、boxed 馬克士威方程式、清單/引用/粗斜體/code/`ts` 高亮區塊。
3. （需後端，列為可選）聊天室送出含 `$E=mc^2$` 的訊息，確認串流中不 crash、完成後公式渲染。

## 異動檔案清單

1. `frontend/package.json` — 新增 6 個 dependencies。
2. `frontend/components/markdown-content.tsx` — 新增。
3. `frontend/app/markdown-demo/sample.md` — 新增（驗收文件原文）。
4. `frontend/app/markdown-demo/page.tsx` — 新增。
5. `frontend/app/page.tsx` — 訊息渲染換成 `MarkdownContent`。
6. `frontend/app/globals.css` — 新增 `.markdown-body` 樣式。
7. `frontend/ai/`（currentTask.md、handoff/latest.md、decisions.md）— 依 repo 慣例更新知識庫。

## 範圍外（YAGNI）

- 訊息輸入框的 Markdown 預覽。
- Mermaid / 圖表渲染。
- 後端任何修改。
- 為此功能引入前端測試框架。

## 驗收用測試文件（sample.md 原文）

以下字串必須完整渲染，為本功能的驗收標準：

````markdown
# React Markdown + KaTeX 測試

這是一段普通的 Markdown。

## Inline Math

質能互換公式：

$E = mc^2$

畢氏定理：

$a^2 + b^2 = c^2$

常見函數：

$f(x)=\sin(x)+\cos(x)$

希臘字母：

$\alpha, \beta, \gamma, \Delta, \Omega$

上下標：

$x_i,\quad x^2,\quad x_i^2$

---

## Block Math

### 二次方程式

$$
x=\frac{-b\pm\sqrt{b^2-4ac}}{2a}
$$

### 積分

$$
\int_0^1 x^2\,dx=\frac13
$$

### 求和

$$
\sum_{i=1}^{n} i=\frac{n(n+1)}{2}
$$

### 極限

$$
\lim_{x\to0}\frac{\sin x}{x}=1
$$

### 矩陣

$$
A=
\begin{bmatrix}
1 & 2 \\
3 & 4
\end{bmatrix}
$$

### 聯立方程

$$
\begin{cases}
x+y=3 \\
2x-y=0
\end{cases}
$$

### 對齊公式

$$
\begin{aligned}
f(x)
&= (x+1)^2 \\
&= x^2+2x+1
\end{aligned}
$$

### 常態分布

$$
f(x)=
\frac{1}{\sigma\sqrt{2\pi}}
e^{-\frac{(x-\mu)^2}{2\sigma^2}}
$$

---

## Markdown 混合測試

- 第一項：$a+b$
- 第二項：$\sqrt{x^2+y^2}$
- 第三項：$\int_0^\infty e^{-x}\,dx=1$

> Einstein 提出的著名公式是 $E=mc^2$。

**粗體文字**、*斜體文字*、`code`

```ts
const area = (r: number) => Math.PI * r ** 2;
```

最後再來一個大型公式：

$$
\boxed{
\nabla\cdot\vec{E}
=
\frac{\rho}{\varepsilon_0}
}
$$
````

## As-built 偏差補記（2026-07-30，實作完成後）

以下三點是實作與上文原始設計的差異，均已於 `frontend/ai/decisions.md` 記錄理由，並經 Oracle 審查確認不影響驗收：

1. **KaTeX / highlight.js 的 CSS 改在 `app/layout.tsx` import**（原設計寫在 `markdown-content.tsx`）。原因：`components/` 位於 `app/` 的 global-CSS 邊界之外，且元件保持 CSS-free 才能被 `node:test` + `tsx` 直接 import（tsx 無 CSS loader）。
2. **依賴為 7 個**（原文寫 6 個）：`highlight.js` 需顯式安裝才能 import `github-dark.css` 主題，原先低估一個。
3. **測試腳本與 `tsconfig.test.json`**：「範圍外」原本寫「不為此功能引入前端測試框架」。實際上工作區在本功能前已有 `lib/user-id.test.ts`（未 commit 的先前工作，採 node:test 模式），且 `tsx` 原就在 devDependencies；本次只是補上可執行的 `npm test` script 與 `tsconfig.test.json`（jsx: react-jsx，因 tsx 在 root `jsx: preserve` 下走 classic JSX），並依 ultrawork TDD 要求新增 `components/markdown-content.test.tsx`。未引入 jest/vitest 等新框架。
