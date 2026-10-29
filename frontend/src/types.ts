
export interface DocumentItem {
  id: number
  filename: string
  file_type: string
  status: string
  uploaded_at: string
}

export interface Conversation {
  id: number
  title: string
  user_id: string
  created_at: string
  updated_at: string
}

export interface Citation {
  document_id: number
  source: string
  chunk_index: number
}

export interface Message {
  id: number
  conversation_id: number
  role: string
  content: string
  citations: Citation[]
  created_at: string
}

export interface ChatRequest {
  question: string
  document_id?: number | null
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
}

export interface DocumentUploadResponse {
  id: number
  filename: string
  status: string
  chunks_created: number
}

export interface StreamEvent {
  type: 'token' | 'done' | 'error'
  content?: string
  message?: string
}
