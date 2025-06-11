import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface ChatRequest {
  message: string
  session_id: string
  user_id?: string
}

export interface ChatResponse {
  message: string
  session_id: string
  is_complete: boolean
  next_step: string
  collected_data: Record<string, any>
}

export interface SessionResponse {
  session_id: string
  user_id: string
  messages: Array<{ role: string; content: string }>
  current_step: string
  collected_data: Record<string, any>
  is_complete: boolean
  created_at?: string
  updated_at?: string
}

export interface TicketResponse {
  ticket_id: string
  subject: string
  description: string
  category: string
  assignee: string
  priority: string
  status: string
  requester_email: string
  member_details: Record<string, any>
  created_at: string
}

export interface ZendeskTicketsResponse {
  tickets: Array<{
    id: string
    subject: string
    description: string
    status: string
    priority: string
    requester_email: string
    created_at: string
    updated_at: string
    tags: string[]
  }>
  total: number
}

export const apiClient = {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await api.post('/api/chat', request)
    return response.data
  },

  async getSession(sessionId: string): Promise<SessionResponse> {
    const response = await api.get(`/api/session/${sessionId}`)
    return response.data
  },

  async getTicket(sessionId: string): Promise<TicketResponse> {
    const response = await api.get(`/api/ticket/${sessionId}`)
    return response.data
  },

  async downloadSummary(sessionId: string): Promise<Blob> {
    const response = await api.get(`/api/summary/${sessionId}`, {
      responseType: 'blob',
    })
    return response.data
  },

  async uploadZendeskDatadump(file: File): Promise<{ message: string; imported_count: number }> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/api/zendesk/datadump', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async getZendeskTickets(limit = 50, offset = 0): Promise<ZendeskTicketsResponse> {
    const response = await api.get('/api/zendesk/tickets', {
      params: { limit, offset },
    })
    return response.data
  },
}
