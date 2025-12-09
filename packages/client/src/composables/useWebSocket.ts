/**
 * Real-time Monitoring WebSocket Composable (N10.0)
 * 
 * Provides reactive WebSocket connection with auto-reconnection.
 * 
 * Usage:
 * const { connect, disconnect, isConnected, subscribe } = useWebSocket()
 * await connect()
 * subscribe(['job', 'metrics'], (event) => { console.log(event) })
 */
import { ref, onUnmounted } from 'vue'

interface WebSocketEvent {
  type: string
  data: any
  timestamp: string
}

type EventHandler = (event: WebSocketEvent) => void

export function useWebSocket() {
  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectDelay = ref(1000) // Start at 1s, exponential backoff
  const eventHandlers = ref<EventHandler[]>([])

  const connect = async (baseUrl?: string) => {
    const wsUrl = baseUrl || `ws://${window.location.hostname}:8000/ws/monitor`
    
    try {
      ws.value = new WebSocket(wsUrl)
      
      ws.value.onopen = () => {
        console.log('[N10.0] WebSocket connected')
        isConnected.value = true
        reconnectAttempts.value = 0
        reconnectDelay.value = 1000
      }
      
      ws.value.onmessage = (event) => {
        try {
          const message: WebSocketEvent = JSON.parse(event.data)
          
          // Skip system messages for event handlers
          if (!message.type.startsWith('system:')) {
            eventHandlers.value.forEach(handler => handler(message))
          } else {
            console.log('[N10.0] System message:', message.type, message.data)
          }
        } catch (error) {
          console.error('[N10.0] Failed to parse WebSocket message:', error)
        }
      }
      
      ws.value.onerror = (error) => {
        console.error('[N10.0] WebSocket error:', error)
      }
      
      ws.value.onclose = () => {
        console.log('[N10.0] WebSocket closed')
        isConnected.value = false
        
        // Auto-reconnect with exponential backoff
        if (reconnectAttempts.value < maxReconnectAttempts) {
          reconnectAttempts.value++
          console.log(`[N10.0] Reconnecting in ${reconnectDelay.value}ms (attempt ${reconnectAttempts.value}/${maxReconnectAttempts})`)
          
          setTimeout(() => {
            connect(baseUrl)
          }, reconnectDelay.value)
          
          // Exponential backoff (1s → 2s → 4s → 8s → 16s)
          reconnectDelay.value = Math.min(reconnectDelay.value * 2, 16000)
        } else {
          console.error('[N10.0] Max reconnection attempts reached')
        }
      }
    } catch (error) {
      console.error('[N10.0] WebSocket connection failed:', error)
    }
  }
  
  const disconnect = () => {
    if (ws.value) {
      ws.value.close()
      ws.value = null
      isConnected.value = false
      reconnectAttempts.value = maxReconnectAttempts // Prevent auto-reconnect
    }
  }
  
  const subscribe = (filters: string[], handler: EventHandler) => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      // Send subscription command
      ws.value.send(JSON.stringify({
        action: 'subscribe',
        filters
      }))
    }
    
    // Register event handler
    eventHandlers.value.push(handler)
    
    // Return unsubscribe function
    return () => {
      const index = eventHandlers.value.indexOf(handler)
      if (index > -1) {
        eventHandlers.value.splice(index, 1)
      }
    }
  }
  
  const ping = () => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({ action: 'ping' }))
    }
  }
  
  // Auto-disconnect on component unmount
  onUnmounted(() => {
    disconnect()
  })
  
  return {
    connect,
    disconnect,
    isConnected,
    subscribe,
    ping,
    reconnectAttempts
  }
}
