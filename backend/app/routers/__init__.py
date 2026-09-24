"""业务模块路由汇总。

这里统一按别名导入再暴露 ROUTERS：模块名有可能和内置名撞车（某个业务模块就叫 dict、list
这种名字时），按名字直接 import 会把内置类型覆盖掉，函数注解在运行时求值就会报
'module' object is not subscriptable。
"""
from __future__ import annotations

from app.routers import facility as router_facility
from app.routers import bridge as router_bridge
from app.routers import tunnel as router_tunnel
from app.routers import pavement as router_pavement
from app.routers import patrol as router_patrol
from app.routers import disease as router_disease
from app.routers import repair as router_repair
from app.routers import material2 as router_material2
from app.routers import machine as router_machine
from app.routers import emergency as router_emergency
from app.routers import deicing as router_deicing
from app.routers import occupy as router_occupy
from app.routers import greening as router_greening
from app.routers import safety2 as router_safety2
from app.routers import geom as router_geom
from app.routers import light as router_light
from app.routers import drain as router_drain
from app.routers import plan as router_plan
from app.routers import complaint as router_complaint
from app.routers import load as router_load

ROUTERS = [router_facility, router_bridge, router_tunnel, router_pavement, router_patrol, router_disease, router_repair, router_material2, router_machine, router_emergency, router_deicing, router_occupy, router_greening, router_safety2, router_geom, router_light, router_drain, router_plan, router_complaint, router_load]
