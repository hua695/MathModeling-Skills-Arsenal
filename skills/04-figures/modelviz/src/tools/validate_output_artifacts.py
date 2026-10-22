"""Tool: 校验脚本输出文件。"""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool
from pydantic import ValidationError

from src.schemas import TechnicalIssue, ValidateOutputArtifactsInput
from src.tools._utils import error_result

SUPPORTED_OUTPUT_FORMATS = {"png", "svg"}
REQUIRED_OUTPUT_FORMATS = {"png", "svg"}


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


@tool(
    "validate_output_artifacts",
    args_schema=ValidateOutputArtifactsInput,
    description="检查生成文件是否存在、非空、扩展名正确且位于允许输出目录。",
)
def validate_output_artifacts(
    generated_files: list[str] | None = None, output_directory: str = "outputs"
) -> dict:
    """只检查文件层面的输出质量。"""

    try:
        ValidateOutputArtifactsInput(
            generated_files=generated_files or [], output_directory=output_directory
        )
    except ValidationError as error:
        return error_result(
            "validation_error", "输出文件校验参数错误。", details={"errors": error.errors()}
        )

    allowed = Path(output_directory)
    formats: list[str] = []
    issues: list[TechnicalIssue] = []
    valid_files: list[str] = []
    for file_name in generated_files or []:
        path = Path(file_name)
        suffix = path.suffix.lower().lstrip(".")
        if suffix not in SUPPORTED_OUTPUT_FORMATS:
            issues.append(
                TechnicalIssue(
                    issue_type="bad_extension",
                    severity="high",
                    message=f"不支持的输出格式：{path.suffix}；正式图片只允许 SVG 和 PNG。",
                )
            )
            continue
        if not _inside(path, allowed):
            issues.append(
                TechnicalIssue(
                    issue_type="forbidden_output_path", message=f"输出不在允许目录：{path}"
                )
            )
            continue
        if not path.exists():
            issues.append(
                TechnicalIssue(
                    issue_type="missing_output", severity="high", message=f"输出文件不存在：{path}"
                )
            )
            continue
        size = path.stat().st_size
        if size == 0:
            issues.append(
                TechnicalIssue(
                    issue_type="empty_file", severity="high", message=f"输出文件为空：{path}"
                )
            )
            continue
        if size < 512:
            issues.append(
                TechnicalIssue(issue_type="tiny_file", message=f"输出文件异常偏小：{path}")
            )
        formats.append(suffix)
        valid_files.append(str(path))
    if not valid_files:
        issues.append(
            TechnicalIssue(issue_type="no_output", severity="high", message="没有可用输出文件。")
        )
    missing_formats = REQUIRED_OUTPUT_FORMATS - set(formats)
    if missing_formats:
        issues.append(
            TechnicalIssue(
                issue_type="missing_required_format",
                severity="high",
                message="缺少正式图片格式：" + ", ".join(sorted(missing_formats)) + "；必须同时提供 SVG 和 PNG。",
            )
        )
    return {
        "success": not any(issue.severity == "high" for issue in issues),
        "valid_files": valid_files,
        "generated_formats": sorted(set(formats)),
        "issues": [issue.model_dump() for issue in issues],
    }
