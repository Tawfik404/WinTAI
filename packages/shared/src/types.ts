export interface ToolRequest {
  tool: string
  parameters: Record<string, unknown>
}

export interface ToolResponse {
  accepted: boolean
  result?: unknown
  error?: string
}

export interface ExecutionResult {
  stdout: string
  stderr: string
  exitCode: number
}

export interface HealthStatus {
  status: string
}
