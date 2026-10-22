# Biology recipes — cells, tissue/IF schematics, pathways, gene maps

Read for **biology figures**. TikZ has no biology package per se — these are
built from core shapes + shadings (already loaded in `preamble.tex`). For
molecules use `chemfig`. For glowing immunofluorescence (IF) use radial shadings
on a black background.

## Contents
- Immunofluorescence (IF) tissue schematic
- Cell with organelles
- Signaling / regulatory pathway (activation + inhibition arrows)
- Circular gene / plasmid map
- Molecules (chemfig)

## Immunofluorescence (IF) tissue schematic
Black background + radial-shaded "glowing" regions reads as fluorescence.
Use distinguishable channels (green / magenta / cyan / yellow), NOT red+green.
```latex
\usetikzlibrary{shadings}
\definecolor{chA}{RGB}{0,220,80}     % e.g. B220 green
\definecolor{chB}{RGB}{230,40,200}   % e.g. CD3 magenta
\fill[black] (-6,-4) rectangle (6,4);                       % IF black field
\shade[shading=radial, inner color=chA, outer color=chA!10!black]
  (-0.7,0.5) circle (1.4);                                  % glowing region
\shade[shading=radial, inner color=black, outer color=cyan!85!black]
  (0,0) circle (2.6);                                       % ring: shade then carve
\fill[black] (0,0) circle (2.3);
% white leader lines + \textcolor{chA}{marker} labels; add a scale bar:
\draw[white, line width=1.2pt] (-5.6,-3.6) -- (-4.1,-3.6)
  node[midway, above, white, font=\scriptsize]{200\,\textmu m};
```

## Cell with organelles
Membrane = rounded blob; organelles = shapes with fills.
```latex
\filldraw[rounded corners=20pt, fill=blue!8, draw=blue!50]
  (0,0) ellipse (3 and 2);                       % cell membrane
\filldraw[fill=purple!25, draw=purple] (0.3,0.2) circle (0.9)
  node{\footnotesize nucleus};
\filldraw[fill=orange!30, draw=orange] (-1.6,-0.6) ellipse (0.5 and 0.28)
  node[font=\tiny]{mito};                          % mitochondrion
```

## Signaling / regulatory pathway
Activation = arrowhead; inhibition = bar (`-|`). Lay out with `positioning`.
```latex
\tikzset{
  gene/.style={draw, rounded corners, fill=gray!8, minimum height=7mm},
  act/.style={-{Stealth}}, inh/.style={-{Bar}},
}
\node[gene] (a) {Receptor};
\node[gene, right=15mm of a] (b) {Kinase};
\node[gene, right=15mm of b] (c) {TF};
\draw[act] (a) -- (b);             % activates
\draw[inh] (b) -- node[above,font=\tiny]{inhibits} (c);
```

## Circular gene / plasmid map
Backbone = circle; features = thick colored arcs (direction = gene orientation).
```latex
\draw[gray, line width=1pt] (0,0) circle (2);                 % backbone
\draw[cbBlue, line width=6pt] (0,0) ++(30:2) arc (30:120:2);  % feature arc
\node at (75:2.6) {\footnotesize \textit{gene A}};
\node[font=\scriptsize] at (0,0) {pXYZ\\5.2 kb};
```

## Molecules
```latex
\usepackage{chemfig}
\chemfig{H-C(-[2]H)(-[6]H)-O-H}     % or SMILES-like manual bonds
```
