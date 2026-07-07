interface Window {
  electronAPI?: {
    platform: string
    hasGoogleApiKey?: boolean
    onBackendStatus?: (callback: (status: any) => void) => void
  }
}



