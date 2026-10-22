# Physics recipes — ray optics, Feynman diagrams, vector fields

Read for **physics figures**. All built from core TikZ libraries in
`preamble.tex` (`arrows.meta, decorations.pathmorphing, decorations.markings`).
`tikz-feynman` gives prettier Feynman diagrams but needs `tlmgr install
tikz-feynman` AND LuaLaTeX — the manual recipe below avoids both.

## Contents
- Ray optics (thin lens)
- Feynman diagram (manual: fermion/photon/gluon lines)
- Vector / force field (quiver)

## Ray optics (thin lens)
```latex
\begin{tikzpicture}
\draw[gray] (-5,0) -- (5,0);                              % optical axis
\draw[thick, cbBlue, {Stealth}-{Stealth}] (0,-1.6) -- (0,1.6);  % converging lens
\node at (0,1.8) {lens}; \node at (-3,0)[below] {$f$};
\draw[-{Stealth}, thick] (-4,0) -- (-4,1);                % object
% three principal rays to the image:
\draw[cbOrange] (-4,1) -- (0,1) -- (4,-1);                % parallel -> through F'
\draw[cbOrange] (-4,1) -- (0,0);                          % through centre
\draw[-{Stealth}, thick, red] (4,0) -- (4,-1);            % image
\end{tikzpicture}
```

## Feynman diagram (manual)
Style the line types with decorations; arrows mark fermion flow.
```latex
\tikzset{
  fermion/.style={draw, -{Stealth}, thick},
  photon/.style={draw, decorate, decoration={snake, amplitude=1.2pt, segment length=5pt}},
  gluon/.style={draw, decorate, decoration={coil, amplitude=2pt, segment length=4pt}},
}
\begin{tikzpicture}
  \coordinate (a) at (-2,1.4); \coordinate (b) at (-2,-1.4);
  \coordinate (v1) at (-0.6,0); \coordinate (v2) at (0.9,0);
  \draw[fermion] (a) -- (v1); \draw[fermion] (v1) -- (b);   % incoming e-/e+
  \draw[photon] (v1) -- (v2) node[midway,above]{$\gamma$};   % propagator
  \draw[fermion] (v2) -- (2.3,1.4); \draw[fermion] (2.3,-1.4) -- (v2);
\end{tikzpicture}
```

## Vector / force field (quiver)
Small arrows on a grid; via pgfplots `quiver` or plain TikZ loop.
```latex
% plain TikZ: field F = (-y, x) (rotational)
\foreach \x in {-2,...,2} \foreach \y in {-2,...,2} {
  \draw[-{Stealth}, cbBlue] (\x,\y) -- ++({-\y*0.18},{\x*0.18});
}
% or pgfplots: \addplot3[quiver={u=..., v=...}, -stealth] table {field.csv};
```
