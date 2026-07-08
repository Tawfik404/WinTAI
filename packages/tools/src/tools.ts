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
    name: 'close_app',
    description: 'Gracefully close a running application',
    parameters: [
      {
        name: 'app_name',
        type: 'string',
        description: 'Name of the application to close',
        required: true,
      },
    ],
  },
  {
    name: 'focus_app',
    description: 'Bring an application window to the foreground',
    parameters: [
      {
        name: 'app_name',
        type: 'string',
        description: 'Name of the application to focus',
        required: true,
      },
    ],
  },
  {
    name: 'restart_app',
    description: 'Restart a running application',
    parameters: [
      {
        name: 'app_name',
        type: 'string',
        description: 'Name of the application to restart',
        required: true,
      },
    ],
  },
  {
    name: 'force_close_app',
    description: 'Forcefully terminate a frozen or unresponsive application',
    parameters: [
      {
        name: 'app_name',
        type: 'string',
        description: 'Name of the application to force close',
        required: true,
      },
    ],
  },
  {
    name: 'open_app_folder',
    description: 'Open the installation directory of an application',
    parameters: [
      {
        name: 'app_name',
        type: 'string',
        description: 'Name of the application',
        required: true,
      },
    ],
  },
  {
    name: 'get_app_details',
    description: 'Return detailed metadata about an application',
    parameters: [
      {
        name: 'app_name',
        type: 'string',
        description: 'Name of the application',
        required: true,
      },
    ],
  },
  {
    name: 'get_active_window',
    description: 'Return information about the currently focused window',
    parameters: [],
  },
  {
    name: 'window_list',
    description: 'List all currently open user-facing windows',
    parameters: [],
  },
  {
    name: 'minimize_app',
    description: 'Minimize an application window to the taskbar',
    parameters: [
      {
        name: 'app_name',
        type: 'string',
        description: 'Name of the application to minimize',
        required: true,
      },
    ],
  },
  {
    name: 'maximize_app',
    description: 'Maximize an application window to fill the screen',
    parameters: [
      {
        name: 'app_name',
        type: 'string',
        description: 'Name of the application to maximize',
        required: true,
      },
    ],
  },
  {
    name: 'snap_window',
    description: 'Snap an application window to a screen region (left, right, top, bottom)',
    parameters: [
      {
        name: 'app_name',
        type: 'string',
        description: 'Name of the application to snap',
        required: true,
      },
      {
        name: 'position',
        type: 'string',
        description: 'Snap position: left, right, top, or bottom',
        required: true,
      },
    ],
  },
  {
    name: 'list_startup_apps',
    description: 'List programs that launch automatically when Windows starts',
    parameters: [],
  },
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
]
