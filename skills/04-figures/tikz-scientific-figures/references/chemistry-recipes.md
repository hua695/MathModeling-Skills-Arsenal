# Chemistry recipes — molecules, reactions, energy diagrams, lattices

Read for **chemistry figures**. Molecules use `chemfig` (installed). Reaction
schemes, energy profiles and lattices are plain TikZ. `mhchem` (`\ce{...}`) is
nicer for inline formulas but needs `tlmgr install mhchem`.

## Contents
- Molecule (chemfig)
- Reaction scheme (arrows + conditions)
- Reaction-coordinate / energy profile
- Crystal lattice (2D / pseudo-3D)

## Molecule (chemfig)
```latex
\usepackage{chemfig}
\chemfig{*6(=-=-=-)}                       % benzene ring
\chemfig{H_3C-[:30]C(=[:90]O)-[:-30]OH}    % acetic acid (angles in [: deg])
```

## Reaction scheme
Reagents over the arrow, conditions under it.
```latex
\usepackage{chemfig}
\schemestart
  \chemfig{*6(=-=-=-)}
  \arrow{->[\footnotesize $\mathrm{Br_2}$][\footnotesize FeBr$_3$]}
  \chemfig{*6(=-=-(-Br)=-)}
\schemestop
```

## Reaction-coordinate / energy profile
Plain TikZ smooth curve with labelled states + Ea/ΔH arrows.
```latex
\begin{tikzpicture}
\draw[->] (0,0) -- (0,4) node[above]{Energy};
\draw[->] (0,0) -- (8,0) node[right]{reaction coordinate};
\draw[thick, cbBlue] (0.5,1) .. controls (2.5,1) and (2.5,3.4) .. (4,3.4) % to TS
                     .. controls (5.5,3.4) and (5.5,0.6) .. (7.5,0.6);     % to product
\node[left] at (0.5,1) {reactants};  \node[above] at (4,3.4) {TS};
\node[right] at (7.5,0.6) {products};
\draw[<->] (4,1) -- (4,3.3) node[midway,right]{$E_a$};       % activation energy
\draw[<->] (7.7,1) -- (7.7,0.65) node[midway,right]{$\Delta H$};
```

## Crystal lattice
2D lattice: loop atoms on a grid. Pseudo-3D: use `tikz-3dplot` (tlmgr install
tikz-3dplot) or skewed coordinates.
```latex
\foreach \x in {0,1,2} \foreach \y in {0,1,2} {
  \filldraw[cbBlue] (\x,\y) circle (3pt);
  \ifnum\x<2 \draw[gray] (\x,\y)--(\x+1,\y); \fi
  \ifnum\y<2 \draw[gray] (\x,\y)--(\x,\y+1); \fi
}
```
