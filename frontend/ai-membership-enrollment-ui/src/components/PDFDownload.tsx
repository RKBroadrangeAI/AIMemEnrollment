import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Download, FileText } from 'lucide-react'
import { apiClient } from '@/services/api'
import { useToast } from '@/hooks/use-toast'

interface PDFDownloadProps {
  sessionId: string
}

export function PDFDownload({ sessionId }: PDFDownloadProps) {
  const [isDownloading, setIsDownloading] = useState(false)
  const { toast } = useToast()

  const downloadPDF = async () => {
    try {
      setIsDownloading(true)
      const blob = await apiClient.downloadSummary(sessionId)
      
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `enrollment_summary_${sessionId}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast({
        title: "Success",
        description: "Enrollment summary downloaded successfully!",
      })
    } catch (error) {
      console.error('Download error:', error)
      toast({
        title: "Error",
        description: "Failed to download summary. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <FileText className="h-5 w-5 text-gray-500" />
        <span className="text-sm font-medium">Enrollment Summary</span>
      </div>
      
      <Button 
        onClick={downloadPDF} 
        disabled={isDownloading}
        className="w-full"
        variant="outline"
      >
        <Download className="h-4 w-4 mr-2" />
        {isDownloading ? 'Generating PDF...' : 'Download PDF Summary'}
      </Button>
      
      <p className="text-xs text-gray-500">
        Download a comprehensive PDF summary of your enrollment details
      </p>
    </div>
  )
}
