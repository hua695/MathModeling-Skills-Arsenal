#!/usr/bin/env python3
"""validate_findings.py — 校验 findings JSON 是否符合 finding_json_schema.json
不依赖 jsonschema 库，手写轻量校验器（覆盖 required / enum / pattern / type / additionalProperties）。
"""
import re, json, argparse
from pathlib import Path

def _default_schema_path():
    return Path(__file__).parent.parent / 'templates' / 'finding_json_schema.json'

def validate_finding(finding, schema, path=''):
    errors = []
    props = schema.get('properties', {})

    # required
    for field in schema.get('required', []):
        if field not in finding:
            errors.append(f'{path}.{field}: 缺失必填字段')

    # additionalProperties
    if schema.get('additionalProperties') is False:
        allowed = set(props.keys())
        for key in finding:
            if key not in allowed:
                errors.append(f'{path}.{key}: 不允许的额外字段')

    # per-property checks
    for field, value in finding.items():
        prop = props.get(field, {})
        if not prop:
            continue
        # type
        expected_type = prop.get('type')
        if expected_type == 'string' and not isinstance(value, str):
            errors.append(f'{path}.{field}: 类型错误，期望 string，实际 {type(value).__name__}')
        # enum
        if 'enum' in prop and value not in prop['enum']:
            errors.append(f'{path}.{field}: 值 "{value}" 不在允许范围 {prop["enum"]}')
        # pattern
        if 'pattern' in prop and isinstance(value, str):
            if not re.match(prop['pattern'], value):
                errors.append(f'{path}.{field}: 值 "{value}" 不匹配正则 {prop["pattern"]}')

    return errors

def main():
    parser = argparse.ArgumentParser(description='校验 findings JSON 文件是否符合 schema')
    parser.add_argument('--findings', required=True, help='findings JSON 文件（单对象或数组）')
    parser.add_argument('--schema', default=None, help='schema 文件路径（默认使用 skill 内置 templates/finding_json_schema.json）')
    args = parser.parse_args()

    schema_path = Path(args.schema) if args.schema else _default_schema_path()
    if not schema_path.exists():
        print(f'错误：schema 文件不存在：{schema_path}')
        exit(2)

    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    data = json.loads(Path(args.findings).read_text(encoding='utf-8-sig'))

    if isinstance(data, list):
        all_errors = []
        for i, f in enumerate(data):
            all_errors.extend(validate_finding(f, schema, f'[{i}]'))
        count = len(data)
    else:
        all_errors = validate_finding(data, schema)
        count = 1

    if all_errors:
        print(f'校验失败：{count} 条 finding 中共 {len(all_errors)} 个错误')
        for e in all_errors:
            print(f'  ✗ {e}')
        exit(1)
    else:
        print(f'校验通过：{count} 条 finding 全部符合 schema（{schema_path.name}）')

if __name__ == '__main__':
    main()
