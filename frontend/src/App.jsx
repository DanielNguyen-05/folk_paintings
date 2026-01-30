import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import { api } from './api';
import './App.css';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const updateLastAssistant = (updater) => {
    setCurrentConversation(prev => {
      if (!prev) return prev;

      const messages = [...prev.messages];
      const lastIndex = messages.length - 1;
      const last = messages[lastIndex];

      if (!last || last.role !== "assistant") return prev;

      messages[lastIndex] = updater({ ...last });
      return { ...prev, messages };
    });
  };

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Load conversation details when selected
  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
        ...conversations,
      ]);
      setCurrentConversationId(newConv.id);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
  };

  const handleSendMessage = async ({ content, image = null }) => {
    if (!currentConversationId) return;

    setIsLoading(true);
    try {
      // Optimistically add user message to UI
      const userMessage = { role: 'user', content, image: image ? URL.createObjectURL(image.file) : null };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
      }));

      // Create a partial assistant message that will be updated progressively
      const assistantMessage = {
        role: 'assistant',
        stage1: null,
        stage2: null,
        stage3: null,
        metadata: null,
        loading: {
          stage1: false,
          stage2: false,
          stage3: false,
        },
      };

      // Add the partial assistant message
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      // Send message with streaming
      await api.sendMessageStream(
        currentConversationId,
        { content, image },
        (type, payload) => {
          switch (type) {
            case "stage1_start":
              updateLastAssistant(msg => ({
                ...msg,
                loading: { ...msg.loading, stage1: true }
              }));
              break;

            case "stage1_complete":
              updateLastAssistant(msg => ({
                ...msg,
                stage1: payload,
                loading: { ...msg.loading, stage1: false }
              }));
              break;

            case "stage2_start":
              updateLastAssistant(msg => ({
                ...msg,
                loading: { ...msg.loading, stage2: true }
              }));
              break;

            case "stage2_complete":
              updateLastAssistant(msg => ({
                ...msg,
                stage2: payload,
                loading: { ...msg.loading, stage2: false }
              }));
              break;

            case "stage3_start":
              updateLastAssistant(msg => ({
                ...msg,
                loading: { ...msg.loading, stage3: true }
              }));
              break;

            case "stage3_complete":
              updateLastAssistant(msg => ({
                ...msg,
                stage3: payload,
                loading: { ...msg.loading, stage3: false }
              }));
              break;

            case "title_complete":
              loadConversations();
              break;

            case "complete":
              setIsLoading(false);
              loadConversations();
              break;

            case "error":
              console.error("Stream error:", payload);
              setIsLoading(false);
              break;
          }
        }
      );
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove optimistic messages on error
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
      />
      <ChatInterface
        conversation={currentConversation}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />
    </div>
  );
}

export default App;
