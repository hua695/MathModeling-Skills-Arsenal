# Runtime modes and stage state

`AUTO` may make routine reversible decisions and must stop on an emergency condition. `COLLAB` asks for user confirmation before changing architecture, parameters, or final wording. `LOCK` only recommends changes after the freeze threshold and never silently changes frozen numbers.

Stages are ordered: `A understand → B plan/baseline → C solve/figures → D write → E critic → F delivery → G replay`. A stage cannot be entered without its checkpoint artifacts. A failed gate returns to the owning stage; it is never skipped.
