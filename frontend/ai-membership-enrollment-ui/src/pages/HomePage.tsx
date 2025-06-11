import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Link } from 'react-router-dom'
import { Bot, Users, Ticket, FileText } from 'lucide-react'

export function HomePage() {
  const features = [
    {
      icon: Bot,
      title: 'AI-Powered Conversations',
      description: 'Natural language bot using OpenAI GPT-4 for seamless enrollment',
    },
    {
      icon: Users,
      title: 'Automated Enrollment',
      description: 'Streamlined membership enrollment with intelligent data collection',
    },
    {
      icon: Ticket,
      title: 'Ticket Management',
      description: 'Automatic ticket generation and Zendesk integration',
    },
    {
      icon: FileText,
      title: 'PDF Summaries',
      description: 'Generate and download enrollment summaries instantly',
    },
  ]

  return (
    <div className="space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-gray-900">
          Welcome to AI Membership Enrollment
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Automate your membership enrollment process with our intelligent AI assistant.
          Reduce manual processing time by 50% and achieve 80% conversation completion.
        </p>
        <div className="flex justify-center space-x-4">
          <Button asChild size="lg">
            <Link to="/enrollment">Start Enrollment</Link>
          </Button>
          <Button variant="outline" size="lg" asChild>
            <Link to="/zendesk">View Tickets</Link>
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {features.map(({ icon: Icon, title, description }) => (
          <Card key={title} className="text-center">
            <CardHeader>
              <div className="mx-auto w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Icon className="h-6 w-6 text-blue-600" />
              </div>
              <CardTitle className="text-lg">{title}</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>{description}</CardDescription>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>How It Works</CardTitle>
          <CardDescription>
            Our AI-powered enrollment process is designed to be simple and efficient
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center space-y-2">
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto font-bold">
                1
              </div>
              <h3 className="font-semibold">Start Conversation</h3>
              <p className="text-sm text-gray-600">
                Begin chatting with our AI assistant about your membership needs
              </p>
            </div>
            <div className="text-center space-y-2">
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto font-bold">
                2
              </div>
              <h3 className="font-semibold">Provide Information</h3>
              <p className="text-sm text-gray-600">
                Answer questions about your name, email, company, and program preferences
              </p>
            </div>
            <div className="text-center space-y-2">
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto font-bold">
                3
              </div>
              <h3 className="font-semibold">Complete Enrollment</h3>
              <p className="text-sm text-gray-600">
                Get your ticket generated and download your enrollment summary
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
