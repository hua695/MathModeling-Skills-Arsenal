# circuitikz recipes — schematic / circuit diagrams

Read when the figure is an **electrical circuit**. Needs `\usepackage{circuitikz}`
(add to preamble for this figure). Draw inside `\begin{circuitikz}...\end{circuitikz}`.

## Contents
- Basic grammar (to[component] between coordinates)
- Common components
- RC / RLC example
- Op-amp
- Labels & current arrows

## Basic grammar
Components are placed `to[...]` along a path between two coordinates:
```latex
\begin{circuitikz}
  \draw (0,0) to[R, l=$R_1$] (2,0)      % resistor labelled R_1
              to[C, l=$C_1$] (2,-2)      % capacitor going down
              to[battery1, l=$V$] (0,-2) % source
              -- (0,0);                   % close the loop
\end{circuitikz}
```

## Common components (the `to[X]` key)
| key | part | key | part |
|-----|------|-----|------|
| `R` | resistor | `L` | inductor |
| `C` | capacitor | `D` | diode |
| `battery1`/`V` | source | `I` | current source |
| `switch` | switch | `short` | wire |
| `ground` (node) | ground | `op amp` | op-amp |

## Labels, values, current
```latex
to[R, l=$R_1$, a=$1\,\si{\kilo\ohm}$, i=$i_1$, v=$v_R$] % l label · a annotation · i current · v voltage
```

## Op-amp
```latex
\draw (0,0) node[op amp] (oa) {};
\draw (oa.-) -- ++(-1,0); \draw (oa.+) -- ++(-1,0);
\draw (oa.out) -- ++(1,0);
```

## Ground node
```latex
\draw (0,-2) node[ground]{};
```
