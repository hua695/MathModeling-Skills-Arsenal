# Figure composition — multi-panel, insets, significance, fits, image overlay

Read when assembling a **paper-grade composite figure**: several panels, an
inset, significance brackets, a fitted curve with confidence band, or labelling a
real microscopy/photo image. All use libraries in `preamble.tex` plus the ones
noted.

## Contents
- Multi-panel (a)(b)(c) with groupplots
- Inset / zoom
- Significance brackets and stars (* / ** / p-value)
- Fitted curve + confidence band
- Annotating a raster image (scale bar, arrows, panel labels)

## Multi-panel (a)(b)(c)
```latex
\usepgfplotslibrary{groupplots}
\begin{groupplot}[group style={group size=2 by 1, horizontal sep=1.4cm},
                  width=6cm, height=4.5cm]
  \nextgroupplot[title={(a)}] \addplot table {a.csv};
  \nextgroupplot[title={(b)}] \addplot table {b.csv};
\end{groupplot}
```
For panels of mixed type (plot + schematic + image), instead place each in its own
`tikzpicture`/`\includegraphics` and tile with a `matrix` or `subcaption`-style
nodes; label each with `\node[anchor=north west] at (panel.north west) {(a)};`.

## Inset / zoom
```latex
\usetikzlibrary{spy}
\begin{tikzpicture}[spy using outlines={rectangle, magnification=3, size=2cm, connect spies}]
  \begin{axis}[name=main] \addplot {x^2}; \end{axis}
  \spy[blue] on (2,1.2) in node at (4.5,3);   % magnified callout
\end{tikzpicture}
```
Or draw a small second `axis` with `at={(main.south east)}` and a restricted domain.

## Significance brackets and stars
Manual, robust, works on any axis. Place in `axis cs:` coordinates.
```latex
% inside the axis, after the data:
\draw (axis cs:1,9) -- (axis cs:1,9.5) -- (axis cs:2,9.5) -- (axis cs:2,9)
  node[midway, above, yshift=2pt, font=\footnotesize] {$\ast\ast$};   % ** p<0.01
% legend of convention in caption: * p<0.05, ** p<0.01, *** p<0.001
```

## Fitted curve + confidence band
`fill between` (bundled with pgfplots) shades between an upper and lower path.
```latex
\usepgfplotslibrary{fillbetween}
\addplot[name path=hi, draw=none] table[x=x, y=upper] {fit.csv};
\addplot[name path=lo, draw=none] table[x=x, y=lower] {fit.csv};
\addplot[cbBlue!20] fill between[of=hi and lo];     % 95% CI band
\addplot[cbBlue, thick] table[x=x, y=fit] {fit.csv}; % fitted line
\addplot[only marks, mark size=1pt] table[x=x, y=y] {fit.csv}; % raw points
```

## Annotating a raster image (microscopy / fluorescence / photo)
Overlay TikZ on a real image — scale bar, arrows, ROI boxes, panel labels.
Use a normalised coordinate system so annotations stay put if the image scales.
```latex
\begin{tikzpicture}
  % image fills a node; x=image width, set its on-page width:
  \node[anchor=south west, inner sep=0] (img) at (0,0)
    {\includegraphics[width=6cm]{cells.png}};
  % overlay layer with 0..1 coordinates over the image:
  \begin{scope}[x={(img.south east)}, y={(img.north west)}]
    \draw[white, line width=1.5pt] (0.05,0.06) -- (0.27,0.06)         % scale bar
      node[midway, above, white, font=\scriptsize]{20\,\textmu m};
    \draw[-{Stealth}, yellow, thick] (0.7,0.8) -- (0.55,0.62);        % arrow to feature
    \node[draw=cyan, thick, minimum width=1.2cm, minimum height=1cm] at (0.4,0.4){}; % ROI
    \node[white, font=\bfseries, anchor=north west] at (0.02,0.98){(a)}; % panel label
  \end{scope}
\end{tikzpicture}
```
Keeping the image as `\includegraphics` (not redrawn) means the data pixels stay
authentic and only the annotations are vector — the correct way to label real data.
