#!/usr/bin/env python3
"""mode_route.py — 论文辅助 skill 模式路由查询
根据 active_mode 输出该模式下的审查范围、检查项和注意事项。
不依赖外部库。
"""
import re, argparse, json
from pathlib import Path

def _default_routing_path():
    return Path(__file__).parent.parent / 'templates' / 'mode_routing.yaml'

def load_routing(f):
    text = Path(f).read_text(encoding='utf-8')
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return _parse_simple_yaml(text)

def _parse_simple_yaml(text):
    """极简 YAML 解析器，支持 mode_routing.yaml 的结构。"""
    result = {}
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            i += 1
            continue
        # top-level key
        m = re.match(r'^([a-zA-Z0-9_-]+):\s*(.*)$', line)
        if m and not line.startswith(' '):
            key = m.group(1)
            val = m.group(2).strip()
            if val:
                result[key] = val.strip('"').strip("'")
            else:
                # parse nested block
                nested, i = _parse_nested(lines, i + 1, 2)
                result[key] = nested
                continue
        i += 1
    return result

def _parse_nested(lines, start, indent):
    result = {}
    i = start
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip().startswith('#'):
            i += 1
            continue
        cur_indent = len(line) - len(line.lstrip())
        if cur_indent < indent:
            break
        if cur_indent > indent:
            i += 1
            continue
        m = re.match(r'^\s+([a-zA-Z0-9_-]+):\s*(.*)$', line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            if val.startswith('[') and val.endswith(']'):
                result[key] = [x.strip().strip('"').strip("'") for x in re.findall(r'["\']([^"\']+)["\']', val)]
            elif val:
                result[key] = val.strip('"').strip("'")
            else:
                nested, i = _parse_nested(lines, i + 1, indent + 2)
                result[key] = nested
                continue
        i += 1
    return result, i

def list_modes(routing):
    modes = routing.get('modes', {})
    print("可用模式：")
    for name, cfg in modes.items():
        if not isinstance(cfg, dict):
            continue
        applicable = cfg.get('applicable', 'unknown')
        desc = cfg.get('description', '')
        status = "✓" if applicable is True or applicable == 'true' else "✗"
        print(f"  {status} {name}: {desc}")

def show_mode(routing, mode_name):
    modes = routing.get('modes', {})
    if mode_name not in modes:
        print(f"错误：未找到模式 '{mode_name}'")
        print("可用模式：", ', '.join(modes.keys()))
        exit(1)
    cfg = modes[mode_name]
    applicable = cfg.get('applicable', 'unknown')
    print(f"模式：{mode_name}")
    print(f"适用：{applicable}")
    if cfg.get('description'):
        print(f"说明：{cfg['description']}")
    if applicable is False or applicable == 'false':
        print(f"原因：{cfg.get('reason', '不适用')}")
        return
    if cfg.get('review_triggers'):
        triggers = cfg['review_triggers']
        if isinstance(triggers, list):
            print(f"审查触发：{', '.join(triggers)}")
        else:
            print(f"审查触发：{triggers}")
    if cfg.get('checks'):
        print("\n检查项：")
        for check, scope in cfg['checks'].items():
            print(f"  - {check}: {scope}")
    if cfg.get('stage_mapping'):
        print("\n阶段映射（A–G → 审查重点）：")
        for stage, mapping in cfg['stage_mapping'].items():
            print(f"  {stage}: {mapping}")
    if cfg.get('node_focus'):
        print("\n节点审查重点：")
        for node, focus in cfg['node_focus'].items():
            print(f"  {node}: {focus}")
    if cfg.get('notes'):
        print("\n注意事项：")
        for note in cfg['notes']:
            print(f"  - {note}")

def main():
    parser = argparse.ArgumentParser(description='论文辅助 skill 模式路由查询')
    parser.add_argument('--mode', help='查询指定模式的审查配置')
    parser.add_argument('--list', action='store_true', help='列出所有可用模式')
    parser.add_argument('--routing', default=None, help='路由表路径（默认使用 skill 内置）')
    parser.add_argument('--json', action='store_true', help='以 JSON 格式输出')
    args = parser.parse_args()

    routing_path = Path(args.routing) if args.routing else _default_routing_path()
    if not routing_path.exists():
        print(f"错误：路由表不存在：{routing_path}")
        exit(2)

    routing = load_routing(routing_path)

    if args.list:
        if args.json:
            modes = routing.get('modes', {})
            out = {name: {'applicable': cfg.get('applicable'), 'description': cfg.get('description', '')}
                   for name, cfg in modes.items() if isinstance(cfg, dict)}
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            list_modes(routing)
        return

    if args.mode:
        if args.json:
            modes = routing.get('modes', {})
            print(json.dumps(modes.get(args.mode, {}), ensure_ascii=False, indent=2))
        else:
            show_mode(routing, args.mode)
        return

    # 默认：列出模式
    list_modes(routing)
    print("\n使用 --mode <模式名> 查看详细配置，或 --list 查看列表")

if __name__ == '__main__':
    main()
