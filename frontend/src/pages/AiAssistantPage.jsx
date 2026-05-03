import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'

const AiAssistantPage = () => {
  const navigate = useNavigate()
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '您好！我是EnerGAI智能助手。基于化工余热回收系统的专业知识，我可以为您提供：\n\n- **设备诊断**：分析换热器、泵、阀门等设备运行状态\n- **故障排查**：定位问题原因并提供处置建议\n- **优化建议**：帮您提升能源利用效率\n\n请问有什么可以帮助您的？',
      sources: ['化工过程安全手册', '热泵工业节能应用指南']
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef(null)
  const chatContainerRef = useRef(null)

  const diagnosticReport = {
    title: '换热器2效率下降分析',
    problem: '换热器2的换热效率在最近30天内下降了12%，导致余热回收率降低，影响整体系统节能效果。',
    causes: [
      '换热管束结垢严重，热阻增加',
      '循环水温度偏高，进出口温差减小',
      '换热管束存在部分堵塞情况'
    ],
    suggestions: [
      '建议本周内进行化学清洗，清除管束水垢',
      '检查循环水冷却系统，确保进水温度在合理范围',
      '对换热器进行压差监测，必要时进行机械清洗'
    ],
    knowledgeSources: [
      '《化工过程安全》赵劲松',
      '《热泵工业节能应用》黄志坚'
    ]
  }

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = () => {
    if (!inputValue.trim()) return

    const userMessage = { role: 'user', content: inputValue }
    setMessages(prev => [...prev, userMessage])
    setInputValue('')

    setTimeout(() => {
      const aiResponse = {
        role: 'assistant',
        content: `根据您的问题 "${inputValue}"，我已经分析了相关的运行数据。\n\n**分析结果**：\n当前工况下，换热器运行在最优区间，但建议关注以下几点：\n\n1. 监控入口温度变化\n2. 定期清理过滤网\n3. 调整循环流量至设定值\n\n来源标注：基于知识库中《化工故障案例集》和实时传感器数据综合分析得出。`,
        sources: ['化工故障案例集_v1', '实时传感器数据']
      }
      setMessages(prev => [...prev, aiResponse])
    }, 1000)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="ai-assistant-page">
      <div className="ambient-bg" aria-hidden="true">
        <div className="ambient-bg__base"></div>
        <div className="ambient-bg__aurora"></div>
        <div className="ambient-bg__aurora ambient-bg__aurora--slow"></div>
        <div className="ambient-bg__mesh"></div>
        <div className="ambient-bg__hex"></div>
        <div className="ambient-bg__flow"></div>
        <div className="ambient-bg__flow ambient-bg__flow--vert"></div>
        <div className="ambient-bg__sweep"></div>
        <div className="ambient-bg__rings"><span></span><span></span><span></span></div>
        <div className="ambient-bg__glow ambient-bg__glow--a"></div>
        <div className="ambient-bg__glow ambient-bg__glow--b"></div>
        <div className="ambient-bg__glow ambient-bg__glow--c"></div>
        <div className="ambient-bg__glow ambient-bg__glow--d"></div>
        <div className="ambient-bg__sparkles"></div>
        <div className="ambient-bg__vignette"></div>
      </div>

      <div className="ai-header">
        <button className="back-btn" onClick={() => navigate('/')}>
          <span>←</span> 返回驾驶舱
        </button>
      </div>

      <div className="ai-content">
        <div className="ai-left-panel">
          <div className="diagnostic-card">
            <h2>📊 诊断报告</h2>
            <div className="diagnostic-section">
              <h3>问题描述</h3>
              <p>{diagnosticReport.problem}</p>
            </div>
            <div className="diagnostic-section">
              <h3>原因分析</h3>
              <ul>
                {diagnosticReport.causes.map((cause, index) => (
                  <li key={index}>{cause}</li>
                ))}
              </ul>
            </div>
            <div className="diagnostic-section">
              <h3>处置建议</h3>
              <ul>
                {diagnosticReport.suggestions.map((suggestion, index) => (
                  <li key={index}>{suggestion}</li>
                ))}
              </ul>
            </div>
            <div className="diagnostic-section">
              <h3>知识来源</h3>
              <div className="source-tags">
                {diagnosticReport.knowledgeSources.map((source, index) => (
                  <span key={index} className="source-tag">{source}</span>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="ai-right-panel">
          <div className="chat-container">
            <div className="chat-header">
              <h2>🤖 EnerGAI 智能助手</h2>
            </div>
            <div className="chat-messages" ref={chatContainerRef}>
              {messages.map((message, index) => (
                <div key={index} className={`message ${message.role}`}>
                  {message.role === 'assistant' && (
                    <div className="message-avatar">🤖</div>
                  )}
                  <div className="message-content">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                    {message.sources && (
                      <div className="message-sources">
                        <span className="sources-label">📚 来源：</span>
                        {message.sources.map((source, idx) => (
                          <span key={idx} className="source-chip">{source}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
            <div className="chat-input-area">
              <input
                type="text"
                className="chat-input"
                placeholder="请输入您的问题..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
              />
              <button className="send-btn" onClick={handleSend}>
                发送
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AiAssistantPage