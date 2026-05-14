"""Anna App Executa: JSON-RPC over stdio (describe / invoke). mini-notes summarization (rule-based)."""

from __future__ import annotations

import json
import sys
from typing import Any

# 总结句中的「主要方向」轴：顺序用于同分排序；关键词用于规则命中（一条笔记可对多轴各计 1 次）
_THEME_AXES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "开发",
        (
            "bug",
            "修",
            "登录",
            "代码",
            "编程",
            "接口",
            "api",
            "debug",
            "缺陷",
            "前端",
            "后端",
            "部署",
            "重构",
            "测试用例",
            "fix",
        ),
    ),
    (
        "协作",
        (
            "设计",
            "沟通",
            "需求",
            "会议",
            "评审",
            "对接",
            "产品",
            "pm",
            "对齐",
            "讨论",
            "客户",
            "同步",
        ),
    ),
    (
        "内容准备",
        (
            "准备",
            "workshop",
            "提纲",
            "ppt",
            "演讲",
            "分享",
            "课件",
            "讲义",
            "材料",
            "写稿",
            "教案",
            "slide",
        ),
    ),
    (
        "规划与管理",
        ("排期", "计划", "roadmap", "里程碑", "周报", "复盘", "okr", "项目管理"),
    ),
)

MANIFEST = {
    "name": "tool-dev-mini-notes",
    "version": "0.1.0",
    "tools": [
        {
            "name": "summarize",
            "description": "Return a short rule-based summary of all notes passed from the host.",
            "parameters": {
                "type": "object",
                "properties": {
                    "notes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "text": {"type": "string"},
                                "order": {"type": "integer"},
                                "createdAt": {"type": "string"},
                            },
                            "required": ["id", "text", "order", "createdAt"],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["notes"],
                "additionalProperties": False,
            },
        }
    ],
}


def _kw_hit(note_text: str, kw: str) -> bool:
    """中文子串匹配；英文等 ASCII 关键词大小写不敏感。"""
    if any("\u4e00" <= c <= "\u9fff" for c in kw):
        return kw in note_text
    return kw.lower() in note_text.lower()


def _note_hits_axes(text: str) -> set[str]:
    hit: set[str] = set()
    for label, kws in _THEME_AXES:
        if any(_kw_hit(text, kw) for kw in kws):
            hit.add(label)
    return hit


def _join_cn_themes(labels: list[str]) -> str:
    """例如：['开发','协作'] -> 开发和协作；['开发','协作','内容准备'] -> 开发、协作和内容准备"""
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]}和{labels[1]}"
    return "、".join(labels[:-1]) + f"和{labels[-1]}"


def _rule_based_summary(notes: list[dict[str, Any]]) -> str:
    """
    单句规则总结，例如：
    当前共有 3 条待处理事项，主要集中在开发、协作和内容准备。
    """
    if not notes:
        return "当前没有笔记。"

    ordered = sorted(notes, key=lambda n: int(n.get("order", 0)))
    n = len(ordered)

    # 每条笔记对各「方向轴」最多贡献 1 次计数
    axis_counts: dict[str, int] = {label: 0 for label, _ in _THEME_AXES}
    for item in ordered:
        text = str(item.get("text", ""))
        for axis in _note_hits_axes(text):
            if axis in axis_counts:
                axis_counts[axis] += 1

    ranked = sorted(
        enumerate(_THEME_AXES),
        key=lambda it: (-axis_counts[it[1][0]], it[0]),
    )
    # ranked 元素为 (轴序号, (轴名, 关键词元组))
    top_labels = [axis[0] for _, axis in ranked if axis_counts[axis[0]] > 0][:3]

    head = f"当前共有 {n} 条待处理事项"
    if not top_labels:
        return f"{head}，主题较为分散。"
    tail = _join_cn_themes(top_labels)
    return f"{head}，主要集中在{tail}。"


def invoke(method: str, args: dict[str, Any]) -> dict[str, Any]:
    if method == "summarize":
        notes = args.get("notes")
        if not isinstance(notes, list):
            return {"success": False, "error": "invalid notes: expected array"}
        summary = _rule_based_summary(notes)
        return {"success": True, "data": {"summary": summary}}

    return {"success": False, "error": f"unknown method: {method}"}


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        try:
            if req.get("method") == "describe":
                result = MANIFEST
            elif req.get("method") == "health":
                result = {"status": "ok"}
            elif req.get("method") == "invoke":
                result = invoke(req["params"]["tool"], req["params"].get("arguments", {}))
            else:
                raise ValueError(f"unknown rpc: {req.get('method')}")
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": req.get("id"), "result": result}) + "\n")
        except Exception as e:  # noqa: BLE001
            sys.stdout.write(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": req.get("id"),
                        "error": {"code": -32601, "message": str(e)},
                    }
                )
                + "\n"
            )
        sys.stdout.flush()


if __name__ == "__main__":
    main()
