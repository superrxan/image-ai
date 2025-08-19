"""工具系统的类型定义"""

from enum import Enum

from dataclasses import dataclass
from typing import Any, Dict, Optional
import uuid


@dataclass
class ToolDefinition:
    """工具定义"""

    name: str  # 工具名称
    description: str  # 工具描述（OpenAI函数调用格式）
    parameters: Optional[Dict[str, Any]] = None  # 额外参数


class Message:
    def __init__(
        self,
        role: str,
        content: str = None,
        uniq_id: str = None,
        tool_calls=None,
        tool_call_id=None,
    ):
        self.role = role
        self.content = content
        self.tool_calls = tool_calls
