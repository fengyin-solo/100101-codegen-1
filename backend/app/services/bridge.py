"""桥梁档案业务规则：技术状况评定流转、字段校验与筛选口径都收在这里。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.store import store

MODULE = "bridge"
REQUIRED_FIELDS = ["桥梁编号", "桥梁名称", "桥型结构"]
EDITABLE_FIELDS = ["桥梁编号", "桥梁名称", "桥型结构", "跨越对象", "桥面宽度", "桥长跨度", "设计荷载"]
ASSESS_FLOW = ["待评定", "一类", "二类"]
RETIRED_STATUS = "注销"
STATUS_ORDER = ASSESS_FLOW + [RETIRED_STATUS]
ACTIONS = ["评定等级", "病害修补", "注销桥梁"]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _record(operator: str, action: str, before: str, after: str) -> dict[str, str]:
    """每一步流转都留下可追溯的记录：谁、什么时候、从哪评到哪。"""
    return {"时间": _now(), "评定人": operator, "动作": action, "变更前": before, "变更后": after}


class BridgeService:
    def list_entries(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = store.rows(MODULE)
        if keyword:
            rows = [row for row in rows if keyword in str(row.get("桥梁编号", ""))]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        total = len(rows)
        start = max(page - 1, 0) * size
        return rows[start:start + size], total

    def get_entry(self, entry_id: int) -> dict[str, Any] | None:
        return store.find(MODULE, entry_id)

    def create_entry(self, values: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
        missing = [field for field in REQUIRED_FIELDS if not str(values.get(field) or "").strip()]
        if missing:
            return None, f"缺少必填字段：{'、'.join(missing)}"
        code = str(values["桥梁编号"]).strip()
        for row in store.rows(MODULE):
            if str(row.get("桥梁编号", "")).strip() == code:
                return None, f"桥梁编号 {code} 已登记（档案 #{row.get('id')}），同一座桥梁不能重复登记"
        rows = store.rows(MODULE)
        entry = {"id": max((int(row.get("id", 0)) for row in rows), default=0) + 1}
        for field in EDITABLE_FIELDS:
            value = str(values.get(field) or "").strip()
            if value:
                entry[field] = value
        operator = str(values.get("评定人") or "").strip() or "系统登记"
        entry["status"] = ASSESS_FLOW[0]
        entry["技术状况"] = ASSESS_FLOW[0]
        entry["pending"] = True
        entry["abnormal"] = False
        entry["评定记录"] = [_record(operator, "登记桥梁", "—", ASSESS_FLOW[0])]
        rows.append(entry)
        return entry, ""

    def run_action(self, entry_id: int, action: str, operator: str) -> tuple[dict[str, Any] | None, str]:
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"桥梁 {entry_id} 不存在或已归档"
        if entry.get("status") == RETIRED_STATUS:
            return None, f"桥梁 {entry_id} 已注销，档案封存，不能再执行任何变更"
        if action not in ACTIONS:
            return None, f"动作「{action}」不属于桥梁档案可执行范围"
        if not operator:
            return None, "缺少评定人，评定流转必须留痕才能执行"
        current = str(entry.get("status") or ASSESS_FLOW[0])
        if action == "评定等级":
            step = ASSESS_FLOW.index(current) if current in ASSESS_FLOW else -1
            if step < 0 or step >= len(ASSESS_FLOW) - 1:
                return None, f"桥梁当前技术状况为「{current}」，不能继续评定等级"
            target = ASSESS_FLOW[step + 1]
            message = f"技术状况评定完成：{current} → {target}"
        elif action == "病害修补":
            if current == ASSESS_FLOW[0]:
                return None, "桥梁尚在待评定，无需通过病害修补退回复核"
            target = ASSESS_FLOW[0]
            message = f"病害修补完成，技术状况回到待评定重新复核：{current} → {target}"
        else:
            target = RETIRED_STATUS
            message = f"桥梁已注销：{current} → {target}，档案封存不再变更"
        entry["status"] = target
        entry["技术状况"] = target
        entry["pending"] = target == ASSESS_FLOW[0]
        entry["abnormal"] = False
        entry.setdefault("评定记录", []).append(_record(operator, action, current, target))
        return entry, message
