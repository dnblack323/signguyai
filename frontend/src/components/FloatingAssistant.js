import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import {
  Bot, Send, X, Minimize2, Maximize2, Loader2, User,
  Sparkles, CheckCircle2, AlertCircle, Briefcase, Calendar,
  FileText, Clock, Users, DollarSign, Mic, MicOff, Volume2, Wand2
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { useAICreditGuard } from './credits/AICreditConfirmationDialog';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Quick action suggestions based on context
const quickActions = [
  { id: 'qa-create-job', icon: Briefcase, text: "Create a new job", action: "create_job" },
  { id: 'qa-create-event', icon: Calendar, text: "Schedule appointment", action: "create_calendar_event" },
  { id: 'qa-create-invoice', icon: FileText, text: "Create invoice", action: "create_invoice" },
  { id: 'qa-query-customer', icon: Users, text: "Look up customer info", action: "query" },
  { id: 'qa-query-revenue', icon: DollarSign, text: "Check revenue today", action: "query" },
  { id: 'qa-log-time', icon: Clock, text: "Log time entry", action: "log_time" },
];

let assistantMessageCounter = 0;
const createAssistantMessage = (message) => ({ id: `assistant-message-${assistantMessageCounter += 1}`, ...message });

export default function FloatingAssistant() {
  const { token, user } = useAuth();
  const { runGuardedAction, dialog: creditDialog } = useAICreditGuard();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([
    createAssistantMessage({
      role: 'assistant',
      content: `Hi${user?.full_name ? ` ${user.full_name.split(' ')[0]}` : ''}! I'm your AI assistant. I can help you:

• **Look up information** - customers, jobs, invoices, revenue
• **Create things** - jobs, appointments, invoices, time entries
• **Answer questions** - pricing, operations, best practices

What would you like to do?`,
      actions: null
    })
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);
  const [sessionId] = useState(() => `floating_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [isRecording, setIsRecording] = useState(false);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [pendingTranscript, setPendingTranscript] = useState(null);
  const [position, setPosition] = useState({ right: 24, bottom: 80 });
  const [isDragging, setIsDragging] = useState(false);
  const recordingTimeoutRef = useRef(null);
  const dragRef = useRef({ startX: 0, startY: 0, startRight: 24, startBottom: 80 });
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus();
    }
  }, [isOpen, isMinimized]);

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks?.().forEach((track) => track.stop());
      if (recordingTimeoutRef.current) clearTimeout(recordingTimeoutRef.current);
    };
  }, []);

  useEffect(() => {
    if (!isDragging) return undefined;
    const onMove = (event) => {
      const dx = event.clientX - dragRef.current.startX;
      const dy = event.clientY - dragRef.current.startY;
      setPosition({
        right: Math.max(12, dragRef.current.startRight - dx),
        bottom: Math.max(12, dragRef.current.startBottom - dy),
      });
    };
    const onUp = () => setIsDragging(false);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, [isDragging]);

  const startDrag = (event) => {
    if (event.button !== 0 || isMinimized) return;
    dragRef.current = {
      startX: event.clientX,
      startY: event.clientY,
      startRight: position.right,
      startBottom: position.bottom,
    };
    setIsDragging(true);
  };

  const stopRecording = async () => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current) { resolve(null); return; }
      if (recordingTimeoutRef.current) {
        clearTimeout(recordingTimeoutRef.current);
        recordingTimeoutRef.current = null;
      }
      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        audioChunksRef.current = [];
        streamRef.current?.getTracks?.().forEach((t) => t.stop());
        streamRef.current = null;
        mediaRecorderRef.current = null;
        setIsRecording(false);
        resolve(blob);
      };
      mediaRecorderRef.current.stop();
    });
  };

  const transcribeAudioBlob = async (audioBlob) => {
    await runGuardedAction({
      actionType: 'voice_transcription',
      featureName: 'Floating Assistant Voice Input',
      execute: async () => {
        setVoiceLoading(true);
        try {
          const formData = new FormData();
          formData.append('audio', audioBlob, 'assistant-input.webm');
          const response = await axios.post(`${API_URL}/api/ai/voice/transcribe`, formData, {
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'multipart/form-data' }
          });
          if (response.data.text) {
            setPendingTranscript(response.data.text);
            setMessages(prev => [...prev, createAssistantMessage({
              role: 'assistant',
              content: `I heard: **${response.data.text}**\n\nWould you like me to use this exactly, let you edit it first, or discard it?`,
              actions: [
                { id: 'assistant-send-transcript', label: 'Send Now', action: 'send_transcript', variant: 'default' },
                { id: 'assistant-edit-transcript', label: 'Edit First', action: 'edit_transcript', variant: 'outline' },
                { id: 'assistant-discard-transcript', label: 'Discard', action: 'discard_transcript', variant: 'outline' }
              ]
            })]);
            toast.success('Voice captured');
          }
        } finally {
          setVoiceLoading(false);
        }
      }
    });
  };

  const handleVoiceInput = async () => {
    if (isRecording) {
      const audioBlob = await stopRecording();
      if (!audioBlob) return;
      await transcribeAudioBlob(audioBlob);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
        streamRef.current = stream;
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus' : undefined;
        const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
        mediaRecorderRef.current = recorder;
        audioChunksRef.current = [];
        recorder.ondataavailable = (event) => {
          if (event.data.size > 0) audioChunksRef.current.push(event.data);
        };
        recorder.start(250);
        setIsRecording(true);
        toast.info('Recording... click mic again to stop');
        if (recordingTimeoutRef.current) clearTimeout(recordingTimeoutRef.current);
        recordingTimeoutRef.current = setTimeout(async () => {
          if (mediaRecorderRef.current) {
            const audioBlob = await stopRecording();
            if (audioBlob) await transcribeAudioBlob(audioBlob);
          }
        }, 45000);
      } catch {
        toast.error('Microphone access denied');
      }
    }
  };

  const playVoice = async (text) => {
    if (!text?.trim()) return;
    await runGuardedAction({
      actionType: 'voice_tts',
      featureName: 'Floating Assistant Voice Output',
      execute: async () => {
        setVoiceLoading(true);
        try {
          const response = await axios.post(
            `${API_URL}/api/ai/voice/speak`,
            { text, voice: 'alloy', speed: 1.0 },
            { headers: { 'Authorization': `Bearer ${token}` } }
          );
          const audio = new Audio(`data:${response.data.mime_type};base64,${response.data.audio_base64}`);
          await audio.play();
        } finally {
          setVoiceLoading(false);
        }
      }
    });
  };

  const handleSend = async (messageText = input) => {
    if (!messageText.trim() || loading) return;

    const userMessage = createAssistantMessage({ role: 'user', content: messageText.trim() });
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // First, try to detect if this is an action request
      const actionResult = await detectAndExecuteAction(messageText);
      
      if (actionResult) {
        setMessages(prev => [...prev, actionResult]);
      } else {
        // Fall back to regular assistant chat
        await runGuardedAction({
          actionType: 'assistant_chat',
          featureName: 'Floating AI Assistant',
          execute: async () => {
            const response = await axios.post(
              `${API_URL}/api/ai/assistant`,
              {
                message: messageText.trim(),
                session_id: sessionId,
                conversation_history: messages.slice(-10)
              },
              {
                headers: {
                  'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json'
                }
              }
            );

            const assistantMessage = createAssistantMessage({ role: 'assistant', content: response.data.response });
            setMessages(prev => [...prev, assistantMessage]);
            return response.data;
          }
        });
      }
    } catch (error) {
      console.error('Error:', error);
      const errorMsg = error.response?.data?.detail || 'Something went wrong. Please try again.';
      setMessages(prev => [...prev, createAssistantMessage({ role: 'assistant', content: `Sorry, ${errorMsg}`, isError: true })]);
    } finally {
      setLoading(false);
    }
  };

  const detectAndExecuteAction = async (message) => {
    const lowerMsg = message.toLowerCase();
    
    // Detect create order intent first
    if (lowerMsg.includes('create') && lowerMsg.includes('order')) {
      return await handleCreateOrderIntent(message);
    }

    // Detect create job intent
    if (lowerMsg.includes('create') && (lowerMsg.includes('job') || lowerMsg.includes('work order') || lowerMsg.includes('order'))) {
      return await handleCreateJobIntent(message);
    }
    
    // Detect create appointment/event intent
    if ((lowerMsg.includes('schedule') || lowerMsg.includes('create') || lowerMsg.includes('add')) && 
        (lowerMsg.includes('appointment') || lowerMsg.includes('meeting') || lowerMsg.includes('event'))) {
      return await handleCreateAppointmentIntent(message);
    }
    
    // Detect create invoice intent
    if (lowerMsg.includes('create') && lowerMsg.includes('invoice')) {
      return await handleCreateInvoiceIntent(message);
    }
    
    // Detect log time intent
    if ((lowerMsg.includes('log') || lowerMsg.includes('add') || lowerMsg.includes('record')) && 
        (lowerMsg.includes('time') || lowerMsg.includes('hours'))) {
      return await handleLogTimeIntent(message);
    }
    
    return null; // No action detected, use regular chat
  };

  const runParseAction = async (message, actionType) => {
    return await runGuardedAction({
      actionType: 'assistant_parse_action',
      featureName: `Assistant action parser: ${actionType}`,
      execute: async () => {
        const parseResponse = await axios.post(
          `${API_URL}/api/ai/assistant/parse-action`,
          { message, action_type: actionType },
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        return parseResponse.data;
      }
    });
  };

  const handleCreateJobIntent = async (message) => {
    try {
      // Use AI to parse the job details
      const parsed = await runParseAction(message, 'create_job');
      if (!parsed) return null;
      
      if (parsed.needs_more_info) {
        return {
          role: 'assistant',
          content: parsed.question || "I'd like to create an order for you. Could you tell me:\n• Customer name\n• Order name/description\n• Any specific details?"
        };
      }
      
      // We have enough info - ask for confirmation
      setPendingAction({
        type: 'create_job',
        params: parsed.parameters,
        description: `Create job "${parsed.parameters.name}" for ${parsed.parameters.customer_name || 'customer'}`
      });
      
      return createAssistantMessage({
        role: 'assistant',
        content: `I'll create this order for you:\n\n**Order:** ${parsed.parameters.name}\n**Customer:** ${parsed.parameters.customer_name || 'TBD'}\n**Description:** ${parsed.parameters.description || 'N/A'}\n\nShould I create this order?`,
        actions: [
          { id: 'assistant-confirm-create-job', label: 'Yes, create it', action: 'confirm', variant: 'default' },
          { id: 'assistant-cancel-create-job', label: 'No, cancel', action: 'cancel', variant: 'outline' }
        ]
      });
    } catch (err) {
      console.error('Error parsing job:', err);
      return {
        role: 'assistant',
        content: "I'd like to create a job for you. Could you tell me the job name and customer?"
      };
    }
  };

  const handleCreateOrderIntent = async (message) => {
    try {
      const parsed = await runParseAction(message, 'create_order');
      if (!parsed) return null;

      if (parsed.needs_more_info) {
        return {
          role: 'assistant',
          content: parsed.question || 'Who is this order for, and do you have a due date or any quick notes for it?'
        };
      }

      setPendingAction({
        type: 'create_order',
        params: parsed.parameters,
        description: `Create order for ${parsed.parameters.customer_name}`
      });

      return createAssistantMessage({
        role: 'assistant',
        content: `I'll create this order for you:\n\n**Customer:** ${parsed.parameters.customer_name}\n**Due Date:** ${parsed.parameters.requested_due_date || 'Not set'}\n**Notes:** ${parsed.parameters.description || 'None'}\n\nShould I create this order?`,
        actions: [
          { id: 'assistant-confirm-create-order', label: 'Yes, create it', action: 'confirm', variant: 'default' },
          { id: 'assistant-cancel-create-order', label: 'No, cancel', action: 'cancel', variant: 'outline' }
        ]
      });
    } catch (err) {
      console.error('Error parsing order:', err);
      return {
        role: 'assistant',
        content: 'I can create an order for you. Who is it for, and do you want to include a due date or short note?'
      };
    }
  };

  const handleCreateAppointmentIntent = async (message) => {
    try {
      const parsed = await runParseAction(message, 'create_calendar_event');
      if (!parsed) return null;
      
      if (parsed.needs_more_info) {
        return {
          role: 'assistant',
          content: parsed.question || "I can schedule an appointment. What details do you have?\n• Title/purpose\n• Date and time\n• Customer (optional)"
        };
      }
      
      setPendingAction({
        type: 'create_calendar_event',
        params: parsed.parameters,
        description: `Schedule "${parsed.parameters.title}" on ${parsed.parameters.date}`
      });
      
      return createAssistantMessage({
        role: 'assistant',
        content: `I'll schedule this appointment:\n\n**Title:** ${parsed.parameters.title}\n**Date:** ${parsed.parameters.date}\n**Time:** ${parsed.parameters.time || 'TBD'}\n\nShould I create this appointment?`,
        actions: [
          { id: 'assistant-confirm-create-event', label: 'Yes, schedule it', action: 'confirm', variant: 'default' },
          { id: 'assistant-cancel-create-event', label: 'No, cancel', action: 'cancel', variant: 'outline' }
        ]
      });
    } catch (err) {
      console.error('Error parsing appointment:', err);
      return {
        role: 'assistant',
        content: "I can schedule an appointment. What's it for and when would you like to schedule it?"
      };
    }
  };

  const handleCreateInvoiceIntent = async (message) => {
    return {
      role: 'assistant',
      content: "To create an invoice, I need a bit more info:\n• Which customer is this for?\n• Is it for an existing job, or a new charge?\n\nOr you can go to **Invoices → New Invoice** for the full form."
    };
  };

  const handleLogTimeIntent = async (message) => {
    try {
      const parsed = await runParseAction(message, 'log_time_entry');
      if (!parsed) return null;
      
      if (parsed.needs_more_info) {
        return {
          role: 'assistant',
          content: parsed.question || "I can log time for you. Tell me:\n• Which job?\n• How many hours?\n• What task?"
        };
      }
      
      setPendingAction({
        type: 'log_time_entry',
        params: parsed.parameters,
        description: `Log ${parsed.parameters.hours} hours for ${parsed.parameters.job_name || 'job'}`
      });
      
      return createAssistantMessage({
        role: 'assistant',
        content: `I'll log this time entry:\n\n**Hours:** ${parsed.parameters.hours}\n**Order:** ${parsed.parameters.job_name || 'TBD'}\n**Task:** ${parsed.parameters.task || 'General work'}\n\nShould I log this?`,
        actions: [
          { id: 'assistant-confirm-log-time', label: 'Yes, log it', action: 'confirm', variant: 'default' },
          { id: 'assistant-cancel-log-time', label: 'No, cancel', action: 'cancel', variant: 'outline' }
        ]
      });
    } catch (err) {
      console.error('Error parsing time entry:', err);
      return {
        role: 'assistant',
        content: "I can log time for you. Which job is it for and how many hours?"
      };
    }
  };

  const handleActionButton = async (action) => {
    if (action === 'send_transcript' && pendingTranscript) {
      const transcript = pendingTranscript;
      setPendingTranscript(null);
      handleSend(transcript);
      return;
    }
    if (action === 'edit_transcript' && pendingTranscript) {
      setInput(pendingTranscript);
      setPendingTranscript(null);
      return;
    }
    if (action === 'discard_transcript') {
      setPendingTranscript(null);
      return;
    }

    if (action === 'confirm' && pendingAction) {
      setLoading(true);
      try {
        const response = await axios.post(
          `${API_URL}/api/ai/assistant/action`,
          {
            action_type: pendingAction.type,
            parameters: pendingAction.params,
            confirmed: true
          },
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        
        const result = response.data;
        
        if (result.status === 'executed') {
          setMessages(prev => [...prev, createAssistantMessage({
            role: 'assistant',
            content: `Done! ${pendingAction.description}.\n\n${result.result?.message || 'Action completed successfully.'}`,
            isSuccess: true
          })]);
          toast.success('Action completed');
        } else {
          throw new Error(result.error || 'Action failed');
        }
      } catch (err) {
        console.error('Action error:', err);
        setMessages(prev => [...prev, createAssistantMessage({
          role: 'assistant',
          content: `Sorry, I couldn't complete that action. ${err.response?.data?.detail || err.message}`,
          isError: true
        })]);
        toast.error('Action failed');
      } finally {
        setPendingAction(null);
        setLoading(false);
      }
    } else if (action === 'cancel') {
      setPendingAction(null);
      setMessages(prev => [...prev, createAssistantMessage({
        role: 'assistant',
        content: "No problem, I've cancelled that. What else can I help with?"
      })]);
    }
  };

  const handleQuickAction = (quickAction) => {
    if (quickAction.action === 'create_job') {
      handleSend("I want to create a new job");
    } else if (quickAction.action === 'create_calendar_event') {
      handleSend("Schedule a new appointment");
    } else if (quickAction.action === 'create_invoice') {
      handleSend("Create a new invoice");
    } else if (quickAction.action === 'log_time') {
      handleSend("Log time for a job");
    } else {
      handleSend(quickAction.text);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed z-50 w-14 h-14 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full shadow-lg hover:shadow-xl transition-all hover:scale-105 flex items-center justify-center group"
        style={{ right: position.right, bottom: position.bottom }}
        data-testid="floating-assistant-trigger"
      >
        <Bot className="h-7 w-7 text-white" />
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white"></span>
      </button>
    );
  }

  return (
    <>
    {creditDialog}
    <div
      className={`fixed z-50 bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col transition-all duration-200 ${
        isMinimized 
          ? 'w-80 h-14' 
          : 'w-96 h-[32rem]'
      }`}
      style={{ right: position.right, bottom: position.bottom }}
      data-testid="floating-assistant-panel"
    >
      {/* Header */}
      <div 
        className={`flex items-center justify-between px-4 py-3 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-t-2xl cursor-pointer ${isDragging ? 'select-none' : ''}`}
        onClick={() => isMinimized && setIsMinimized(false)}
        onMouseDown={startDrag}
        onContextMenu={(event) => {
          event.preventDefault();
          setIsOpen(false);
        }}
      >
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <p className="font-medium text-sm">AI Assistant</p>
            {!isMinimized && <p className="text-xs text-purple-100">I can look up & create things</p>}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={(e) => { e.stopPropagation(); setIsMinimized(!isMinimized); }}
            className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
          >
            {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); setIsOpen(false); }}
            className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Messages Area */}
          <ScrollArea className="flex-1 p-3">
            <div className="space-y-3">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-2 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {message.role === 'assistant' && (
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
                      message.isError ? 'bg-red-100' : message.isSuccess ? 'bg-green-100' : 'bg-purple-100'
                    }`}>
                      {message.isError ? (
                        <AlertCircle className="h-4 w-4 text-red-600" />
                      ) : message.isSuccess ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                      ) : (
                        <Bot className="h-4 w-4 text-purple-600" />
                      )}
                    </div>
                  )}
                  <div className="flex flex-col gap-2 max-w-[80%]">
                    <div
                      className={`rounded-xl px-3 py-2 text-sm ${
                        message.role === 'user'
                          ? 'bg-purple-500 text-white'
                          : message.isError
                          ? 'bg-red-50 text-red-800 border border-red-200'
                          : message.isSuccess
                          ? 'bg-green-50 text-green-800 border border-green-200'
                          : 'bg-slate-100 text-slate-800'
                      }`}
                    >
                      <div className="whitespace-pre-wrap leading-relaxed">
                        {message.content.split('\n').map((line, i) => {
                          const parts = line.split(/(\*\*.*?\*\*)/g);
                          return (
                            <p key={`${message.id}-line-${i}-${line}`} className={i > 0 ? 'mt-1.5' : ''}>
                              {parts.map((part, j) => {
                                if (part.startsWith('**') && part.endsWith('**')) {
                                  return <strong key={`${message.id}-bold-${i}-${j}-${part}`}>{part.slice(2, -2)}</strong>;
                                }
                                return <React.Fragment key={`${message.id}-text-${i}-${j}-${part}`}>{part}</React.Fragment>;
                              })}
                            </p>
                          );
                        })}
                      </div>
                    </div>
                    {/* Action buttons */}
                    {message.actions && (
                      <div className="flex gap-2">
                        {message.actions.map((action) => (
                          <Button
                            key={action.id || action.action || action.label}
                            size="sm"
                            variant={action.variant || 'default'}
                            onClick={() => handleActionButton(action.action)}
                            className={action.variant === 'default' ? 'bg-purple-500 hover:bg-purple-600' : ''}
                            disabled={loading}
                          >
                            {action.label}
                          </Button>
                        ))}
                      </div>
                    )}
                  </div>
                  {message.role === 'user' && (
                    <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center flex-shrink-0">
                      <User className="h-4 w-4 text-slate-600" />
                    </div>
                  )}
                </div>
              ))}
              
              {loading && (
                <div className="flex gap-2 justify-start">
                  <div className="w-7 h-7 rounded-full bg-purple-100 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-purple-600" />
                  </div>
                  <div className="bg-slate-100 rounded-xl px-3 py-2">
                    <Loader2 className="h-4 w-4 animate-spin text-purple-500" />
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Quick Actions - Show when few messages */}
          {messages.length <= 2 && (
            <div className="px-3 py-2 border-t bg-slate-50/80">
              <p className="text-xs text-slate-500 mb-2">Quick actions:</p>
              <div className="flex flex-wrap gap-1.5">
                {quickActions.slice(0, 4).map((qa) => (
                  <button
                    key={qa.id}
                    onClick={() => handleQuickAction(qa)}
                    className="flex items-center gap-1 px-2 py-1 rounded-full bg-white border text-xs text-slate-600 hover:bg-slate-100 hover:border-slate-300 transition-colors"
                  >
                    <qa.icon className="h-3 w-3" />
                    {qa.text}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="p-3 border-t">
            <div className="flex gap-1.5 items-end">
              <Textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask or tell me what to do..."
                className="min-h-[40px] max-h-[80px] resize-none text-sm"
                rows={1}
                disabled={loading}
              />
              <Button
                onClick={handleVoiceInput}
                disabled={voiceLoading || loading}
                variant="outline"
                size="sm"
                className={`px-2.5 flex-shrink-0 ${isRecording ? 'border-red-400 text-red-600 bg-red-50' : ''}`}
                data-testid="floating-assistant-mic-btn"
              >
                {voiceLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </Button>
              <Button
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className="bg-purple-500 hover:bg-purple-600 px-2.5 flex-shrink-0"
                size="sm"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
            {messages.length > 1 && (
              <div className="flex justify-center mt-1.5">
                <button
                  onClick={() => {
                    const lastAssistant = [...messages].reverse().find((m) => m.role === 'assistant');
                    if (lastAssistant) playVoice(lastAssistant.content);
                  }}
                  disabled={voiceLoading || !messages.some((m) => m.role === 'assistant')}
                  className="flex items-center gap-1 text-xs text-slate-500 hover:text-purple-600 disabled:opacity-40 transition-colors"
                  data-testid="floating-assistant-speak-btn"
                >
                  {voiceLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Volume2 className="h-3 w-3" />}
                  Read aloud
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
    </>
  );
}
