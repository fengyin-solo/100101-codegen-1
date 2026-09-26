"""桥梁档案业务规则：技术状况评定流转、字段校验与筛选口径都收在这里。

流转约定：新登记的桥梁一律从「待评定」起步，依次评定为「一类」「二类」；
病害修补完成后必须回到「待评定」重新复核；「注销」是终态，档案封存后任何动作都拦下。
每一次状态变更都追加一条评定记录（时间、动作、原状态、新状态、评定人），
交接班后刷新页面也能看到上一步是谁评的。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.store import store

MODULE = "bridge"
REQUIRED_FIELDS = ["桥梁编号", "桥梁名称", "桥型结构"]

STATUS_PENDING = "待评定"
STATUS_CANCELLED = "注销"
STATUSES = [STATUS_PENDING, "一类", "二类", STATUS_CANCELLED]

# 动作 -> (允许发起的当前状态集合, 目标状态)；顺序即页面上的动作顺序
STATUS_FLOW: dict[str, tuple[set[str], str]] = {
    "评定一类": ({STATUS_PENDING}, "一类"),
    "评定二类": ({"一类"}, "二类"),
    "病害修补完成": ({"一类", "二类"}, STATUS_PENDING),
    "注销桥梁": ({STATUS_PENDING, "一类", "二类"}, STATUS_CANCELLED),
}
ACTIONS = list(STATUS_FLOW)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _sync(row: dict[str, Any]) -> dict[str, Any]:
    """技术状况以 status 为唯一口径，列表与详情读到的一定是同一个值。"""
    row["技术状况"] = str(row.get("status") or STATUS_PENDING)
    return row


class BridgeService:
    def list_entries(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = [_sync(row) for row in store.rows(MODULE)]
        if keyword:
            rows = [row for row in rows if keyword in str(row.get("桥梁编号", ""))]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        total = len(rows)
        start = max(page - 1, 0) * size
        return rows[start:start + size], total

    def get_entry(self, entry_id: int) -> dict[str, Any] | None:
        row = store.find(MODULE, entry_id)
        return _sync(row) if row is not None else None

    def create_entry(self, values: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
        """登记桥梁；返回 (档案, 错误说明)，错误说明为空即成功。"""
        missing = [field for field in REQUIRED_FIELDS if not str(values.get(field) or "").strip()]
        if missing:
            return None, f"缺少必填字段：{'、'.join(missing)}，未保存"
        code = str(values["桥梁编号"]).strip()
        rows = store.rows(MODULE)
        for row in rows:
            if str(row.get("桥梁编号", "")).strip() == code:
                return None, f"桥梁编号 {code} 已登记在案（档案 #{row.get('id')}），同一座桥梁不能重复登记"
        operator = str(values.get("评定人") or "").strip() or "系统登记"
        entry: dict[str, Any] = {"id": max((int(row.get("id", 0)) for row in rows), default=0) + 1}
        for field in REQUIRED_FIELDS:
            entry[field] = str(values.get(field) or "").strip()
        for field in ("跨越对象", "桥面宽度", "桥长跨度", "设计荷载"):
            text = str(values.get(field) or "").strip()
            if text:
                entry[field] = text
        entry["status"] = STATUS_PENDING
        entry["pending"] = True
        entry["abnormal"] = False
        entry["评定人"] = ""
        entry["评定时间"] = ""
        entry["评定记录"] = [{
            "时间": _now(),
            "动作": "登记建档",
            "原状态": "—",
            "新状态": STATUS_PENDING,
            "评定人": operator,
        }]
        rows.append(entry)
        return _sync(entry), ""

    def run_action(self, entry_id: int, action: str, operator: str) -> tuple[dict[str, Any] | None, str]:
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"桥梁 {entry_id} 不存在或已归档"
        current = str(entry.get("status") or STATUS_PENDING)
        if current == STATUS_CANCELLED:
            return None, f"桥梁 {entry_id} 已注销，档案封存，不能再改动"
        if action not in STATUS_FLOW:
            return None, f"动作「{action}」不属于桥梁档案可执行范围"
        if not operator:
            return None, "每次评定变更都必须登记评定人，请填写后再提交"
        allowed_from, target = STATUS_FLOW[action]
        if current not in allowed_from:
            return None, f"当前技术状况为「{current}」，不能执行「{action}」，请按待评定→一类→二类的顺序流转"
        record = {
            "时间": _now(),
            "动作": action,
            "原状态": current,
            "新状态": target,
            "评定人": operator,
        }
        entry.setdefault("评定记录", []).append(record)
        entry["status"] = target
        entry["评定人"] = operator
        entry["评定时间"] = record["时间"]
        entry["pending"] = target == STATUS_PENDING
        entry["abnormal"] = False
        _sync(entry)
        return entry, f"桥梁已{action}：技术状况 {current} → {target}"
