import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function GemmaReply({ reply, toolCalls }) {
  if (!reply) return null

  // Extract content inside <reply> tags to hide Chain-of-Thought
  let displayReply = reply
  const replyMatch = reply.match(/<reply>([\s\S]*?)<\/reply>/i)
  if (replyMatch) {
    displayReply = replyMatch[1].trim()
  }

  return (
    <div className="gemma-card">
      <div className="gemma-header">
        <div className="gemma-avatar">G4</div>
        <div>
          <div className="gemma-name">MandiMind Agent</div>
          <div className="gemma-model">Gemma 4 · gemma-4-26b-a4b-it</div>
        </div>
      </div>

      {toolCalls?.length > 0 && (
        <div className="tool-chips">
          {toolCalls.map((t, i) => (
            <span key={i} className="tool-chip">⚡ {t}</span>
          ))}
        </div>
      )}

      <div className="gemma-body markdown-body">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {displayReply}
        </ReactMarkdown>
      </div>
    </div>
  )
}
