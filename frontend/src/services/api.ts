
import type {
  ChatRequest,
  ChatResponse,
  Conversation,
  DocumentItem,
  DocumentUploadResponse,
  Message,
  StreamEvent,
} from '../types'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options)

  if (!response.ok) {
    let message = `Request failed (${response.status})`

    try {
      const error = (await response.json()) as { detail?: string }
      message = error.detail ?? message
    } catch {
      // Keep the default message if the response isn't JSON.
    }

    throw new Error(message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export async function getDocuments(): Promise<DocumentItem[]> {
  return request<DocumentItem[]>('/documents/')
}

export function uploadDocument(
  file: File,
  onProgress?: (percentage: number) => void,
): Promise<DocumentUploadResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const formData = new FormData()

    formData.append('file', file)

    xhr.open('POST', `${API_BASE_URL}/documents/upload`)

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && event.total > 0) {
        const percentage = Math.round(
          (event.loaded / event.total) * 100,
        )
        onProgress?.(percentage)
      }
    }

    xhr.onload = () => {
      let response: unknown

      try {
        response = JSON.parse(xhr.responseText)
      } catch {
        response = null
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(response as DocumentUploadResponse)
        return
      }

      const detail =
        typeof response === 'object' &&
        response !== null &&
        'detail' in response &&
        typeof response.detail === 'string'
          ? response.detail
          : `Upload failed (${xhr.status})`

      reject(new Error(detail))
    }

    xhr.onerror = () => {
      reject(new Error('Network error while uploading the document.'))
    }

    xhr.onabort = () => {
      reject(new Error('Document upload was cancelled.'))
    }

    xhr.send(formData)
  })
}

export async function deleteDocument(
  documentId: number,
): Promise<void> {
  return request<void>(`/documents/${documentId}`, {
    method: 'DELETE',
  })
}

export async function getConversations(): Promise<Conversation[]> {
  return request<Conversation[]>('/conversations/')
}

export async function createConversation(
  title = 'New Conversation',
): Promise<Conversation> {
  return request<Conversation>('/conversations/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title }),
  })
}

export async function getMessages(
  conversationId: number,
): Promise<Message[]> {
  return request<Message[]>(
    `/conversations/${conversationId}/messages`,
  )
}

export async function sendChatMessage(
  conversationId: number,
  payload: ChatRequest,
): Promise<ChatResponse> {
  return request<ChatResponse>(
    `/conversations/${conversationId}/chat`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )
}

export async function streamChatMessage(
  conversationId: number,
  payload: ChatRequest,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/conversations/${conversationId}/chat/stream`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify(payload),
    },
  )

  if (!response.ok) {
    let message = `Chat request failed (${response.status})`

    try {
      const error = (await response.json()) as { detail?: string }
      message = error.detail ?? message
    } catch {
      // Keep the default message if the response isn't JSON.
    }

    throw new Error(message)
  }

  if (!response.body) {
    throw new Error('The server did not provide a streaming response.')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  function processEvent(block: string) {
    const data = block
      .split(/\r?\n/)
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trimStart())
      .join('\n')

    if (!data) return

    let event: StreamEvent

    try {
      event = JSON.parse(data) as StreamEvent
    } catch {
      throw new Error('Received an invalid streaming event from the server.')
    }

    onEvent(event)

    if (event.type === 'error') {
      throw new Error(
        event.message ?? 'The AI could not generate an answer.',
      )
    }
  }

  try {
    while (true) {
      const { value, done } = await reader.read()

      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const blocks = buffer.split(/\r?\n\r?\n/)
      buffer = blocks.pop() ?? ''

      for (const block of blocks) {
        processEvent(block)
      }
    }

    buffer += decoder.decode()

    if (buffer.trim()) {
      processEvent(buffer)
    }
  } finally {
    reader.releaseLock()
  }
}
