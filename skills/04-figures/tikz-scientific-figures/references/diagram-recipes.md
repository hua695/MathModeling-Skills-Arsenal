# Diagram recipes — flowcharts, block diagrams, physics schematics

Read for **non-circuit schematics**: flowcharts, system/block diagrams,
free-body / force diagrams, geometry. Uses libraries already in `preamble.tex`
(`positioning, arrows.meta, shapes.geometric, calc, angles, decorations`).

## Contents
- Flowchart (nodes + relative positioning)
- Block diagram (signal flow)
- Free-body / force diagram
- Angle & geometry annotation
- Braces / dimension markers

## Flowchart
Define reusable node styles, then place with `positioning` (`right=of`, `below=of`)
instead of absolute coordinates — auto-layout survives edits.
```latex
\tikzset{
  box/.style={draw, rounded corners, minimum width=2cm, minimum height=0.8cm, align=center},
  arr/.style={-{Stealth[length=2mm]}},
}
\begin{tikzpicture}[node distance=8mm]
  \node[box] (a) {Input};
  \node[box, below=of a] (b) {Process};
  \node[box, below=of b] (c) {Output};
  \draw[arr] (a) -- (b); \draw[arr] (b) -- (c);
\end{tikzpicture}
```

## Block diagram with feedback
```latex
\node[box] (sum) {$\Sigma$};
\node[box, right=of sum] (plant) {$G(s)$};
\draw[arr] (sum) -- (plant);
\draw[arr] (plant.east) -- ++(1,0) |- (sum.south);  % feedback path
```

## Free-body / force diagram
```latex
\filldraw (0,0) circle (2pt) node (m) {};         % the body
\draw[-{Stealth}] (m) -- ++(0,-1.5) node[below]{$mg$};
\draw[-{Stealth}] (m) -- ++(1.5,0)  node[right]{$F$};
\draw[-{Stealth}] (m) -- ++(0,1.5)  node[above]{$N$};
```

## Angle annotation
```latex
\usetikzlibrary{angles, quotes}   % already loaded
\coordinate (A) at (2,0); \coordinate (O) at (0,0); \coordinate (B) at (1.5,1.5);
\draw (A)--(O)--(B);
\pic[draw, "$\theta$", angle radius=6mm] {angle=A--O--B};
```

## Dimension brace
```latex
\draw[decorate, decoration={brace, amplitude=4pt}] (0,0) -- (3,0)
  node[midway, below=4pt]{width};
```
