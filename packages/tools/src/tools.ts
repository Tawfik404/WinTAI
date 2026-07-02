export interface ToolParameter {
  name: string
  type: 'string' | 'number' | 'boolean'
  description: string
  required?: boolean
}

export interface ToolDefinition {
  name: string
  description: string
  parameters: ToolParameter[]
}

export const toolDefinitions: ToolDefinition[] = [
  {
    name: 'open_app',
    description: 'Launch a Windows application by name or path',
    parameters: [
      {
        name: 'name',
        type: 'string',
        description: 'Application name or executable path',
        required: true,
      },
    ],
  },
  {
    name: 'open_url',
    description: 'Open a URL in the default browser',
    parameters: [
      {
        name: 'url',
        type: 'string',
        description: 'The URL to open',
        required: true,
      },
    ],
  },
  {
    name: 'shutdown',
    description: 'Shut down or restart the system',
    parameters: [
      {
        name: 'action',
        type: 'string',
        description: 'shutdown | restart | hibernate',
        required: true,
      },
    ],
  },
]
