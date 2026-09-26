<template>
  <section class="page" data-module="bridge">
    <header class="page-head">
      <div>
        <h2>桥梁档案管理</h2>
        <p class="page-desc">维护桥梁，围绕桥梁编号、桥梁名称、桥型结构、跨越对象做登记、筛选与状态流转。</p>
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
        <input v-model="filters.keyword" placeholder="按桥梁编号检索" />
      </label>
      <label class="filter-item">
        <span>技术状况</span>
        <select v-model="filters.status">
          <option value="">全部</option>
          <option v-for="status in statuses" :key="status" :value="status">{{ status }}</option>
        </select>
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetFilters">重置条件</button>
    </form>

    <form v-if="createVisible" class="create-panel" @submit.prevent="submitCreate">
      <h3 class="panel-title">登记桥梁</h3>
      <div class="create-grid">
        <label v-for="field in createFields" :key="field.name" class="filter-item">
          <span>{{ field.label }}<em v-if="field.required" class="required-mark">*</em></span>
          <input v-model="createForm[field.name]" :placeholder="`请输入${field.label}`" />
        </label>
        <label class="filter-item">
          <span>评定人</span>
          <input :value="session.operator" disabled />
        </label>
      </div>
      <div class="panel-actions">
        <button class="btn primary" type="submit">保存登记</button>
        <button class="btn ghost" type="button" @click="closeCreate">取消</button>
      </div>
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
          <td v-for="column in columns" :key="column">{{ row[column] ?? '—' }}</td>
          <td class="row-actions">
            <button class="link" type="button" @click="openDetail(row)">详情</button>
            <button
              v-for="action in availableActions(row)"
              :key="action"
              class="link"
              type="button"
              @click="runAction(action, row)"
            >
              {{ action }}
            </button>
            <span v-if="isRetired(row)" class="retired-tag">已注销</span>
          </td>
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="columns.length + 1" class="empty-state">暂无桥梁档案数据，可先登记桥梁</td>
        </tr>
      </tbody>
    </table>

    <aside v-if="detail" class="detail-panel">
      <header class="panel-head">
        <h3 class="panel-title">桥梁详情 #{{ detail.id }}</h3>
        <button class="btn ghost" type="button" @click="closeDetail">关闭</button>
      </header>
      <dl class="detail-grid">
        <div v-for="column in columns" :key="column" class="detail-item">
          <dt>{{ column }}</dt>
          <dd>{{ detail[column] ?? '—' }}</dd>
        </div>
      </dl>
      <h4 class="panel-subtitle">评定记录</h4>
      <table class="data-table">
        <thead>
          <tr>
            <th>时间</th>
            <th>评定人</th>
            <th>动作</th>
            <th>变更前</th>
            <th>变更后</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(record, index) in detailRecords" :key="index">
            <td>{{ record.时间 }}</td>
            <td>{{ record.评定人 }}</td>
            <td>{{ record.动作 }}</td>
            <td>{{ record.变更前 }}</td>
            <td>{{ record.变更后 }}</td>
          </tr>
          <tr v-if="!detailRecords.length">
            <td colspan="5" class="empty-state">暂无评定记录</td>
          </tr>
        </tbody>
      </table>
    </aside>

    <footer class="page-foot">
      <span>共 {{ total }} 条桥梁档案记录</span>
      <span v-if="noticeMessage" class="notice-text">{{ noticeMessage }}</span>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { request } from '@/api/client'
import { useSessionStore } from '@/stores/session'

type Row = Record<string, string | number | null>
type AssessRecord = { 时间: string; 评定人: string; 动作: string; 变更前: string; 变更后: string }

const ENDPOINT = '/api/bridge'
const columns = ["桥梁编号", "桥梁名称", "桥型结构", "跨越对象", "桥面宽度", "桥长跨度", "设计荷载", "技术状况"]
const statuses = ["待评定", "一类", "二类", "注销"]
const createFields = [
  { name: '桥梁编号', label: '桥梁编号', required: true },
  { name: '桥梁名称', label: '桥梁名称', required: true },
  { name: '桥型结构', label: '桥型结构', required: true },
  { name: '跨越对象', label: '跨越对象', required: false },
  { name: '桥面宽度', label: '桥面宽度', required: false },
  { name: '桥长跨度', label: '桥长跨度', required: false },
  { name: '设计荷载', label: '设计荷载', required: false },
]

const session = useSessionStore()

const rows = ref<Row[]>([])
const total = ref(0)
const errorMessage = ref('')
const noticeMessage = ref('')
const filters = ref<Record<string, string>>({ keyword: '', status: '' })
const createVisible = ref(false)
const createForm = ref<Record<string, string>>({})
const detail = ref<Row | null>(null)

const stats = computed(() => [
  { label: '待评定桥梁', value: rows.value.filter((row) => row['技术状况'] === '待评定').length },
  { label: '一类桥梁', value: rows.value.filter((row) => row['技术状况'] === '一类').length },
  { label: '二类桥梁', value: rows.value.filter((row) => row['技术状况'] === '二类').length },
])

const detailRecords = computed<AssessRecord[]>(() => {
  const records = detail.value?.['评定记录']
  return Array.isArray(records) ? (records as AssessRecord[]) : []
})

function isRetired(row: Row) {
  return row['技术状况'] === '注销'
}

function availableActions(row: Row) {
  const status = String(row['技术状况'] ?? '')
  if (status === '注销') return []
  const actions: string[] = []
  if (status === '待评定' || status === '一类') actions.push('评定等级')
  if (status === '一类' || status === '二类') actions.push('病害修补')
  actions.push('注销桥梁')
  return actions
}

function resetFilters() {
  filters.value = { keyword: '', status: '' }
  void reload()
}

function exportRows() {
  window.open(`${ENDPOINT}/export`, '_blank')
}

function openCreate() {
  createForm.value = {}
  createVisible.value = true
  errorMessage.value = ''
  noticeMessage.value = ''
}

function closeCreate() {
  createVisible.value = false
}

async function submitCreate() {
  errorMessage.value = ''
  noticeMessage.value = ''
  try {
    const response = await request(ENDPOINT, {
      method: 'POST',
      body: JSON.stringify({ values: { ...createForm.value, 评定人: session.operator } }),
    })
    const result = await response.json()
    if (!result.ok) {
      errorMessage.value = result.message ?? '桥梁登记未生效'
      return
    }
    noticeMessage.value = result.message ?? '桥梁已登记'
    createVisible.value = false
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '桥梁登记失败'
  }
}

async function runAction(action: string, row: Row) {
  errorMessage.value = ''
  noticeMessage.value = ''
  try {
    const response = await request(`${ENDPOINT}/${row.id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ values: { action, 评定人: session.operator } }),
    })
    const result = await response.json()
    if (!result.ok) {
      errorMessage.value = result.message ?? '桥梁档案动作未生效'
      return
    }
    noticeMessage.value = result.message ?? '桥梁档案动作已生效'
    await reload()
    if (detail.value && detail.value.id === row.id) {
      await openDetail(row)
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '桥梁档案操作失败'
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

async function reload() {
  errorMessage.value = ''
  const query = new URLSearchParams()
  if (filters.value.keyword) query.set('keyword', filters.value.keyword)
  if (filters.value.status) query.set('status', filters.value.status)
  try {
    const response = await request(`${ENDPOINT}?${query.toString()}`)
    if (!response.ok) {
      throw new Error('桥梁列表读取失败')
    }
    const payload = await response.json()
    rows.value = payload.items ?? []
    total.value = payload.total ?? rows.value.length
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '桥梁档案列表读取失败'
  }
}

onMounted(reload)
</script>

<style scoped>
.create-panel,
.detail-panel {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 12px;
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.panel-title {
  margin: 0 0 10px;
  font-size: 15px;
}
.panel-subtitle {
  margin: 12px 0 8px;
  font-size: 14px;
}
.create-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
  margin-bottom: 10px;
}
.panel-actions {
  display: flex;
  gap: 8px;
}
.required-mark {
  color: #b42318;
  font-style: normal;
  margin-left: 2px;
}
.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 8px;
  margin: 0;
}
.detail-item dt {
  font-size: 12px;
  color: var(--muted);
}
.detail-item dd {
  margin: 2px 0 0;
  font-size: 13px;
}
.retired-tag {
  color: var(--muted);
  font-size: 12px;
}
.notice-text {
  color: #067647;
}
</style>
