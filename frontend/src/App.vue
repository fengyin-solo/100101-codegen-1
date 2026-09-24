<template>
  <div class="app-shell">
    <aside class="app-side">
      <h1 class="app-title">市政道路桥梁养护管理平台</h1>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <header class="app-head">
        <span class="head-desc">面向市政道路桥梁日常巡查、定期检测、病害维修、除雪防汛与占道施工的一体化养护管理后台。</span>
        <span class="head-user">当前值班：{{ store.operator }} · {{ store.shiftLabel }}</span>
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '@/stores/session'

const store = useSessionStore()

const navItems = [{ label: "运营概览", path: "/" }, { label: "设施台账", path: "/facility" }, { label: "桥梁档案", path: "/bridge" }, { label: "隧道管理", path: "/tunnel" }, { label: "路面状况", path: "/pavement" }, { label: "日常巡查", path: "/patrol" }, { label: "病害记录", path: "/disease" }, { label: "养护维修", path: "/repair" }, { label: "养护材料", path: "/material2" }, { label: "养护机械", path: "/machine" }, { label: "应急抢险", path: "/emergency" }, { label: "除雪防汛", path: "/deicing" }, { label: "占道施工", path: "/occupy" }, { label: "绿化管护", path: "/greening" }, { label: "交安设施", path: "/safety2" }, { label: "边坡挡墙", path: "/geom" }, { label: "路灯管养", path: "/light" }, { label: "排水设施", path: "/drain" }, { label: "养护计划", path: "/plan" }, { label: "市民热线", path: "/complaint" }, { label: "车辆超限", path: "/load" }]
</script>
