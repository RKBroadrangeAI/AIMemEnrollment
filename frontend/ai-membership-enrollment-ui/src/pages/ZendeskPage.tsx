import { ZendeskTickets } from '@/components/ZendeskTickets'
import { ZendeskUpload } from '@/components/ZendeskUpload'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function ZendeskPage() {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Zendesk Integration</h1>
        <p className="text-gray-600">
          Manage Zendesk tickets and import datadumps for analytics
        </p>
      </div>

      <Tabs defaultValue="tickets" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="tickets">View Tickets</TabsTrigger>
          <TabsTrigger value="upload">Import Datadump</TabsTrigger>
        </TabsList>
        
        <TabsContent value="tickets">
          <Card>
            <CardHeader>
              <CardTitle>Zendesk Tickets</CardTitle>
              <CardDescription>
                View imported tickets from Zendesk datadumps
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ZendeskTickets />
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="upload">
          <Card>
            <CardHeader>
              <CardTitle>Import Datadump</CardTitle>
              <CardDescription>
                Upload JSON or CSV files from Zendesk for analytics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ZendeskUpload />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
