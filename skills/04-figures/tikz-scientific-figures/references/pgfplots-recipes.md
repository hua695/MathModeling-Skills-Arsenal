# PGFPlots recipes — publication data plots

Read when the figure is a **data plot**. Snippets go inside `\begin{axis}...\end{axis}`
unless noted. Colours/markers come from the `cbcycle` list in `preamble.tex` —
do not hard-code red/green. For multi-panel layout, significance markers, fit
bands and insets see `figure-composition.md`.

## Contents
- Line / multi-series
- Scatter
- Error bars
- Bar chart (simple / grouped / stacked)
- Histogram
- Box plot / violin
- Log axis
- Heatmap (matrix) / contour
- 3D surface & scatter
- Reading data from CSV

## Line / multi-series
```latex
\addplot table[x=t, y=v1, col sep=comma] {data.csv}; \addlegendentry{series 1}
\addplot table[x=t, y=v2, col sep=comma] {data.csv}; \addlegendentry{series 2}
```
`data.csv` first row = column names (`t,v1,v2`). Editing the plot = editing the CSV.

## Scatter (no connecting line)
```latex
\addplot[only marks, mark=*, mark size=1.2pt] table[x=x, y=y] {data.csv};
```

## Error bars
```latex
\addplot+[error bars/.cd, y dir=both, y explicit]
  table[x=x, y=y, y error=err] {data.csv};
```
Always note in the caption whether bars are SD, SE, or 95% CI.

## Bar chart
```latex
% simple
\begin{axis}[ybar, bar width=6pt, ymin=0, symbolic x coords={A,B,C}, xtick=data]
  \addplot coordinates {(A,3) (B,5) (C,2)};
\end{axis}
% grouped: several \addplot in one ybar axis
% stacked: use  ybar stacked  instead of  ybar
\begin{axis}[ybar stacked, ymin=0, symbolic x coords={A,B,C}, xtick=data]
  \addplot coordinates {(A,2)(B,3)(C,1)}; \addplot coordinates {(A,1)(B,2)(C,4)};
\end{axis}
```

## Histogram
```latex
\begin{axis}[ymin=0, ylabel={count}]
  \addplot+[hist={bins=12}, fill=cbBlue!40] table[y index=0] {samples.csv};
\end{axis}
```

## Box plot / violin
Needs `\usepgfplotslibrary{statistics}` (bundled with pgfplots).
```latex
\usepgfplotslibrary{statistics}
\begin{axis}[boxplot/draw direction=y, xtick={1,2}, xticklabels={ctrl,treat}]
  \addplot+[boxplot] table[row sep=\\, y index=0] {3\\5\\6\\6\\7\\8\\12\\};
  \addplot+[boxplot] table[row sep=\\, y index=0] {5\\7\\8\\9\\9\\11\\14\\};
\end{axis}
```
Violin: there is no built-in; approximate with a symmetric `\addplot fill` of a
kernel-density curve, or note it needs an external estimate.

## Log axis
```latex
\begin{semilogyaxis}[...] ... \end{semilogyaxis}   % or loglogaxis / semilogxaxis
```

## Heatmap (matrix) / contour
```latex
\begin{axis}[colorbar, colormap/viridis]   % viridis = perceptually uniform
  \addplot[matrix plot, point meta=explicit] table[meta=z] {grid.csv};
\end{axis}
% filled contour from prepared data:
\addplot[contour prepared] table {contour.dat};
```

## 3D surface & scatter
```latex
\begin{axis}[view={60}{30}, colormap/viridis]
  \addplot3[surf] {sin(deg(x))*cos(deg(y))};          % surface from expression
  % \addplot3[only marks] table {xyz.csv};            % 3D scatter
\end{axis}
```
