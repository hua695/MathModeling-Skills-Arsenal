# 多 Agent 协作配置

主会话与 fork 分支使用同一份 `contest-orchestrator` 规则。主会话维护范围、事实、冻结状态和交付裁决；fork 分支执行被授权的求解、实验或论文节点。

## 分支回流

回流包至少包含：

- 当前阶段与完成状态；
- 项目相对路径和文件 SHA-256；
- 已执行命令及验证结果；
- 未决事项、阻塞项和禁止动作；
- 下一节点开始时应提交的首个状态报告。

主会话重新读取当前源文件、运行清单和 PDF 文本层后，才能接受回流。分支日志和内部讨论不得复制到论文成品。

## 安装后检查

```text
python scripts/check_skill_consistency.py . --strict
python scripts/skill_health_check.py . --strict --smoke
```

不同宿主的安装路径由宿主适配器决定；不在论文或项目文件中写入访问令牌、私有地址或本机绝对路径。
