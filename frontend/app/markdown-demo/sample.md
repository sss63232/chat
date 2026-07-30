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
