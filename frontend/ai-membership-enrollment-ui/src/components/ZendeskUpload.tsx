import React, { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react'
import { apiClient } from '@/services/api'
import { useToast } from '@/hooks/use-toast'

export function ZendeskUpload() {
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadResult, setUploadResult] = useState<{
    success: boolean
    message: string
    count?: number
  } | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

  const handleFileSelect = () => {
    fileInputRef.current?.click()
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.json') && !file.name.endsWith('.csv')) {
      toast({
        title: "Invalid file type",
        description: "Please upload a JSON or CSV file.",
        variant: "destructive",
      })
      return
    }

    try {
      setUploading(true)
      setUploadProgress(0)
      setUploadResult(null)

      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90))
      }, 200)

      const result = await apiClient.uploadZendeskDatadump(file)
      
      clearInterval(progressInterval)
      setUploadProgress(100)
      
      setUploadResult({
        success: true,
        message: result.message,
        count: result.imported_count
      })
      
      toast({
        title: "Upload successful",
        description: `Imported ${result.imported_count} tickets successfully.`,
      })
    } catch (error) {
      console.error('Upload error:', error)
      setUploadResult({
        success: false,
        message: 'Failed to upload file. Please try again.'
      })
      
      toast({
        title: "Upload failed",
        description: "Failed to upload datadump. Please try again.",
        variant: "destructive",
      })
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <div className="space-y-6">
      <Card className="border-dashed border-2 border-gray-300 hover:border-gray-400 transition-colors">
        <CardContent className="text-center py-8">
          <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Upload Zendesk Datadump
          </h3>
          <p className="text-gray-500 mb-4">
            Select a JSON or CSV file exported from Zendesk
          </p>
          
          <Button 
            onClick={handleFileSelect} 
            disabled={uploading}
            className="mb-4"
          >
            <FileText className="h-4 w-4 mr-2" />
            Choose File
          </Button>
          
          <input
            ref={fileInputRef}
            type="file"
            accept=".json,.csv"
            onChange={handleFileUpload}
            className="hidden"
          />
          
          <div className="text-xs text-gray-500">
            Supported formats: JSON, CSV (max 10MB)
          </div>
        </CardContent>
      </Card>

      {uploading && (
        <Card>
          <CardContent className="py-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Uploading and processing...</span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} className="w-full" />
            </div>
          </CardContent>
        </Card>
      )}

      {uploadResult && (
        <Card className={uploadResult.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
          <CardContent className="py-4">
            <div className="flex items-center space-x-2">
              {uploadResult.success ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600" />
              )}
              <div>
                <p className={`font-medium ${uploadResult.success ? 'text-green-800' : 'text-red-800'}`}>
                  {uploadResult.success ? 'Upload Successful' : 'Upload Failed'}
                </p>
                <p className={`text-sm ${uploadResult.success ? 'text-green-600' : 'text-red-600'}`}>
                  {uploadResult.message}
                  {uploadResult.count && ` (${uploadResult.count} tickets imported)`}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="py-4">
          <h4 className="font-medium mb-2">Sample Datadump Format</h4>
          <div className="text-sm text-gray-600 space-y-2">
            <p><strong>JSON format:</strong></p>
            <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
{`[
  {
    "id": "12345",
    "subject": "Membership Question",
    "description": "User inquiry about premium membership",
    "status": "open",
    "priority": "normal",
    "requester_email": "user@example.com",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "tags": ["membership", "premium"]
  }
]`}
            </pre>
            <p><strong>CSV format:</strong> Headers should match the JSON field names above.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
