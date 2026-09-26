<template>
  <section class="page" data-module="bridge">
    <header class="page-head">
      <div>
        <h2>桥梁档案管理</h2>
        <p class="page-desc">技术状况按 待评定 → 一类 → 二类 顺序评定，病害修补完成后回到待评定重新复核，每次变更都记下时间与评定人，注销后档案封存。</p>
      </div>
      <div class="page-actions">
        <button class="btn primary" type="button" @click="openCreate">登记桥梁</button>
        <button class="btn" type="button" @click="exportRows">导出桥梁档案清单</button>
      </div>
    </header>

    <div class="stat-row">
      <article v-for="item in stats" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong class="stat-value">{{ item.value }}</strong>
      </article>
    </div>

    <form class="filter-bar" @submit.prevent="reload">
      <label class="filter-item">
        <span>桥梁编号</span>
        <input v-model="keyword" placeholder="按桥梁编号检索" />
      </label>
      <label class="filter-item">
        <span>技术状况</span>
        <select v-model="statusFilter">
          <option value="">全部</option>
          <option v-for="status in statuses" :key="status" :value="status">{{ status }}</option>
        </select>
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetFilters">重置条件</button>
    </form>

    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column">{{ column }}</th>
          <th>可执行动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="String(row.id)">
          <td v-for="column in columns" :key="column">
            <button v-if="column === '桥梁编号'" class="link" type="button" @click="openDetail(row)">
              {{ row[column] ?? '—' }}
            </button>
            <template v-else>{{ row[column] || '—' }}</template>
          </td>
          <td class="row-actions">
            <button class="link" type="button" @click="openDetail(row)">详情</button>
            <button
              v-for="action in rowActions(row)"
              :key="action"
              class="link"
              type="button"
              @click="openAction(action, row)"
            >
              {{ action }}
            </button>
            <span v-if="!rowActions(row).length" class="muted-text">已注销封存</span>
          </td>
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="columns.length + 1" class="empty-state">暂无桥梁档案数据，可先登记桥梁</td>
        </tr>
      </tbody>
    </table>

    <footer class="page-foot">
      <span>共 {{ total }} 条桥梁档案记录</span>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
    </footer>

    <div v-if="createVisible" class="dialog-mask" @click.self="createVisible = false">
      <div class="dialog">
        <h3>登记桥梁</h3>
        <form @submit.prevent="submitCreate">
          <label v-for="field in createFields" :key="field.name" class="form-item">
            <span>{{ field.name }}<em v-if="field.required" class="required-mark">*</em></span>
            <input
              v-model="createForm[field.name]"
              :placeholder="field.required ? `必填，请输入${field.name}` : '选填'"
            />
          </label>
          <p v-if="createError" class="error-text">{{ createError }}</p>
          <div class="dialog-actions">
            <button class="btn primary" type="submit">保存登记</button>
            <button class="btn ghost" type="button" @click="createVisible = false">取消</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="actionDialog.visible" class="dialog-mask" @click.self="actionDialog.visible = false">
      <div class="dialog">
        <h3>{{ actionDialog.action }}</h3>
        <p class="page-desc">
          桥梁 {{ actionDialog.row?.桥梁编号 }}（{{ actionDialog.row?.桥梁名称 }}），当前技术状况「{{ actionDialog.row?.技术状况 }}」。
        </p>
        <label class="form-item">
          <span>评定人<em class="required-mark">*</em></span>
          <input v-model="actionDialog.operator" placeholder="每次变更都要留下评定人" />
        </label>
        <p v-if="actionDialog.error" class="error-text">{{ actionDialog.error }}</p>
        <div class="dialog-actions">
          <button class="btn primary" type="button" @click="submitAction">确认{{ actionDialog.action }}</button>
          <button class="btn ghost" type="button" @click="actionDialog.visible = false">取消</button>
        </div>
      </div>
    </div>

    <div v-if="detail" class="dialog-mask" @click.self="closeDetail">
      <div class="dialog wide">
        <h3>桥梁详情 · {{ detail.桥梁编号 }}</h3>
        <div class="detail-grid">
          <div v-for="column in columns" :key="column" class="detail-item">
            <span class="stat-label">{{ column }}</span>
            <strong>{{ detail[column] || '—' }}</strong>
          </div>
        </div>
        <h4 class="history-title">评定流转记录</h4>
        <table class="data-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>动作</th>
              <th>原状态</th>
              <th>新状态</th>
              <th>评定人</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(record, index) in detailHistory" :key="index">
              <td>{{ record.时间 }}</td>
              <td>{{ record.动作 }}</td>
              <td>{{ record.原状态 }}</td>
              <td>{{ record.新状态 }}</td>
              <td>{{ record.评定人 }}</td>
            </tr>
            <tr v-if="!detailHistory.length">
              <td colspan="5" class="empty-state">暂无评定记录</td>
            </tr>
          </tbody>
        </table>
        <div class="dialog-actions">
          <button class="btn ghost" type="button" @click="closeDetail">关闭</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { request } from '@/api/client'
import { useSessionStore } from '@/stores/session'

type Row = Record<string, any>

const ENDPOINT = '/api/bridge'
const columns = ["桥梁编号", "桥梁名称", "桥型结构", "跨越对象", "桥面宽度", "桥长跨度", "设计荷载", "技术状况", "评定人", "评定时间"]
const statuses = ["待评定", "一类", "二类", "注销"]
// 与后端 STATUS_FLOW 保持一致：按当前技术状况给出可执行动作，注销后不再出现任何动作
const ACTION_FLOW: Record<string, string[]> = {
  '待评定': ['评定一类', '注销桥梁'],
  '一类': ['评定二类', '病害修补完成', '注销桥梁'],
  '二类': ['病害修补完成', '注销桥梁'],
  '注销': [],
}
const createFields = [
  { name: '桥梁编号', required: true },
  { name: '桥梁名称', required: true },
  { name: '桥型结构', required: true },
  { name: '跨越对象', required: false },
  { name: '桥面宽度', required: false },
  { name: '桥长跨度', required: false },
  { name: '设计荷载', required: false },
]

const session = useSessionStore()

const rows = ref<Row[]>([])
const total = ref(0)
const errorMessage = ref('')
const keyword = ref('')
const statusFilter = ref('')
const stats = ref([
  { label: '待评定', value: 0 },
  { label: '一类桥梁', value: 0 },
  { label: '二类桥梁', value: 0 },
  { label: '已注销', value: 0 },
])

const createVisible = ref(false)
const createForm = reactive<Record<string, string>>({})
const createError = ref('')

const actionDialog = reactive({
  visible: false,
  action: '',
  row: null as Row | null,
  operator: '',
  error: '',
})

const detail = ref<Row | null>(null)
const detailHistory = computed<Row[]>(() => (detail.value?.评定记录 as Row[]) ?? [])

function rowActions(row: Row): string[] {
  return ACTION_FLOW[String(row.技术状况 ?? '待评定')] ?? []
}

function resetFilters() {
  keyword.value = ''
  statusFilter.value = ''
  void reload()
}

function exportRows() {
  window.open(`${ENDPOINT}/export`, '_blank')
}

function openCreate() {
  for (const field of createFields) {
    createForm[field.name] = ''
  }
  createError.value = ''
  createVisible.value = true
}

async function submitCreate() {
  createError.value = ''
  try {
    const response = await request(ENDPOINT, {
      method: 'POST',
      body: JSON.stringify({ values: { ...createForm, 评定人: session.operator } }),
    })
    const payload = await response.json()
    if (!response.ok || !payload.ok) {
      createError.value = payload.message ?? '桥梁登记未生效，请检查后重试'
      return
    }
    createVisible.value = false
    await reload()
  } catch (error) {
    createError.value = error instanceof Error ? error.message : '桥梁登记失败'
  }
}

function openAction(action: string, row: Row) {
  actionDialog.visible = true
  actionDialog.action = action
  actionDialog.row = row
  actionDialog.operator = session.operator
  actionDialog.error = ''
}

async function submitAction() {
  actionDialog.error = ''
  const operator = actionDialog.operator.trim()
  if (!operator) {
    actionDialog.error = '每次评定变更都必须登记评定人'
    return
  }
  try {
    const response = await request(`${ENDPOINT}/${actionDialog.row?.id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ values: { action: actionDialog.action, 评定人: operator } }),
    })
    const payload = await response.json()
    if (!response.ok || !payload.ok) {
      actionDialog.error = payload.message ?? '桥梁档案动作未生效，请稍后重试'
      return
    }
    actionDialog.visible = false
    await reload()
    if (detail.value && actionDialog.row && detail.value.id === actionDialog.row.id) {
      await openDetail(actionDialog.row)
    }
  } catch (error) {
    actionDialog.error = error instanceof Error ? error.message : '桥梁档案操作失败'
  }
}

async function openDetail(row: Row) {
  errorMessage.value = ''
  try {
    const response = await request(`${ENDPOINT}/${row.id}`)
    if (!response.ok) {
      throw new Error('桥梁详情读取失败')
    }
    detail.value = await response.json()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '桥梁详情读取失败'
  }
}

function closeDetail() {
  detail.value = null
}

async function loadStats() {
  try {
    const response = await request(`${ENDPOINT}?page=1&size=200`)
    if (!response.ok) {
      return
    }
    const payload = await response.json()
    const items: Row[] = payload.items ?? []
    stats.value = [
      { label: '待评定', value: items.filter((item) => item.技术状况 === '待评定').length },
      { label: '一类桥梁', value: items.filter((item) => item.技术状况 === '一类').length },
      { label: '二类桥梁', value: items.filter((item) => item.技术状况 === '二类').length },
      { label: '已注销', value: items.filter((item) => item.技术状况 === '注销').length },
    ]
  } catch {
    // 统计失败不阻塞列表展示
  }
}

async function reload() {
  errorMessage.value = ''
  const query = new URLSearchParams()
  if (keyword.value.trim()) {
    query.set('keyword', keyword.value.trim())
  }
  if (statusFilter.value) {
    query.set('status', statusFilter.value)
  }
  try {
    const response = await request(`${ENDPOINT}?${query}`)
    if (!response.ok) {
      throw new Error('桥梁列表读取失败')
    }
    const payload = await response.json()
    rows.value = payload.items ?? []
    total.value = payload.total ?? rows.value.length
    await loadStats()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '桥梁档案列表读取失败'
  }
}

onMounted(reload)
</script>

<style scoped>
.muted-text { color: var(--muted); font-size: 12px; }
.filter-item select { padding: 4px 8px; border: 1px solid var(--border); border-radius: 6px; background: #fff; }
.dialog-mask { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.45); display: flex; align-items: center; justify-content: center; z-index: 20; }
.dialog { background: #fff; border-radius: 10px; padding: 20px; width: 420px; max-width: 92vw; max-height: 86vh; overflow: auto; }
.dialog.wide { width: 640px; }
.dialog h3 { margin: 0 0 12px; }
.form-item { display: block; margin-bottom: 10px; }
.form-item span { display: block; font-size: 12px; color: var(--muted); margin-bottom: 4px; }
.form-item input { width: 100%; padding: 6px 8px; border: 1px solid var(--border); border-radius: 6px; }
.required-mark { color: #b42318; font-style: normal; }
.dialog-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 14px; }
.detail-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px; }
.detail-item { border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; }
.detail-item strong { display: block; margin-top: 2px; font-size: 14px; }
.history-title { margin: 0 0 8px; font-size: 14px; }
</style>
