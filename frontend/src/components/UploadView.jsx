import React, { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload } from 'lucide-react'
import axios from 'axios'

// UploadView: Accepts file upload and query input, dispatches analysis task
function UploadView({ onSubmit }) {
  const [file, setFile] = useState(null)
  const [query, setQuery] = useState('')
  const [promptVersion, setPromptVersion] = useState('v3')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'audio/mpeg': ['.mp3'],
      'audio/wav': ['.wav'],
      'application/vnd.ms-excel': ['.xlsx'],
      'application/vnd.ms-powerpoint': ['.pptx'],
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setFile(acceptedFiles[0])
        setError('')
      }
    },
  })

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!file || !query.trim()) {
      setError('Please provide both file and query')
      return
    }

    setLoading(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('query', query)
      formData.append('prompt_version', promptVersion)

      const response = await axios.post('/api/v1/analyze', formData)

      onSubmit(response.data.task_id, response.data.session_id)
    } catch (err) {
      setError(`Upload failed: ${err.response?.data?.detail || err.message}`)
      setLoading(false)
    }
  }

  const canSubmit = file && query.trim() && !loading

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-6">
      <div className="w-full max-w-2xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Dropzone */}
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition ${
              isDragActive
                ? 'border-brand-500 bg-blue-900/20'
                : 'border-gray-600 hover:border-gray-500 bg-gray-800/50'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="text-gray-300 font-medium">
              {isDragActive ? 'Drop file here' : 'Drag and drop your document here'}
            </p>
            <p className="text-gray-400 text-sm mt-1">PDF, PNG, JPG, MP3, WAV, XLSX, PPTX</p>
          </div>

          {/* Selected File Display */}
          {file && (
            <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
              <p className="text-gray-300">
                <span className="font-semibold">File:</span> {file.name}
              </p>
              <p className="text-gray-400 text-sm">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          )}

          {/* Query Input */}
          <div>
            <label className="block text-gray-300 font-semibold mb-2">Your Question</label>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What would you like to know about this document?"
              className="w-full h-24 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none resize-none"
            />
          </div>

          {/* Prompt Version Selector */}
          <div style={{marginBottom: '16px'}}>
            <p style={{color:'#9ca3af', fontSize:'12px', marginBottom:'8px', 
                       textTransform:'uppercase', letterSpacing:'0.05em'}}>
              Prompt Version
            </p>
            <div style={{display:'flex', gap:'8px'}}>
              {[
                {v:'v1', desc:'Basic — minimal instructions'},
                {v:'v2', desc:'Structured — JSON schema'},
                {v:'v3', desc:'Advanced — ReAct + citations'}
              ].map(({v, desc}) => (
                <div
                  key={v}
                  onClick={() => setPromptVersion(v)}
                  style={{
                    flex:1, padding:'12px', borderRadius:'8px', cursor:'pointer',
                    border: promptVersion === v 
                      ? '2px solid #4f6ef7' 
                      : '2px solid #374151',
                    background: promptVersion === v 
                      ? 'rgba(79,110,247,0.1)' 
                      : '#1f2937',
                    transition: 'all 0.2s'
                  }}
                >
                  <div style={{
                    color: promptVersion === v ? '#4f6ef7' : '#fff',
                    fontWeight:'700', fontSize:'18px', marginBottom:'4px'
                  }}>
                    {v.toUpperCase()}
                  </div>
                  <div style={{color:'#6b7280', fontSize:'11px'}}>{desc}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-900/30 border border-red-700 text-red-300 p-4 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!canSubmit}
            className={`w-full py-3 rounded-lg font-semibold transition ${
              canSubmit
                ? 'bg-brand-500 text-white hover:bg-brand-500/90'
                : 'bg-gray-700 text-gray-400 cursor-not-allowed'
            }`}
          >
            {loading ? (
              <span className="inline-block animate-spin">⌛</span>
            ) : (
              'Analyze Document'
            )}
          </button>
        </form>
      </div>
    </div>
  )
}

export default UploadView
