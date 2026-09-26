"""桥梁档案接口：维护桥梁，覆盖评定等级、病害修补、注销桥梁等动作。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.schemas import ActionResult, EntryPayload, PageResult
from app.services.bridge import BridgeService

router = APIRouter(prefix="/api/bridge", tags=["桥梁档案"])

service = BridgeService()

LIST_FIELDS = ["桥梁编号", "桥梁名称", "桥型结构", "跨越对象", "桥面宽度", "桥长跨度", "设计荷载", "技术状况"]
STATUSES = ["待评定", "一类", "二类", "注销"]


@router.get("", response_model=PageResult[dict])
def list_entries(
    keyword: str | None = Query(default=None, description="按桥梁编号检索"),
    status: str | None = Query(default=None, description="待评定、一类、二类、注销"),
    page: int = 1,
    size: int = 20,
) -> PageResult[dict]:
    """按桥梁编号与状态过滤桥梁档案列表；没有数据时返回空页，不报错。"""
    if size > 200:
        raise HTTPException(status_code=400, detail="每页最多 200 条，请缩小分页范围")
    items, total = service.list_entries(keyword=keyword, status=status, page=page, size=size)
    return PageResult(items=items, total=total, page=page, size=size)


@router.get("/export")
def export_entries() -> dict[str, Any]:
    """导出桥梁档案清单：返回当前过滤条件下的全量数据。"""
    items, total = service.list_entries(page=1, size=10000)
    return {"module": "bridge", "total": total, "items": items}


@router.get("/{entry_id}", response_model=dict)
def get_entry(entry_id: int) -> dict:
    """读取单条桥梁明细；不存在时给出可读的错误说明。"""
    entry = service.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"桥梁 {entry_id} 不存在或已归档")
    return entry


@router.post("", response_model=ActionResult)
def create_entry(payload: EntryPayload) -> ActionResult:
    """登记一条桥梁，缺字段或编号重复时说明原因而不是静默丢弃。"""
    entry, error = service.create_entry(payload.values)
    if entry is None:
        return ActionResult(ok=False, message=error)
    return ActionResult(ok=True, message="桥梁已登记，技术状况进入待评定", entry=entry)


@router.post("/{entry_id}/actions", response_model=ActionResult)
def run_action(entry_id: int, payload: EntryPayload) -> ActionResult:
    """对单条桥梁执行评定等级、病害修补、注销桥梁；不允许的动作会被拦下并说明原因。"""
    action = str(payload.values.get("action") or "").strip()
    operator = str(payload.values.get("评定人") or "").strip()
    entry, message = service.run_action(entry_id, action, operator)
    if entry is None:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message=message, entry=entry)
