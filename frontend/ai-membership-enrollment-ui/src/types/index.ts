export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface EnrollmentData {
  name?: string
  email?: string
  program_type?: string
  company?: string
  job_title?: string
  referral_source?: string
}

export interface SessionData {
  session_id: string
  user_id: string
  messages: Message[]
  current_step: string
  collected_data: EnrollmentData
  is_complete: boolean
  created_at?: string
  updated_at?: string
}

export interface TicketData {
  ticket_id: string
  subject: string
  description: string
  category: string
  assignee: string
  priority: string
  status: string
  requester_email: string
  member_details: EnrollmentData
  created_at: string
}

export interface ZendeskTicket {
  id: string
  subject: string
  description: string
  status: string
  priority: string
  requester_email: string
  created_at: string
  updated_at: string
  tags: string[]
}
