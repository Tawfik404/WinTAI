import { useState, useCallback, type ReactNode } from 'react'
import {
  AppWindow,
  XSquare,
  RotateCw,
  Terminal,
  Monitor,
  Clipboard,
  FolderOpen,
  Rocket,
  Square,
  Layout,
  Settings,
  Check,
  Copy,
  ChevronDown,
  ChevronRight,
  Globe,
  Power,
  Lock,
  Moon,
  RefreshCw,
  AlertTriangle,
  Info,
  ScanLine,
  PanelRightClose,
  type LucideIcon,
} from 'lucide-react'
import type { ToolData } from '../../types'
import styles from './ToolResponseCard.module.css'

/* ─── Tool-to-Icon mapping ─── */

const toolIconMap: Record<string, LucideIcon> = {
  open_app: AppWindow,
  close_app: XSquare,
  force_close_app: Terminal,
  restart_app: RotateCw,
  focus_app: ScanLine,
  get_app_details: Info,
  get_active_window: Square,
  window_list: Layout,
  minimize_app: PanelRightClose,
  maximize_app: AppWindow,
  snap_window: Layout,
  get_system_info: Monitor,
  get_clipboard: Clipboard,
  set_clipboard: Clipboard,
  list_startup_apps: Rocket,
  file_explorer: FolderOpen,
  open_app_folder: FolderOpen,
  open_url: Globe,
  restart_pc: RefreshCw,
  hibernate_pc: Moon,
  lock_pc: Lock,
}

function getToolIcon(toolId: string): LucideIcon {
  return toolIconMap[toolId] ?? Settings
}

/* ─── Status helpers ─── */

type CardStatus = 'success' | 'error' | 'warning' | 'info'

function getCardStatus(toolData: ToolData): CardStatus {
  if (!toolData || !toolData.status) return 'info'
  const s = toolData.status.toLowerCase()
  if (s === 'success') return 'success'
  if (s === 'failed' || s === 'error') return 'error'
  if (s === 'warning') return 'warning'
  return 'info'
}

function getStatusLabel(toolData: ToolData): string {
  if (!toolData || !toolData.status) return 'Info'
  return toolData.status
}

/* ─── Title builder ─── */

function buildTitle(toolData: ToolData): string {
  const exec = toolData.execution ?? {}
  const toolName = toolData.tool?.name ?? toolData.tool?.id ?? ''
  const app = (exec.app as string) || (exec.app_name as string) || ''
  const status = toolData.status?.toLowerCase() ?? ''

  if (status === 'success') {
    if (app) {
      const action = toolName.replace(/_/g, ' ')
      return `${action}: ${app}`
    }
    return `${toolName.replace(/_/g, ' ')} completed`
  }

  if (status === 'failed' || status === 'error') {
    const err = (exec.error as string) || toolData.reason || ''
    if (app) return `${toolName.replace(/_/g, ' ')} failed for ${app}`
    if (err) return `${toolName.replace(/_/g, ' ')} failed`
    return `${toolName.replace(/_/g, ' ')} failed`
  }

  if (app) return `${toolName.replace(/_/g, ' ')}: ${app}`
  return toolName.replace(/_/g, ' ')
}

function buildDescription(toolData: ToolData): string {
  const exec = toolData.execution ?? {}
  const msg = (exec.message as string) || ''
  const err = (exec.error as string) || toolData.reason || ''
  return msg || err || ''
}

/* ─── CopyButton ─── */

function CopyButton({ text, label }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    } catch {
      /* silent */
    }
  }, [text])

  return (
    <button
      className={`${styles.copyBtn} ${copied ? styles.copied : ''}`}
      onClick={handleCopy}
      aria-label={label ?? 'Copy to clipboard'}
      title={label ?? 'Copy'}
    >
      {copied ? <Check size={14} /> : <Copy size={14} />}
    </button>
  )
}

/* ─── CollapsibleSection ─── */

function CollapsibleSection({
  label,
  children,
  defaultOpen = false,
}: {
  label: string
  children: ReactNode
  defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div>
      <button
        className={styles.collapsibleToggle}
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        {label}
      </button>
      <div className={`${styles.collapsibleContent} ${open ? styles.open : styles.closed}`}>
        {children}
      </div>
    </div>
  )
}

/* ─── MetadataTable ─── */

function MetadataTable({ data }: { data: Record<string, string | number | boolean | null> }) {
  const entries = Object.entries(data).filter(([, v]) => v !== null && v !== '')
  if (!entries.length) return null

  return (
    <div className={styles.metadata}>
      {entries.map(([key, value]) => (
        <div key={key} style={{ display: 'contents' }}>
          <span className={styles.metadataLabel}>
            {key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
          </span>
          <span className={styles.metadataValue}>
            {String(value)}
            {key.endsWith('_gb') ? ' GB' : ''}
          </span>
        </div>
      ))}
    </div>
  )
}

/* ─── SkeletonCard ─── */

export function ToolResponseSkeleton() {
  return (
    <div className={styles.skeleton}>
      <div className={styles.skeletonLine} />
      <div className={styles.skeletonLine} />
      <div className={styles.skeletonLine} />
    </div>
  )
}

/* ═══════════════════════════════════════
   Tool-specific renderers
   ═══════════════════════════════════════ */

function renderOpenApp(exec: Record<string, unknown>) {
  const params = exec.params as Record<string, unknown> | undefined
  const path = (params?.app_path as string) || ''
  const name = path.split('\\').pop() || path.split('/').pop() || ''
  return (
    <MetadataTable
      data={{
        application: name.replace(/\.exe$/i, ''),
        path,
      }}
    />
  )
}

function renderCloseApp(exec: Record<string, unknown>) {
  const app = (exec.app as string) || ''
  return <MetadataTable data={{ application: app }} />
}

function renderForceCloseApp(exec: Record<string, unknown>) {
  const app = (exec.app as string) || ''
  return <MetadataTable data={{ application: app }} />
}

function renderRestartApp(exec: Record<string, unknown>) {
  const app = (exec.app as string) || ''
  const data = exec.data as Record<string, unknown> | undefined
  return (
    <MetadataTable
      data={{
        application: app,
        ...(data?.pid ? { pid: data.pid as number } : {}),
      }}
    />
  )
}

function renderFocusApp(exec: Record<string, unknown>) {
  const app = (exec.app_name as string) || (exec.app as string) || ''
  return <MetadataTable data={{ application: app }} />
}

function renderAppDetails(exec: Record<string, unknown>) {
  const data = exec.data as Record<string, unknown> | undefined
  if (!data) return null
  return (
    <MetadataTable
      data={{
        name: data.name as string,
        version: data.version as string,
        publisher: data.publisher as string,
        'install location': data.install_location as string,
        running: data.running ? 'Yes' : 'No',
        windows: data.windows as number,
        path: data.path as string,
      }}
    />
  )
}

function renderActiveWindow(exec: Record<string, unknown>) {
  const data = exec.data as Record<string, unknown> | undefined
  const title = (data?.title as string) || ''
  const process = (data?.process as string) || ''
  const path = (data?.path as string) || ''
  return (
    <MetadataTable
      data={{
        title,
        process,
        ...(path ? { path } : {}),
      }}
    />
  )
}

function renderMinimizeApp(exec: Record<string, unknown>) {
  const app = (exec.app_name as string) || ''
  return <MetadataTable data={{ application: app }} />
}

function renderMaximizeApp(exec: Record<string, unknown>) {
  const app = (exec.app_name as string) || ''
  return <MetadataTable data={{ application: app }} />
}

function renderSnapWindow(exec: Record<string, unknown>) {
  const app = (exec.app_name as string) || ''
  const pos = (exec.position as string) || ''
  return (
    <MetadataTable
      data={{
        application: app,
        ...(pos ? { position: pos } : {}),
      }}
    />
  )
}

function renderSystemInfo(exec: Record<string, unknown>) {
  const data = exec.data as Record<string, unknown> | undefined
  if (!data) return null

  const system = data.system as string
  const release = data.release as string
  const version = data.version as string
  const machine = data.machine as string
  const processor = data.processor as string
  const cpuCount = data.cpu_count as number
  const cpuPhysical = data.cpu_physical as number
  const ramTotal = data.ram_total_gb as number
  const ramAvail = data.ram_available_gb as number
  const diskTotal = data.disk_c_total_gb as number
  const diskFree = data.disk_c_free_gb as number

  return (
    <>
      <div className={styles.sysSection}>
        <div className={styles.sectionLabel}>Operating System</div>
        <div className={styles.gridRow}>
          <span className={styles.gridLabel}>OS</span>
          <span className={styles.gridValue}>{system} {release}</span>
        </div>
        <div className={styles.gridRow}>
          <span className={styles.gridLabel}>Version</span>
          <span className={styles.gridValue}>{version}</span>
        </div>
      </div>

      <div className={styles.sysSection}>
        <div className={styles.sectionLabel}>CPU</div>
        <div className={styles.gridRow}>
          <span className={styles.gridLabel}>Model</span>
          <span className={styles.gridValue}>{processor || machine}</span>
        </div>
        <div className={styles.gridRow}>
          <span className={styles.gridLabel}>Cores</span>
          <span className={styles.gridValue}>{cpuPhysical} physical / {cpuCount} logical</span>
        </div>
      </div>

      {ramTotal ? (
        <div className={styles.sysSection}>
          <div className={styles.sectionLabel}>Memory</div>
          <div className={styles.gridRow}>
            <span className={styles.gridLabel}>Total</span>
            <span className={styles.gridValue}>{ramTotal} GB</span>
          </div>
          <div className={styles.gridRow}>
            <span className={styles.gridLabel}>Available</span>
            <span className={styles.gridValue}>{ramAvail} GB</span>
          </div>
        </div>
      ) : null}

      {diskTotal ? (
        <div className={styles.sysSection}>
          <div className={styles.sectionLabel}>Drive C:</div>
          <div className={styles.gridRow}>
            <span className={styles.gridLabel}>Total</span>
            <span className={styles.gridValue}>{diskTotal} GB</span>
          </div>
          <div className={styles.gridRow}>
            <span className={styles.gridLabel}>Free</span>
            <span className={styles.gridValue}>{diskFree} GB</span>
          </div>
        </div>
      ) : null}
    </>
  )
}

function renderClipboard(exec: Record<string, unknown>) {
  const data = exec.data as Record<string, unknown> | undefined
  const text = (data?.text as string) || ''
  const length = (data?.length as number) || 0

  if (!text) {
    return <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>Clipboard is empty</span>
  }

  return (
    <div>
      <div className={styles.codeBlockHeader}>
        <span className={styles.codeBlockLabel}>{length} characters</span>
        <CopyButton text={text} label="Copy clipboard content" />
      </div>
      <pre className={styles.codeBlock}>{text}</pre>
    </div>
  )
}

function renderSetClipboard(exec: Record<string, unknown>) {
  const data = exec.data as Record<string, unknown> | undefined
  const length = (data?.length as number) || 0
  return <MetadataTable data={{ chars: length }} />
}

function renderWindowList(exec: Record<string, unknown>) {
  const windows = exec.data as Array<Record<string, unknown>> | undefined
  if (!windows || !windows.length) {
    return <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>No windows found</span>
  }

  return (
    <div className={styles.scrollableList}>
      {windows.map((w, i) => (
        <div key={w.hwnd as string ?? i} className={styles.listItem}>
          <div className={styles.listItemIcon}>
            <Layout size={16} />
          </div>
          <div className={styles.listItemContent}>
            <div className={styles.listItemTitle}>{(w.title as string) || '(untitled)'}</div>
            <div className={styles.listItemSub}>{(w.process as string) || ''}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

function renderStartupApps(exec: Record<string, unknown>) {
  const apps = exec.data as Array<Record<string, unknown>> | undefined
  if (!apps || !apps.length) {
    return <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>No startup apps found</span>
  }

  return (
    <table className={styles.startupTable}>
      <thead>
        <tr>
          <th>Name</th>
          <th>Status</th>
          <th>Path</th>
        </tr>
      </thead>
      <tbody>
        {apps.map((app, i) => (
          <tr key={`${app.name as string}-${i}`}>
            <td>{(app.name as string) || ''}</td>
            <td>
              <span className={`${styles.enabledBadge} ${(app.enabled as boolean) ? styles.on : styles.off}`}>
                {(app.enabled as boolean) ? 'Enabled' : 'Disabled'}
              </span>
            </td>
            <td>{(app.path as string) || ''}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function renderFileExplorer(exec: Record<string, unknown>) {
  const path = (exec.path as string) || ''
  return path ? <MetadataTable data={{ path }} /> : null
}

function renderOpenUrl(exec: Record<string, unknown>) {
  const params = exec.params as Record<string, unknown> | undefined
  const url = (params?.url as string) || ''
  return url ? <MetadataTable data={{ url }} /> : null
}

function renderGeneric(exec: Record<string, unknown>) {
  const data = exec.data as Record<string, unknown> | undefined
  if (!data) return null
  const entries = Object.entries(data).filter(([, v]) => v !== null && v !== undefined)
  if (!entries.length) return null
  return <MetadataTable data={Object.fromEntries(entries) as Record<string, string | number | boolean | null>} />
}

/* ─── Renderer registry ─── */

const renderers: Record<string, (exec: Record<string, unknown>) => ReactNode> = {
  open_app: renderOpenApp,
  close_app: renderCloseApp,
  force_close_app: renderForceCloseApp,
  restart_app: renderRestartApp,
  focus_app: renderFocusApp,
  get_app_details: renderAppDetails,
  get_active_window: renderActiveWindow,
  window_list: renderWindowList,
  minimize_app: renderMinimizeApp,
  maximize_app: renderMaximizeApp,
  snap_window: renderSnapWindow,
  get_system_info: renderSystemInfo,
  get_clipboard: renderClipboard,
  set_clipboard: renderSetClipboard,
  list_startup_apps: renderStartupApps,
  file_explorer: renderFileExplorer,
  open_app_folder: renderFileExplorer,
  open_url: renderOpenUrl,
}

/* ═══════════════════════════════════════
   Main ToolResponseCard component
   ═══════════════════════════════════════ */

interface ToolResponseCardProps {
  toolData: ToolData
  timestamp?: number
}

export default function ToolResponseCard({ toolData, timestamp }: ToolResponseCardProps) {
  const status = getCardStatus(toolData)
  const exec = toolData.execution ?? {}
  const toolId = toolData.tool?.id ?? ''
  const Icon = getToolIcon(toolId)
  const title = buildTitle(toolData)
  const description = buildDescription(toolData)

  const renderBody = renderers[toolId] ?? renderGeneric
  const body = renderBody(exec)

  const rawJson = exec ? JSON.stringify(exec, null, 2) : ''
  const timeStr = timestamp
    ? new Date(timestamp).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : ''

  return (
    <div className={`${styles.card} ${styles[status]}`}>
      <div className={styles.header}>
        <div className={styles.iconCircle}>
          <Icon size={18} />
        </div>
        <div className={styles.headerContent}>
          <div className={styles.titleRow}>
            <span className={styles.title}>{title}</span>
            <span className={styles.statusBadge}>{getStatusLabel(toolData)}</span>
          </div>
          {description && <div className={styles.description}>{description}</div>}
        </div>
      </div>

      {body && <div className={styles.body}>{body}</div>}

      <div className={styles.divider} />

      <div className={styles.footer}>
        <span className={styles.timestamp}>{timeStr}</span>
        <div className={styles.footerActions}>
          {rawJson && (
            <CollapsibleSection label="Show Raw JSON">
              <pre className={styles.rawJson}>{rawJson}</pre>
            </CollapsibleSection>
          )}
        </div>
      </div>
    </div>
  )
}
