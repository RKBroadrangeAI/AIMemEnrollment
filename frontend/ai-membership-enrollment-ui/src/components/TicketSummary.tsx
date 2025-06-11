import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { apiClient } from '@/services/api'
import { useToast } from '@/hooks/use-toast'

interface TicketSummaryProps {
  sessionId: string
  showTicketDetails?: boolean
}

interface SessionData {
  name?: string
  email?: string
  program_type?: string
  company?: string
  job_title?: string
}

interface TicketData {
  ticket_id: string
  subject: string
  description: string
  category: string
  assignee: string
  priority: string
  status: string
  requester_email: string
  member_details: SessionData
  created_at: string
}

export function TicketSummary({ sessionId, showTicketDetails = false }: TicketSummaryProps) {
  const [sessionData, setSessionData] = useState<SessionData | null>(null)
  const [ticketData, setTicketData] = useState<TicketData | null>(null)
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        
        if (showTicketDetails) {
          const ticket = await apiClient.getTicket(sessionId)
          setTicketData(ticket)
        } else {
          const session = await apiClient.getSession(sessionId)
          setSessionData(session.collected_data || {})
        }
      } catch (error) {
        console.error('Error fetching data:', error)
        toast({
          title: "Error",
          description: "Failed to load data. Please try again.",
          variant: "destructive",
        })
      } finally {
        setLoading(false)
      }
    }

    if (sessionId) {
      fetchData()
    }
  }, [sessionId, showTicketDetails, toast])

  if (loading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </div>
    )
  }

  if (showTicketDetails && ticketData) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Ticket #{ticketData.ticket_id.slice(0, 8)}</h3>
          <Badge variant={ticketData.status === 'open' ? 'default' : 'secondary'}>
            {ticketData.status.toUpperCase()}
          </Badge>
        </div>
        
        <div className="space-y-2">
          <div>
            <span className="font-medium">Subject:</span>
            <p className="text-sm text-gray-600">{ticketData.subject}</p>
          </div>
          
          <div>
            <span className="font-medium">Description:</span>
            <p className="text-sm text-gray-600">{ticketData.description}</p>
          </div>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">Category:</span>
              <p className="text-gray-600">{ticketData.category}</p>
            </div>
            <div>
              <span className="font-medium">Priority:</span>
              <p className="text-gray-600">{ticketData.priority}</p>
            </div>
            <div>
              <span className="font-medium">Assignee:</span>
              <p className="text-gray-600">{ticketData.assignee}</p>
            </div>
            <div>
              <span className="font-medium">Created:</span>
              <p className="text-gray-600">
                {new Date(ticketData.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!showTicketDetails && sessionData) {
    return (
      <div className="space-y-3">
        {sessionData.name && (
          <div>
            <span className="font-medium">Name:</span>
            <p className="text-sm text-gray-600">{sessionData.name}</p>
          </div>
        )}
        
        {sessionData.email && (
          <div>
            <span className="font-medium">Email:</span>
            <p className="text-sm text-gray-600">{sessionData.email}</p>
          </div>
        )}
        
        {sessionData.company && (
          <div>
            <span className="font-medium">Company:</span>
            <p className="text-sm text-gray-600">{sessionData.company}</p>
          </div>
        )}
        
        {sessionData.program_type && (
          <div>
            <span className="font-medium">Program:</span>
            <Badge variant="outline">{sessionData.program_type}</Badge>
          </div>
        )}
        
        {sessionData.job_title && (
          <div>
            <span className="font-medium">Job Title:</span>
            <p className="text-sm text-gray-600">{sessionData.job_title}</p>
          </div>
        )}
      </div>
    )
  }

  return (
    <p className="text-sm text-gray-500">
      {showTicketDetails ? 'No ticket data available' : 'No enrollment data available'}
    </p>
  )
}
