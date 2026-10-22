# Math recipes — commutative diagrams, Venn, number line

Read for **math figures**. Venn and number lines are core TikZ. Commutative
diagrams are cleanest with `tikz-cd` (`tlmgr install tikz-cd`); a core-TikZ
`matrix` fallback is given for when it is not installed.

## Contents
- Commutative diagram (tikz-cd + core fallback)
- Venn diagram
- Number line / interval

## Commutative diagram
Preferred (`tikz-cd`):
```latex
\usepackage{tikz-cd}
\begin{tikzcd}
  A \arrow[r, "f"] \arrow[d, "g"'] & B \arrow[d, "h"] \\
  C \arrow[r, "k"']               & D
\end{tikzcd}
```
Core fallback (no extra package):
```latex
\usetikzlibrary{matrix, arrows.meta}
\begin{tikzpicture}
\matrix (m) [matrix of math nodes, row sep=1.2cm, column sep=1.2cm]
  { A & B \\ C & D \\ };
\draw[-{Stealth}] (m-1-1)--(m-1-2) node[midway,above]{$f$};
\draw[-{Stealth}] (m-1-1)--(m-2-1) node[midway,left]{$g$};
\draw[-{Stealth}] (m-1-2)--(m-2-2) node[midway,right]{$h$};
\draw[-{Stealth}] (m-2-1)--(m-2-2) node[midway,below]{$k$};
\end{tikzpicture}
```

## Venn diagram
```latex
\begin{tikzpicture}
\fill[cbBlue, opacity=0.4] (-0.6,0) circle (1.2);
\fill[cbOrange, opacity=0.4] (0.6,0) circle (1.2);
\node at (-1.1,0){$A$}; \node at (1.1,0){$B$}; \node at (0,0){$A\cap B$};
\draw (-0.6,0) circle (1.2); \draw (0.6,0) circle (1.2);
\end{tikzpicture}
```

## Number line / interval
```latex
\begin{tikzpicture}
\draw[-{Stealth}] (-3.3,0) -- (3.3,0);
\foreach \x in {-3,...,3} \draw (\x,0.08)--(\x,-0.08) node[below]{$\x$};
\draw[ultra thick, cbBlue] (-1,0) -- (2,0);            % interval [-1,2]
\filldraw[cbBlue] (-1,0) circle (2.5pt);               % closed endpoint
\draw[cbBlue, fill=white, thick] (2,0) circle (2.5pt); % open endpoint
\end{tikzpicture}
```
