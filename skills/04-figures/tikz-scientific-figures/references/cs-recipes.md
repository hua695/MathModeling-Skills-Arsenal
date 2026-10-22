# CS / ML recipes — neural nets, architecture, automata, trees, graphs

Read for **computer-science / machine-learning figures**. Most use core TikZ
libraries already in `preamble.tex` (`positioning, arrows.meta, fit, calc`). A
couple need an extra library/package noted inline.

## Contents
- System / architecture block diagram
- Neural network (layered nodes)
- Finite state machine / automaton
- Tree (binary tree, syntax tree)
- Graph (nodes + edges)
- UML class / sequence diagram
- ER (entity-relationship) diagram
- Data structures (array, linked list, stack)
- Gantt chart

## System / architecture block diagram
Boxes via `positioning`; group related boxes with `fit`. See also
diagram-recipes.md for feedback loops.
```latex
\tikzset{svc/.style={draw, rounded corners, minimum width=2.2cm, minimum height=9mm, fill=cbBlue!10},
         arr/.style={-{Stealth}}}
\node[svc] (api) {API};
\node[svc, right=14mm of api] (svc) {Service};
\node[svc, right=14mm of svc] (db) {\strut Database};
\draw[arr] (api) -- (svc); \draw[arr] (svc) -- (db);
\begin{scope}[on background layer]
  \node[draw, dashed, fit=(svc)(db), inner sep=4mm, label=above:backend]{};
\end{scope}
```

## Neural network (layered nodes)
Loop over layers; connect every node to the next layer.
```latex
\tikzset{neuron/.style={circle, draw, minimum size=6mm}}
\foreach \l/\n in {0/3, 1/4, 2/2} {            % layer / #neurons
  \foreach \i in {1,...,\n}
    \node[neuron] (n\l-\i) at (\l*2.2, -\i + \n/2) {};
}
\foreach \i in {1,...,3} \foreach \j in {1,...,4} \draw[-{Stealth}] (n0-\i)--(n1-\j);
\foreach \i in {1,...,4} \foreach \j in {1,...,2} \draw[-{Stealth}] (n1-\i)--(n2-\j);
\node[below=2mm] at (0,-2) {input}; \node[below=2mm] at (4.4,-2) {output};
```

## Finite state machine / automaton
Needs `\usetikzlibrary{automata}` (part of PGF — no install).
```latex
\usetikzlibrary{automata, positioning}
\node[state, initial] (q0) {$q_0$};
\node[state, right=of q0] (q1) {$q_1$};
\node[state, accepting, right=of q1] (q2) {$q_2$};
\draw[-{Stealth}] (q0) edge[above] node{a} (q1)
                  (q1) edge[above] node{b} (q2)
                  (q1) edge[loop above] node{a} (q1);
```

## Tree
Easiest with the `forest` package (`tlmgr install forest`):
```latex
\usepackage{forest}
\begin{forest}
  [root [left [a][b]] [right [c]]]
\end{forest}
```
Without forest, use the core `trees` library:
```latex
\usetikzlibrary{trees}
\node {root} child {node {L}} child {node {R}};
```

## Graph (nodes + edges)
```latex
\tikzset{v/.style={circle, draw, fill=gray!10, minimum size=6mm}}
\node[v] (a) at (0,0) {A}; \node[v] (b) at (2,0.6) {B}; \node[v] (c) at (1.4,-1.2) {C};
\draw (a)--(b) (b)--(c) (c)--node[below,font=\tiny]{w=3} (a);   % weighted edge
```

## UML class / sequence diagram
Class box = 3 stacked compartments (name / attributes / methods).
```latex
\node[draw, rectangle split, rectangle split parts=3, align=left] {
  \textbf{Account} \nodepart{second} - balance: float \nodepart{third} + deposit()};
% needs \usetikzlibrary{shapes.multipart}
```
Sequence: vertical lifelines + horizontal message arrows.
```latex
\foreach \x/\n in {0/User, 3/System} {
  \node (\n) at (\x,0) {\n}; \draw[dashed] (\x,-0.3)--(\x,-4); }   % lifelines
\draw[-{Stealth}] (0,-1) -- node[above,font=\tiny]{request} (3,-1);
\draw[-{Stealth}, dashed] (3,-2) -- node[above,font=\tiny]{response} (0,-2);
```

## ER (entity-relationship) diagram
Entity = rectangle, relationship = diamond, attribute = ellipse.
```latex
\tikzset{ent/.style={draw, minimum width=2cm, minimum height=8mm},
         rel/.style={draw, diamond, aspect=2, inner sep=1pt}}
\node[ent] (u) {User}; \node[rel, right=2cm of u] (p) {places}; \node[ent, right=2cm of p] (o) {Order};
\draw (u)--node[above,font=\tiny]{1}(p); \draw (p)--node[above,font=\tiny]{N}(o);
```

## Data structures (array / linked list / stack)
```latex
% array: a row of cells
\foreach \i/\v in {0/3,1/1,2/4,3/1,4/5} {
  \node[draw, minimum size=7mm] (c\i) at (\i*0.72,0) {\v};
  \node[font=\tiny, below=0pt of c\i] {\i};        % index
}
% linked list: nodes + next pointers
\foreach \i/\v in {0/A,1/B,2/C} \node[draw, minimum size=7mm] (n\i) at (\i*1.6,-2) {\v};
\foreach \i [evaluate=\i as \j using int(\i+1)] in {0,1}
  \draw[-{Stealth}] (n\i.east) -- (n\j.west);
```

## Gantt chart
Cleanest with `pgfgantt` (`tlmgr install pgfgantt`):
```latex
\usepackage{pgfgantt}
\begin{ganttchart}[hgrid, vgrid]{1}{12}
  \gantttitle{2026}{12} \\ \gantttitlelist{1,...,12}{1} \\
  \ganttbar{Design}{1}{3} \\ \ganttbar{Build}{3}{8} \\ \ganttbar{Write-up}{8}{12}
\end{ganttchart}
```
Without pgfgantt: draw bars as `\fill` rectangles on a manual time axis.
