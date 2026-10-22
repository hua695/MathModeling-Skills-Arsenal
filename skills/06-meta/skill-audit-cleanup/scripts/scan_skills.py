import os, re, json, glob, time, io, sys

roots = {
  "user": r"C:/Users/USER/.workbuddy/skills",
  "claude": r"C:/Users/USER/.claude/skills",
  "plugin_cache": r"C:/Users/USER/.workbuddy/plugins/cache",
  "connector": r"C:/Users/USER/.workbuddy/connectors/skills",
  "marketplace": r"C:/Users/USER/.workbuddy/plugins/marketplaces",
}

def parse_front(p):
    try:
        t = io.open(p, encoding="utf-8", errors="replace").read(4000)
    except Exception:
        return {}
    m = re.match(r"^---\s*\n(.*?)\n---", t, re.S)
    if not m: return {}
    fm = m.group(1)
    d = {}
    for line in fm.splitlines():
        mm = re.match(r"^([A-Za-z_\-]+):\s*(.*)$", line)
        if mm:
            d[mm.group(1)] = mm.group(2).strip().strip('"').strip("'")
    return d

out = []
for scope, root in roots.items():
    if not os.path.isdir(root): continue
    for dirpath, dirnames, filenames in os.walk(root):
        if "SKILL.md" not in filenames: continue
        p = os.path.join(dirpath, "SKILL.md")
        fm = parse_front(p)
        st = os.stat(p)
        # skill folder name = dirpath basename (or parent if dir is 'skills')
        rel = os.path.relpath(dirpath, root)
        out.append({
            "scope": scope,
            "folder": os.path.basename(dirpath),
            "rel": rel.replace("\\","/"),
            "name": fm.get("name",""),
            "desc": (fm.get("description","") or "").replace("\n"," ")[:300],
            "version": fm.get("version",""),
            "agent_created": fm.get("agent_created",""),
            "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)),
            "size_kb": round(sum(os.path.getsize(os.path.join(dirpath,f)) for f in filenames)/1024,1),
            "nfiles": len(filenames),
            "path": p.replace("\\","/"),
        })

out.sort(key=lambda x:(x["scope"], x["mtime"]), reverse=False)
print(json.dumps(out, ensure_ascii=False, indent=1))
print("TOTAL", len(out), file=sys.stderr)
