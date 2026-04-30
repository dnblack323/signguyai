import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { ScrollArea } from '../components/ui/scroll-area';
import { Badge } from '../components/ui/badge';
import { 
  Sparkles, Send, ArrowLeft, Loader2, User, Bot, 
  Lightbulb, DollarSign, Users, Briefcase, TrendingUp,
  Clock, FileText, RefreshCw, Mic, MicOff, Volume2, ShoppingCart
} from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { startRecording as startVoiceRecording } from '../lib/voiceRecorder';
import { useAICreditGuard } from '../components/credits/AICreditConfirmationDialog';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Shared readable error helper - prevents "Error: [object Object]"
function getReadableError(error) {
  if (!error) return "Something went wrong.";
  if (typeof error === "string") return error;
  if (error.message) return error.message;
  if (error.response?.data?.detail) return error.response.data.detail;
  if (error.response?.data?.message) return error.response.data.message;
  if (error.data?.detail) return error.data.detail;
  if (error.data?.message) return error.data.message;
  try {
    const str = JSON.stringify(error);
    if (str !== '{}') return str;
  } catch {
    // ignore
  }
  return "Something went wrong.";
}

const suggestedPrompts = [
  { icon: DollarSign, text: "What's a good profit margin for vehicle wraps?", category: 'pricing' },
  { icon: Users, text: "How do I handle a difficult customer complaint?", category: 'customers' },
  { icon: Briefcase, text: "What questions should I ask for a sign project?", category: 'sales' },
  { icon: TrendingUp, text: "How can I increase my average order value?", category: 'growth' },
  { icon: Clock, text: "How long should a full vehicle wrap take?", category: 'operations' },
  { icon: FileText, text: "Write a follow-up email for a quote I sent", category: 'communications' },
  { icon: ShoppingCart, text: "Make an order for a customer", category: 'orders' },
];

export default function AIAssistant() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const { runGuardedAction, dialog: creditDialog } = useAICreditGuard();
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hey there! I'm your AI Business Assistant for sign shop operations. I can help you with:

- **Pricing & Quoting** - Profit margins, competitive pricing, upselling
- **Customer Management** - Handling complaints, communication tips
- **Operations** - Production times, workflow optimization
- **Sales & Growth** - Closing deals, marketing ideas, increasing revenue
- **Create Orders** - Say "Make an order for [customer] for [product]" and I'll help you build it step by step

What can I help you with today?`
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [activeOrderDraft, setActiveOrderDraft] = useState(null);
  const [sessionId] = useState(() => `assistant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  // Voice state: 'idle' | 'listening' | 'transcribing' | 'thinking' | 'speaking' | 'error'
  const [voiceState, setVoiceState] = useState('idle');
  const [voiceTranscript, setVoiceTranscript] = useState(null); // Show transcript immediately
  const [voiceError, setVoiceError] = useState(null);
  const [voiceTimings, setVoiceTimings] = useState(null); // Debug timing logs
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const voiceAbortRef = useRef(null); // For timeout handling

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks?.().forEach((track) => track.stop());
    };
  }, []);

  const playVoice = async (text) => {
    if (!text?.trim()) return;
    
    // Prevent duplicate TTS while already speaking
    if (voiceState === 'speaking') return;
    
    await runGuardedAction({
      actionType: 'voice_tts',
      featureName: 'Business Assistant Voice Output',
      execute: async () => {
        setVoiceLoading(true);
        setVoiceState('speaking');
        const ttsStart = Date.now();
        
        try {
          const response = await axios.post(
            `${API_URL}/api/ai/voice/speak`,
            { text, voice: 'alloy', speed: 1.0 },
            {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              },
              timeout: 30000 // 30 second timeout for TTS
            }
          );
          
          const ttsTime = Date.now() - ttsStart;
          console.log(`[Voice] TTS completed in ${ttsTime}ms`);
          
          const audio = new Audio(`data:${response.data.mime_type};base64,${response.data.audio_base64}`);
          
          // Wait for audio to finish playing
          await new Promise((resolve, reject) => {
            audio.onended = resolve;
            audio.onerror = reject;
            audio.play().catch(reject);
          });
          
          return response.data;
        } catch (error) {
          console.error('Voice output error:', error);
          // TTS failure should not block - just show the text response
          toast.error('Voice playback failed, but you can read the response above.');
          // Don't re-throw - allow the flow to continue
        } finally {
          setVoiceLoading(false);
          setVoiceState('idle');
        }
      }
    });
  };

  // Holds the active recording handle returned by startVoiceRecording().
  // .stop() returns { blob, mimeType, filename }.
  const voiceHandleRef = useRef(null);

  const stopRecording = async () => {
    const handle = voiceHandleRef.current;
    if (!handle) return null;
    voiceHandleRef.current = null;
    streamRef.current = null;
    setIsRecording(false);
    try {
      const { blob, mimeType, filename } = await handle.stop();
      return { blob, mimeType, filename };
    } catch (err) {
      console.warn('stopRecording failed', err);
      return null;
    }
  };

  const handleVoiceInput = async () => {
    // Prevent duplicate requests while processing
    if (voiceState === 'transcribing' || voiceState === 'thinking' || voiceState === 'speaking') {
      return;
    }

    if (isRecording) {
      const recordingStopTime = Date.now();
      const result = await stopRecording();
      if (!result) return;
      const { blob: audioBlob, filename: audioFilename } = result;

      // Reset previous state
      setVoiceTranscript(null);
      setVoiceError(null);
      setVoiceTimings(null);

      const timings = {
        recordingDuration: 0,
        uploadStart: Date.now(),
        transcriptionTime: 0,
        aiResponseTime: 0,
        ttsTime: 0,
        totalTime: 0
      };

      await runGuardedAction({
        actionType: 'voice_transcription',
        featureName: 'Business Assistant Voice Input',
        execute: async () => {
          setVoiceLoading(true);
          setVoiceState('transcribing');
          
          try {
            // Create abort controller for timeout
            const controller = new AbortController();
            voiceAbortRef.current = controller;
            
            // 15 second timeout for transcription
            const transcriptionTimeout = setTimeout(() => {
              controller.abort();
            }, 15000);

            const formData = new FormData();
            formData.append('audio', audioBlob, audioFilename || 'assistant-input.webm');
            
            const transcribeStart = Date.now();
            const response = await axios.post(`${API_URL}/api/ai/voice/transcribe`, formData, {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'multipart/form-data'
              },
              signal: controller.signal
            });
            
            clearTimeout(transcriptionTimeout);
            timings.transcriptionTime = Date.now() - transcribeStart;
            
            if (response.data?.text) {
              const transcript = response.data.text;
              setVoiceTranscript(transcript);
              setInput(transcript);
              
              // Log timing for debugging
              console.log(`[Voice] Transcription completed in ${timings.transcriptionTime}ms`);
              
              toast.success('Voice captured! You can edit or send as-is.');
            } else {
              throw new Error('No transcription returned');
            }
            
            setVoiceState('idle');
            setVoiceTimings(timings);
            return response.data;
            
          } catch (error) {
            console.error('Voice transcription error:', error);
            
            if (error.name === 'AbortError' || error.code === 'ECONNABORTED') {
              setVoiceError('Transcription timed out. Please try a shorter recording.');
              toast.error('Transcription timed out after 15 seconds. Try a shorter recording.');
            } else {
              const errorMsg = getReadableError(error);
              setVoiceError(errorMsg);
              toast.error(errorMsg);
            }
            
            setVoiceState('error');
            throw error;
          } finally {
            setVoiceLoading(false);
            voiceAbortRef.current = null;
          }
        }
      });
      return;
    }

    // Start recording (with voice-activity-detection auto-stop).
    try {
      const handle = await startVoiceRecording({
        onSilence: () => {
          // Auto-stop fires when the user has been silent for ~1.2s. We
          // re-enter the same handler in "stop" mode so the existing
          // transcription pipeline runs unchanged.
          // NB: we don't await — fire-and-forget.
          handleVoiceInputRef.current?.();
        },
      });
      voiceHandleRef.current = handle;
      streamRef.current = handle.stream;
      setIsRecording(true);
      setVoiceState('listening');
      setVoiceTranscript(null);
      setVoiceError(null);
      toast.info('Recording... I\'ll auto-stop when you finish speaking.');
    } catch (error) {
      console.error('Microphone access error:', error);
      setVoiceState('error');
      setVoiceError('Microphone access failed');
      toast.error(getReadableError(error) || 'Microphone access failed. Please allow microphone access and try again.');
    }
  };

  // Stable ref so VAD's onSilence callback always sees the latest function.
  const handleVoiceInputRef = useRef(null);
  useEffect(() => {
    handleVoiceInputRef.current = handleVoiceInput;
  });

  const handleSend = async (messageText = input) => {
    if (!messageText.trim() || loading) return;

    const userMessage = { role: 'user', content: messageText.trim() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setVoiceTranscript(null); // Clear transcript after sending
    setLoading(true);

    try {
      await runGuardedAction({
        actionType: 'ai_business_assistant',
        featureName: 'AI Business Assistant',
        execute: async () => {
          const aiStart = Date.now();
          
          // Create abort controller for 20 second timeout
          const controller = new AbortController();
          const aiTimeout = setTimeout(() => {
            controller.abort();
          }, 20000);
          
          try {
            const response = await axios.post(
              `${API_URL}/api/ai/assistant`,
              {
                message: messageText.trim(),
                session_id: sessionId,
                conversation_history: messages.slice(-30)
              },
              {
                headers: {
                  'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json'
                },
                signal: controller.signal
              }
            );
            
            clearTimeout(aiTimeout);
            const aiTime = Date.now() - aiStart;
            console.log(`[Assistant] AI response in ${aiTime}ms`);

            const assistantMessage = { role: 'assistant', content: response.data.response };
            setMessages(prev => [...prev, assistantMessage]);
            
            // Update active order draft if returned from backend
            if (response.data.active_order_draft) {
              setActiveOrderDraft(response.data.active_order_draft);
            }
            
            return assistantMessage;
          } catch (error) {
            clearTimeout(aiTimeout);
            if (error.name === 'AbortError' || error.code === 'ECONNABORTED') {
              throw new Error('Response timed out after 20 seconds. Please try again.');
            }
            throw error;
          }
        }
      });
    } catch (error) {
      console.error('Assistant error:', error);
      toast.error(getReadableError(error));
      // Remove the user message if we failed
      setMessages(prev => prev.slice(0, -1));
      setInput(messageText);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestedPrompt = (prompt) => {
    handleSend(prompt);
  };

  const handleNewChat = async () => {
    // Clear the persistent server-side conversation so the assistant forgets
    // what was said across reloads too (not just this tab).
    try {
      await axios.delete(`${API_URL}/api/ai/assistant/history`, {
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch (err) {
      console.warn('Assistant clear failed', err);
    }
    setMessages([{
      role: 'assistant',
      content: `Hey there! I'm your AI Business Assistant for sign shop operations. I can help you with:

- **Pricing & Quoting** - Profit margins, competitive pricing, upselling
- **Customer Management** - Handling complaints, communication tips
- **Operations** - Production times, workflow optimization
- **Sales & Growth** - Closing deals, marketing ideas, increasing revenue
- **Create Orders** - Say "Make an order for [customer] for [product]" and I'll help you build it step by step

What can I help you with today?`
    }]);
    setActiveOrderDraft(null); // Clear the order draft when starting new chat
    setVoiceState('idle');
    setVoiceTranscript(null);
    setVoiceError(null);
  };

  // Hydrate persistent conversation history on mount so the assistant
  // remembers what was said across page reloads / navigation.
  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const r = await axios.get(`${API_URL}/api/ai/assistant/history`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const saved = r.data?.messages || [];
        if (!cancelled && saved.length > 0) {
          // Replace the greeting with the persisted conversation.
          setMessages(saved.map((m) => ({ role: m.role, content: m.content })));
        }
      } catch (err) {
        console.warn('Assistant history hydrate failed', err);
      }
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {creditDialog}
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => navigate('/ai-tools')}
            className="text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-purple-500" />
              AI Business Assistant
            </h1>
            <p className="text-sm text-gray-500">Your sign shop operations expert</p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleNewChat}
          className="flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      {/* Chat Area */}
      <Card className="flex-1 flex flex-col overflow-hidden">
        {/* Compact Order Draft Indicator */}
        {activeOrderDraft && activeOrderDraft.intent === 'create_order' && (
          <div className="px-4 py-2 bg-green-50 border-b border-green-200 flex items-center gap-3" data-testid="active-order-draft-indicator">
            <ShoppingCart className="h-4 w-4 text-green-600 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <span className="text-xs font-medium text-green-800">Creating Order</span>
              <span className="text-xs text-green-600 ml-2">
                {activeOrderDraft.customer_name && `Customer: ${activeOrderDraft.customer_name}`}
                {activeOrderDraft.order_items?.[0]?.product_type && ` • ${activeOrderDraft.order_items[0].product_type}`}
                {activeOrderDraft.order_items?.[0]?.quantity && ` • Qty: ${activeOrderDraft.order_items[0].quantity}`}
                {activeOrderDraft.order_items?.[0]?.size && ` • ${activeOrderDraft.order_items[0].size}`}
                {activeOrderDraft.order_items?.[0]?.material && ` • ${activeOrderDraft.order_items[0].material}`}
              </span>
            </div>
          </div>
        )}
        
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4 max-w-3xl mx-auto">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                    <Bot className="h-5 w-5 text-purple-600" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <div className="whitespace-pre-wrap text-sm leading-relaxed prose prose-sm max-w-none">
                    {message.content.split('\n').map((line, i) => {
                      // Handle bold text
                      const parts = line.split(/(\*\*.*?\*\*)/g);
                      return (
                        <p key={i} className={i > 0 ? 'mt-2' : ''}>
                          {parts.map((part, j) => {
                            if (part.startsWith('**') && part.endsWith('**')) {
                              return <strong key={j}>{part.slice(2, -2)}</strong>;
                            }
                            return part;
                          })}
                        </p>
                      );
                    })}
                  </div>
                </div>
                {message.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                    <User className="h-5 w-5 text-blue-600" />
                  </div>
                )}
              </div>
            ))}
            
            {loading && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                  <Bot className="h-5 w-5 text-purple-600" />
                </div>
                <div className="bg-gray-100 rounded-2xl px-4 py-3">
                  <Loader2 className="h-5 w-5 animate-spin text-purple-500" />
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Suggested Prompts - Show only when few messages */}
        {messages.length <= 2 && (
          <div className="px-4 py-3 border-t bg-gray-50/50">
            <div className="flex items-center gap-2 mb-2">
              <Lightbulb className="h-4 w-4 text-amber-500" />
              <span className="text-xs font-medium text-gray-500">Suggested questions</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {suggestedPrompts.map((prompt, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestedPrompt(prompt.text)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white border border-gray-200 text-xs text-gray-600 hover:bg-gray-100 hover:border-gray-300 transition-colors"
                >
                  <prompt.icon className="h-3 w-3" />
                  {prompt.text}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 border-t">
          {/* Voice State Indicator */}
          {voiceState !== 'idle' && (
            <div className="flex items-center justify-center gap-2 mb-3 text-sm" data-testid="voice-state-indicator">
              {voiceState === 'listening' && (
                <>
                  <span className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                  </span>
                  <span className="text-red-600 font-medium">Listening...</span>
                </>
              )}
              {voiceState === 'transcribing' && (
                <>
                  <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                  <span className="text-blue-600">Transcribing audio...</span>
                </>
              )}
              {voiceState === 'thinking' && (
                <>
                  <Loader2 className="h-4 w-4 animate-spin text-purple-500" />
                  <span className="text-purple-600">Thinking...</span>
                </>
              )}
              {voiceState === 'speaking' && (
                <>
                  <Volume2 className="h-4 w-4 text-green-500 animate-pulse" />
                  <span className="text-green-600">Speaking...</span>
                </>
              )}
              {voiceState === 'error' && voiceError && (
                <>
                  <span className="text-red-500">⚠️ {voiceError}</span>
                </>
              )}
            </div>
          )}
          
          {/* Show transcript immediately when available */}
          {voiceTranscript && voiceState === 'idle' && (
            <div className="flex items-center gap-2 mb-2 px-2 py-1 bg-blue-50 rounded text-sm text-blue-700">
              <Mic className="h-3 w-3" />
              <span>Heard: "{voiceTranscript}"</span>
            </div>
          )}
          
          <div className="flex gap-2 max-w-3xl mx-auto">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything about running your sign shop..."
              className="min-h-[44px] max-h-[120px] resize-none"
              rows={1}
              disabled={loading || voiceState === 'transcribing'}
            />
          <Button
            type="button"
            variant="outline"
            onClick={handleVoiceInput}
            disabled={voiceLoading || loading || voiceState === 'transcribing' || voiceState === 'speaking'}
            className={isRecording ? 'border-red-400 text-red-600 bg-red-50' : ''}
            data-testid="assistant-voice-input-button"
            title={isRecording ? 'Click to stop recording' : 'Click to start voice input'}
          >
            {voiceLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
          </Button>
            <Button
              onClick={() => handleSend()}
              disabled={!input.trim() || loading || voiceState === 'transcribing'}
              className="bg-purple-500 hover:bg-purple-600 px-4"
            >
              {loading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </div>
          <div className="flex items-center justify-center mt-3">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                const lastAssistant = [...messages].reverse().find((msg) => msg.role === 'assistant');
                if (lastAssistant) playVoice(lastAssistant.content);
              }}
              disabled={voiceLoading || !messages.some((msg) => msg.role === 'assistant')}
              data-testid="assistant-voice-output-button"
            >
              {voiceLoading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Volume2 className="h-4 w-4 mr-2" />}
              Read last reply aloud
            </Button>
          </div>
          <p className="text-xs text-gray-400 text-center mt-2">
            AI responses are suggestions only. Always verify important business decisions. Voice input and voice output are available in this assistant.
          </p>
        </div>
      </Card>
    </div>
  );
}
