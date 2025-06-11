import { useState } from 'react'
import { ChatInterface } from '@/components/ChatInterface'
import { TicketSummary } from '@/components/TicketSummary'
import { PDFDownload } from '@/components/PDFDownload'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function EnrollmentPage() {
  const [sessionId, setSessionId] = useState<string>('')
  const [isComplete, setIsComplete] = useState<boolean>(false)

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Membership Enrollment</h1>
        <p className="text-gray-600">
          Chat with our AI assistant to complete your membership enrollment
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>AI Assistant</CardTitle>
              <CardDescription>
                Start a conversation to begin your enrollment process
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ChatInterface
                onSessionUpdate={(id, complete) => {
                  setSessionId(id)
                  setIsComplete(complete)
                }}
              />
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          {sessionId && (
            <Tabs defaultValue="summary" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="summary">Summary</TabsTrigger>
                <TabsTrigger value="ticket">Ticket</TabsTrigger>
              </TabsList>
              <TabsContent value="summary">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Enrollment Summary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <TicketSummary sessionId={sessionId} />
                    {isComplete && (
                      <div className="mt-4">
                        <PDFDownload sessionId={sessionId} />
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
              <TabsContent value="ticket">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Ticket Details</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <TicketSummary sessionId={sessionId} showTicketDetails />
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          )}

          {!sessionId && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Getting Started</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-gray-600">
                  Start chatting with our AI assistant to begin your enrollment.
                </p>
                <div className="space-y-2">
                  <h4 className="font-medium">We'll collect:</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Your full name</li>
                    <li>• Email address</li>
                    <li>• Company information</li>
                    <li>• Program preferences</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
