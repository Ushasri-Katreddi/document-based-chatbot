
import { useEffect, useState, type ChangeEvent, type FormEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import './App.css'

import {
  createConversation,
  getConversations,
  getDocuments,
  getMessages,
  streamChatMessage,
  uploadDocument,
} from './services/api'

import type {
  Citation,
  Conversation,
  DocumentItem,
  Message,
} from './types'

const suggestions = [
  {
    icon: '⌕',
    title: 'Summarize a document',
    description: 'Get the key points in seconds.',
    prompt: 'Summarize the selected document.',
  },
  {
    icon: '✧',
    title: 'Find key skills',
    description: 'Extract skills and experience.',
    prompt: 'What are the key skills and experience?',
  },
  {
    icon: '≋',
    title: 'Compare information',
    description: 'Explore details across documents.',
    prompt: 'Compare the key information in my documents.',
  },
]

function AnswerContent({ content }: { content: string }) {
  return (
    <div className="answer-content">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  )
}

function App() {
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<number | null>(
    null,
  )
  const [selectedDocument, setSelectedDocument] = useState<number | 'all'>(
    'all',
  )
  const [messages, setMessages] = useState<Message[]>([])
  const [question, setQuestion] = useState('')

  const [initialLoading, setInitialLoading] = useState(true)
  const [documentsLoading, setDocumentsLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadFilename, setUploadFilename] = useState('')
  const [uploadStage, setUploadStage] = useState<
    'uploading' | 'processing' | null
  >(null)
  const [uploadFileIndex, setUploadFileIndex] = useState(0)
  const [uploadFileCount, setUploadFileCount] = useState(0)

  const [creatingConversation, setCreatingConversation] = useState(false)
  const [sending, setSending] = useState(false)

  const [documentError, setDocumentError] = useState<string | null>(null)
  const [chatError, setChatError] = useState<string | null>(null)

  async function refreshDocuments() {
    try {
      const result = await getDocuments()
      setDocuments(result)

      setSelectedDocument((current) => {
        if (
          current !== 'all' &&
          !result.some((document) => document.id === current)
        ) {
          return 'all'
        }

        return current
      })

      return true
    } catch (error) {
      setDocumentError(
        error instanceof Error ? error.message : 'Unable to load documents.',
      )
      return false
    } finally {
      setDocumentsLoading(false)
    }
  }

  async function loadInitialData() {
    try {
      const [documentResult, conversationResult] = await Promise.all([
        getDocuments(),
        getConversations(),
      ])

      setDocuments(documentResult)
      setConversations(conversationResult)

      if (conversationResult.length > 0) {
        const firstConversation = conversationResult[0]

        setActiveConversationId(firstConversation.id)

        const history = await getMessages(firstConversation.id)
        setMessages(history)
      }
    } catch (error) {
      setDocumentError(
        error instanceof Error
          ? error.message
          : 'Unable to load application data.',
      )
    } finally {
      setDocumentsLoading(false)
      setInitialLoading(false)
    }
  }

  useEffect(() => {
    void loadInitialData()
  }, [])

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? [])
    event.target.value = ''

    if (files.length === 0 || uploading) return

    const allowedExtensions = ['.pdf', '.txt', '.md']

    const invalidFiles = files.filter(
      (file) =>
        !allowedExtensions.some((extension) =>
          file.name.toLowerCase().endsWith(extension),
        ),
    )

    if (invalidFiles.length > 0) {
      setDocumentError(
        `Unsupported file type: ${invalidFiles
          .map((file) => file.name)
          .join(', ')}. Use PDF, TXT, or Markdown files.`,
      )
      return
    }

    const oversizedFiles = files.filter(
      (file) => file.size > 10 * 1024 * 1024,
    )

    if (oversizedFiles.length > 0) {
      setDocumentError(
        `Files must not exceed 10 MB: ${oversizedFiles
          .map((file) => file.name)
          .join(', ')}`,
      )
      return
    }

    setUploading(true)
    setDocumentError(null)
    setUploadFileCount(files.length)

    try {
      for (let index = 0; index < files.length; index++) {
        const file = files[index]

        setUploadFileIndex(index + 1)
        setUploadFilename(file.name)
        setUploadProgress(0)
        setUploadStage('uploading')

        await uploadDocument(file, (percentage) => {
          setUploadProgress(percentage)

          if (percentage >= 100) {
            setUploadStage('processing')
          }
        })

        // The API returns after the backend's ingestion function completes.
        setUploadProgress(100)
        setUploadStage('processing')

        const refreshed = await refreshDocuments()

        if (!refreshed) {
          throw new Error(
            'The upload completed, but the document list could not be refreshed.',
          )
        }
      }
    } catch (error) {
      const uploadError =
        error instanceof Error ? error.message : 'Unable to upload documents.'

      await refreshDocuments()
      setDocumentError(uploadError)
    } finally {
      setUploading(false)
      setUploadStage(null)
      setUploadFilename('')
      setUploadProgress(0)
      setUploadFileIndex(0)
      setUploadFileCount(0)
    }
  }

  async function handleNewConversation() {
    if (creatingConversation || sending) return

    setCreatingConversation(true)
    setChatError(null)

    try {
      const conversation = await createConversation()

      setConversations((current) => [conversation, ...current])
      setActiveConversationId(conversation.id)
      setMessages([])
      setQuestion('')
    } catch (error) {
      setChatError(
        error instanceof Error
          ? error.message
          : 'Unable to create a conversation.',
      )
    } finally {
      setCreatingConversation(false)
    }
  }

  async function handleSelectConversation(conversationId: number) {
    if (sending || conversationId === activeConversationId) return

    setActiveConversationId(conversationId)
    setMessages([])
    setChatError(null)

    try {
      const history = await getMessages(conversationId)
      setMessages(history)
    } catch (error) {
      setChatError(
        error instanceof Error
          ? error.message
          : 'Unable to load conversation history.',
      )
    }
  }

  async function handleSend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmedQuestion = question.trim()

    if (!trimmedQuestion || sending || initialLoading) return

    if (selectedDocument !== 'all') {
      const selected = documents.find(
        (document) => document.id === selectedDocument,
      )

      if (!selected) {
        setChatError('The selected document is no longer available.')
        return
      }

      if (selected.status !== 'ready') {
        setChatError('The selected document is not ready for questions yet.')
        return
      }
    }

    setSending(true)
    setChatError(null)
    setQuestion('')

    let conversationId = activeConversationId

    try {
      if (conversationId === null) {
        const conversation = await createConversation(trimmedQuestion)

        conversationId = conversation.id

        setConversations((current) => [conversation, ...current])
        setActiveConversationId(conversationId)
      }

      const timestamp = new Date().toISOString()
      const temporaryId = Date.now()
      const assistantMessageId = temporaryId + 1

      const userMessage: Message = {
        id: temporaryId,
        conversation_id: conversationId,
        role: 'user',
        content: trimmedQuestion,
        citations: [],
        created_at: timestamp,
      }

      const assistantMessage: Message = {
        id: assistantMessageId,
        conversation_id: conversationId,
        role: 'assistant',
        content: '',
        citations: [],
        created_at: timestamp,
      }

      setMessages((current) => [...current, userMessage, assistantMessage])

      await streamChatMessage(
        conversationId,
        {
          question: trimmedQuestion,
          document_id:
            selectedDocument === 'all' ? null : selectedDocument,
        },
        (streamEvent) => {
          if (streamEvent.type === 'token' && streamEvent.content) {
            const token = streamEvent.content

            setMessages((current) =>
              current.map((message) =>
                message.id === assistantMessageId
                  ? { ...message, content: message.content + token }
                  : message,
              ),
            )
          }
        },
      )

      const history = await getMessages(conversationId)
      setMessages(history)

      const updatedConversations = await getConversations()
      setConversations(updatedConversations)
    } catch (error) {
      setChatError(
        error instanceof Error
          ? error.message
          : 'Unable to generate an answer.',
      )
    } finally {
      setSending(false)
    }
  }

  function getMessageCitations(message: Message): Citation[] {
    return message.citations ?? []
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">D</div>

          <div>
            <h1>DocuMind</h1>
            <p>DOCUMENT INTELLIGENCE</p>
          </div>
        </div>

        <button
          className="new-chat-button"
          onClick={handleNewConversation}
          type="button"
          disabled={creatingConversation || sending}
        >
          <span aria-hidden="true">＋</span>
          {creatingConversation ? 'Creating...' : 'New conversation'}
        </button>

        <section className="sidebar-section">
          <div className="section-heading">
            <span>Your documents</span>
            <span className="count-badge">{documents.length}</span>
          </div>

          <label className="upload-button" aria-disabled={uploading}>
            <span aria-hidden="true">↑</span>
            {uploading ? 'Uploading documents...' : 'Upload documents'}

            <input
              type="file"
              accept=".pdf,.txt,.md"
              multiple
              onChange={handleUpload}
              disabled={uploading}
              hidden
            />
          </label>

          {uploading && (
            <div
              className="upload-progress-panel"
              role="status"
              aria-live="polite"
            >
              <div className="upload-progress-heading">
                <span
                  className="upload-progress-filename"
                  title={uploadFilename}
                >
                  {uploadFilename}
                </span>

                <span className="upload-progress-percent">
                  {uploadStage === 'processing'
                    ? 'Processing'
                    : `${uploadProgress}%`}
                </span>
              </div>

              <div
                className="upload-progress-track"
                role="progressbar"
                aria-label={`Uploading ${uploadFilename}`}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={
                  uploadStage === 'processing' ? 100 : uploadProgress
                }
              >
                <div
                  className={`upload-progress-fill ${
                    uploadStage === 'processing' ? 'processing' : ''
                  }`}
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>

              <p className="upload-progress-caption">
                {uploadStage === 'processing'
                  ? 'File received. Extracting text and indexing your document...'
                  : 'Uploading your document...'}
              </p>

              {uploadFileCount > 1 && (
                <p className="upload-progress-caption">
                  File {uploadFileIndex} of {uploadFileCount}
                </p>
              )}
            </div>
          )}

          {documentsLoading && (
            <p className="document-message">Loading documents...</p>
          )}

          {documentError && (
            <p className="document-error" role="alert">
              {documentError}
            </p>
          )}

          <button
            type="button"
            className={`document-row ${
              selectedDocument === 'all' ? 'selected' : ''
            }`}
            onClick={() => setSelectedDocument('all')}
          >
            <span className="document-icon all-icon" aria-hidden="true">
              ▤
            </span>

            <span className="document-details">
              <strong>All documents</strong>
              <small>Search across your library</small>
            </span>
          </button>

          {!documentsLoading &&
            documents.length === 0 &&
            !documentError && (
              <p className="document-message">
                No documents yet. Upload a PDF, TXT, or Markdown file to begin.
              </p>
            )}

          {documents.map((document) => (
            <button
              type="button"
              className={`document-row ${
                selectedDocument === document.id ? 'selected' : ''
              }`}
              key={document.id}
              onClick={() => setSelectedDocument(document.id)}
              title={document.filename}
            >
              <span className="document-icon" aria-hidden="true">
                {document.file_type.toUpperCase()}
              </span>

              <span className="document-details">
                <strong>{document.filename}</strong>
                <small>
                  {document.file_type.toUpperCase()} · {document.status}
                </small>
              </span>
            </button>
          ))}
        </section>

        <section className="sidebar-section conversation-section">
          <div className="section-heading">
            <span>Recent conversations</span>
            <span className="count-badge">{conversations.length}</span>
          </div>

          {conversations.map((conversation) => (
            <button
              type="button"
              className={`document-row ${
                activeConversationId === conversation.id ? 'selected' : ''
              }`}
              key={conversation.id}
              onClick={() => void handleSelectConversation(conversation.id)}
              disabled={sending}
              title={conversation.title}
            >
              <span className="document-icon all-icon" aria-hidden="true">
                ◷
              </span>

              <span className="document-details">
                <strong>{conversation.title}</strong>
                <small>
                  {new Date(conversation.updated_at).toLocaleDateString()}
                </small>
              </span>
            </button>
          ))}

          {conversations.length === 0 && !initialLoading && (
            <p className="document-message">No conversations yet.</p>
          )}
        </section>

        <div className="sidebar-footer">
          <span className="status-dot" />
          <span>Local AI workspace</span>
          <span className="free-label">FREE</span>
        </div>
      </aside>

      <section className="main-panel">
        <header className="topbar">
          <div>
            <p className="eyebrow">YOUR PERSONAL KNOWLEDGE BASE</p>
            <h2>Document assistant</h2>
          </div>

          <div className="backend-status">
            <span className="status-dot" />
            {initialLoading
              ? 'Loading workspace...'
              : sending
                ? 'Generating answer...'
                : documentError || chatError
                  ? 'Check notifications'
                  : 'Workspace ready'}
          </div>
        </header>

        <div className="chat-area">
          {initialLoading ? (
            <div className="welcome">
              <div className="welcome-icon" aria-hidden="true">
                ✳
              </div>

              <h2>Loading your workspace...</h2>

              <p className="welcome-description">
                Retrieving your documents and conversations.
              </p>
            </div>
          ) : messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-icon" aria-hidden="true">
                ✳
              </div>

              <p className="eyebrow">YOUR DOCUMENTS, UNDERSTOOD</p>

              <h2>
                What would you like
                <br />
                to discover today?
              </h2>

              <p className="welcome-description">
                Ask questions about your documents and find the information
                that matters, with answers grounded in your sources.
              </p>

              <div className="suggestion-grid">
                {suggestions.map((suggestion) => (
                  <button
                    type="button"
                    className="suggestion-card"
                    key={suggestion.title}
                    onClick={() => setQuestion(suggestion.prompt)}
                  >
                    <span className="suggestion-icon" aria-hidden="true">
                      {suggestion.icon}
                    </span>

                    <strong>{suggestion.title}</strong>
                    <small>{suggestion.description}</small>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="message-list">
              {messages.map((message) => (
                <article
                  className={`message ${message.role}`}
                  key={message.id}
                >
                  <div className="message-avatar" aria-hidden="true">
                    {message.role === 'user' ? 'U' : 'D'}
                  </div>

                  <div className="message-body">
                    <strong>
                      {message.role === 'user' ? 'You' : 'DocuMind'}
                    </strong>

                    {message.role === 'assistant' ? (
                      message.content ? (
                        <AnswerContent content={message.content} />
                      ) : sending ? (
                        <p className="thinking-indicator">Thinking...</p>
                      ) : null
                    ) : (
                      <p className="user-message-content">
                        {message.content}
                      </p>
                    )}

                    {getMessageCitations(message).length > 0 && (
                      <div className="source-list">
                        {getMessageCitations(message).map((citation) => (
                          <span
                            className="source-chip"
                            key={`${citation.document_id}-${citation.chunk_index}`}
                          >
                            ▤ {citation.source} · Chunk {citation.chunk_index}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </article>
              ))}

              {sending && (
                <p className="demo-notice">
                  DocuMind is generating your answer...
                </p>
              )}
            </div>
          )}

          {chatError && (
            <p className="document-error" role="alert">
              {chatError}
            </p>
          )}
        </div>

        <footer className="composer-wrapper">
          <form className="composer" onSubmit={handleSend}>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  event.currentTarget.form?.requestSubmit()
                }
              }}
              placeholder={
                selectedDocument === 'all'
                  ? 'Ask anything about your documents...'
                  : 'Ask about the selected document...'
              }
              aria-label="Your question"
              rows={2}
              disabled={sending || initialLoading}
            />

            <div className="composer-bottom">
              <span className="composer-hint">
                <span aria-hidden="true">✧</span>

                {selectedDocument === 'all'
                  ? 'Answers grounded in your documents'
                  : `Selected document ID: ${selectedDocument}`}
              </span>

              <button
                type="submit"
                className="send-button"
                disabled={!question.trim() || sending || initialLoading}
                aria-label="Send message"
              >
                {sending ? '…' : '↑'}
              </button>
            </div>
          </form>

          <p className="disclaimer">
            AI can make mistakes. Verify important information against your
            sources.
          </p>
        </footer>
      </section>
    </main>
  )
}

export default App
