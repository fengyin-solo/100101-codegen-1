"""桥梁档案接口：维护桥梁，覆盖技术状况评定流转、病害修补复核与注销封存。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.schemas import ActionResult, EntryPayload, PageResult
from app.services.bridge import BridgeService

router = APIRouter(prefix="/api/bridge", tags=["桥梁档案"])

service = BridgeService()

LIST_FIELDS = ["桥梁编号", "桥梁名称", "桥型结构", "跨越对象", "桥面宽度", "桥长跨度", "设计荷载", "技术状况", "评定人", "评定时间"]


@router.get("/export")
def export_entries() -> dict[str, Any]:
    """导出桥梁档案清单：返回当前过滤条件下的全量数据。"""
    items, total = service.list_entries(page=1, size=10000)
    return {"module": "bridge", "total": total, "items": items}


@router.get("", response_model=PageResult[dict])
def list_entries(
    keyword: str | None = Query(default=None, description="按桥梁编号检索"),
    status: str | None = Query(default=None, description="待评定、一类、二类、注销"),
    page: int = 1,
    size: int = 20,
) -> PageResult[dict]:
    """按桥梁编号与技术状况过滤桥梁档案列表；没有数据时返回空页，不报错。"""
    if size > 200:
        raise HTTPException(status_code=400, detail="每页最多 200 条，请缩小分页范围")
    items, total = service.list_entries(keyword=keyword, status=status, page=page, size=size)
    return PageResult(items=items, total=total, page=page, size=size)


@router.get("/{entry_id}", response_model=dict)
def get_entry(entry_id: int) -> dict:
    """读取单条桥梁明细（含评定记录）；不存在时给出可读的错误说明。"""
    entry = service.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"桥梁 {entry_id} 不存在或已归档")
    return entry


@router.post("", response_model=ActionResult)
def create_entry(payload: EntryPayload) -> ActionResult:
    """登记一条桥梁：缺必填字段会逐项说明，桥梁编号重复当场拦下。"""
    entry, error = service.create_entry(payload.values)
    if error:
        return ActionResult(ok=False, message=error)
    return ActionResult(ok=True, message="桥梁已登记，技术状况待评定", entry=entry)


@router.post("/{entry_id}/actions", response_model=ActionResult)
def run_action(entry_id: int, payload: EntryPayload) -> ActionResult:
    """执行评定一类、评定二类、病害修补完成、注销桥梁；每次变更都要留下评定人。"""
    action = str(payload.values.get("action") or payload.action or "").strip()
    operator = str(payload.values.get("评定人") or "").strip()
    entry, message = service.run_action(entry_id, action, operator)
    if entry is None:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message=message, entry=entry)
