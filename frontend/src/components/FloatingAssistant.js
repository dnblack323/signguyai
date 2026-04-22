import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { ScrollArea } from './ui/scroll-area';
import {
  Bot, Send, X, Minimize2, Maximize2, Loader2, User,
  Sparkles, CheckCircle2, AlertCircle, Briefcase, Calendar,
  FileText, Clock, Users, DollarSign, Mic, MicOff, Volume2,
  Pin
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { useAICreditGuard } from './credits/AICreditConfirmationDialog';
import AssistantQueryResult from './assistant/AssistantQueryResult';
import AssistantPreviewCard from './assistant/AssistantPreviewCard';
import AssistantEmptyState from './assistant/AssistantEmptyState';
import AssistantErrorBlock from './assistant/AssistantErrorBlock';
import AssistantModeSwitcher from './assistant/AssistantModeSwitcher';
import AssistantRoutinesModal from './assistant/AssistantRoutinesModal';
import AssistantNextSteps from './assistant/AssistantNextSteps';
import AssistantBulkActionCard from './assistant/AssistantBulkActionCard';
import { createSavedCommand, getNextStepSuggestions, recordRoutineRun } from '../utils/assistantPrefsApi';
import { useNavigate } from 'react-router-dom';
import { usePageContext } from '../context/PageContext';

// Phrases that trigger the overdue-reminders bulk preview card.
// Kept deliberately narrow — only matches when "overdue" is explicit
// (avoids false positives like "send reminder to John").
const BULK_OVERDUE_PATTERNS = [
  /\bremind\b.*\boverdue\b/i,
  /\boverdue\b.*\bremind/i,
  /\bsend\s+(out\s+)?(the\s+)?overdue\s+reminders?\b/i,
  /\bchase\s+(all\s+)?overdue\b/i,
];

const API_URL = process.env.REACT_APP_BACKEND_URL;

const QUERY_INTENTS = new Set([
  'overdue_invoices', 'ar_by_customer', 'jobs_due', 'artwork_pending',
  'employee_hours', 'production_load', 'jobs_in_production',
  'revenue', 'revenue_by_source', 'top_categories',
]);

// Phrases that strongly suggest navigation/context commands.
// We send them through /assistant/resolve FIRST before the generic auto-classifier.
const NAV_HINT_PATTERNS = [
  /\b(open|show|take me to|go to|view|navigate|display)\b/i,
  /\b(this|that|current|related|linked|the)\s+(order|customer|invoice|ticket|employee|job|schedule)\b/i,
  /\bORD-\d+\b/i,
];

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
  const { token } = useAuth();
  const { runGuardedAction, dialog: creditDialog } = useAICreditGuard();
  const navigate = useNavigate();
  const pageContext = usePageContext();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);
  const [sessionId] = useState(() => `floating_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [isRecording, setIsRecording] = useState(false);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [pendingTranscript, setPendingTranscript] = useState(null);
  const [recentCommands, setRecentCommands] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('assistant_recent_commands') || '[]');
    } catch {
      return [];
    }
  });
  const [mode, setMode] = useState('guided');
  const [routinesOpen, setRoutinesOpen] = useState(false);
  const [savedRefreshKey, setSavedRefreshKey] = useState(0);
  const [activeRoutine, setActiveRoutine] = useState(null); // { id, name, step, total }
  const routineAbortRef = useRef(false);

  const pushRecentCommand = (text) => {
    setRecentCommands((prev) => {
      const trimmed = text.trim();
      if (!trimmed) return prev;
      const next = [trimmed, ...prev.filter((c) => c !== trimmed)].slice(0, 8);
      try { localStorage.setItem('assistant_recent_commands', JSON.stringify(next)); } catch { /* ignore */ }
      return next;
    });
  };
  const [position, setPosition] = useState({ right: 24, bottom: 80 });
  const [isDragging, setIsDragging] = useState(false);
  const recordingTimeoutRef = useRef(null);
  const dragRef = useRef({ startX: 0, startY: 0, startRight: 24, startBottom: 80 });
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const messagesRef = useRef([]);

  // Keep a live ref of messages so async loops (e.g., routine runs) always
  // read the latest conversation history instead of a stale closure.
  useEffect(() => { messagesRef.current = messages; }, [messages]);

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

  const handleSend = async (messageText = input, source = 'text') => {
    if (!messageText.trim() || loading) return;

    pushRecentCommand(messageText);
    const userMessage = createAssistantMessage({ role: 'user', content: messageText.trim() });
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Phase 5: detect bulk action trigger BEFORE LLM classification.
      if (BULK_OVERDUE_PATTERNS.some((re) => re.test(messageText))) {
        setMessages(prev => [...prev, createAssistantMessage({
          role: 'assistant',
          bulkAction: { kind: 'overdue_reminders' },
        })]);
        return;
      }

      // Phase 3: try navigation/context resolver FIRST when the message looks
      // like a nav command. Falls through to parse-action if not navigational.
      const looksLikeNav = NAV_HINT_PATTERNS.some((re) => re.test(messageText));
      if (looksLikeNav) {
        const navResult = await runResolveNavigation(messageText, pageContext);
        if (navResult?.handled) return; // already navigated via toast
        if (navResult?.message) {
          setMessages(prev => [...prev, navResult.message]);
          return;
        }
      }

      // Single brain: ask backend to classify intent. No frontend regex.
      const classified = await runParseAction(messageText, 'auto');
      const intent = classified?.intent || 'chat';

      // Phase 2: query intents (read live data) route to /assistant/query.
      if (QUERY_INTENTS.has(intent)) {
        const queryResult = await runQueryIntent(intent, classified?.filters || {});
        if (queryResult) {
          setMessages(prev => [...prev, queryResult]);
          return;
        }
      }

      if (intent !== 'chat' && !QUERY_INTENTS.has(intent)) {
        const actionResult = await routeClassifiedIntent(intent, classified, messageText, source);
        if (actionResult) {
          setMessages(prev => [...prev, actionResult]);
          return;
        }
      }

      // Regular chat — general Q&A. Include context so chat knows where user is.
      await runGuardedAction({
        actionType: 'assistant_chat',
        featureName: 'Floating AI Assistant',
        execute: async () => {
          const response = await axios.post(
            `${API_URL}/api/ai/assistant`,
            {
              message: messageText.trim(),
              session_id: sessionId,
              conversation_history: messagesRef.current.slice(-10),
              context: pageContext,
            },
            { headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } }
          );
          const assistantMessage = createAssistantMessage({ role: 'assistant', content: response.data.response });
          setMessages(prev => [...prev, assistantMessage]);
          return response.data;
        }
      });
    } catch (error) {
      console.error('Error:', error);
      const errorMsg = error.response?.data?.detail || 'Something went wrong. Please try again.';
      setMessages(prev => [...prev, createAssistantMessage({ role: 'assistant', content: `Sorry, ${errorMsg}`, isError: true })]);
    } finally {
      setLoading(false);
    }
  };

  const runResolveNavigation = async (message, context) => {
    return await runGuardedAction({
      actionType: 'assistant_nav_classify',
      featureName: 'Business Assistant navigation',
      execute: async () => {
        const resp = await axios.post(
          `${API_URL}/api/ai/assistant/resolve`,
          { message, context: context || null },
          { headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } }
        );
        const actions = resp.data?.actions || [];
        // If resolver returned no actions at all, fall through to parse-action/chat.
        if (!actions.length && !resp.data?.message) return null;

        // Auto-navigate for a single direct "kind=navigate" action.
        const singleNavigate = actions.length === 1 && actions[0].kind === 'navigate';
        if (singleNavigate) {
          setIsOpen(false);
          navigate(actions[0].route);
          toast.success(`Opened: ${actions[0].label}`);
          return { handled: true };
        }

        // Otherwise render as a structured result (clarification / multiple candidates).
        return {
          message: createAssistantMessage({
            role: 'assistant',
            queryResult: {
              query_type: 'navigation',
              summary: resp.data.message || 'Pick one:',
              metrics: [],
              rows: [],
              suggested_actions: actions.map((a, i) => ({
                id: `nav-${i}`,
                label: a.label,
                action: 'navigate',
                target: a.route,
                record_id: a.record_id,
                record_type: a.record_type,
              })),
            },
          }),
        };
      },
    });
  };

  const runQueryIntent = async (queryType, filters) => {
    return await runGuardedAction({
      actionType: 'assistant_query',
      featureName: `Business Assistant live query: ${queryType}`,
      execute: async () => {
        const resp = await axios.post(
          `${API_URL}/api/ai/assistant/query`,
          { query_type: queryType, filters: filters || {} },
          { headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } }
        );
        return createAssistantMessage({
          role: 'assistant',
          queryResult: resp.data,
        });
      },
    });
  };

  const handleQueryActionClick = (a) => {
    if (!a) return;
    if (a.action === 'navigate' && a.target) {
      setIsOpen(false);
      navigate(a.target);
      return;
    }
    if (a.action === 'assistant_action') {
      // Phase 2: surface that follow-up actions aren't wired yet; don't fake success.
      toast.info(`"${a.label}" is not wired up yet — I can show this data, but the follow-up action will land in a later phase.`);
      return;
    }
  };

  const handleNextStepClick = (s) => {
    if (!s) return;
    if (s.action === 'navigate' && s.target) {
      setIsOpen(false);
      navigate(s.target);
      return;
    }
    if (s.action === 'rerun_command' && s.target) {
      handleSend(s.target, 'text');
    }
  };

  const handlePinCommand = async (text) => {
    const trimmed = (text || '').trim();
    if (!trimmed) return;
    try {
      await createSavedCommand(token, { command: trimmed, label: trimmed.slice(0, 60), pinned: true });
      toast.success('Saved to pinned commands');
      setSavedRefreshKey((k) => k + 1);
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Could not save command');
    }
  };

  const triggerBulkReminders = () => {
    setMessages(prev => [...prev, createAssistantMessage({
      role: 'assistant',
      bulkAction: { kind: 'overdue_reminders' },
    })]);
  };

  const runRoutine = async (routine) => {
    if (!routine?.commands?.length || activeRoutine) return;
    routineAbortRef.current = false;
    const total = routine.commands.length;
    setActiveRoutine({ id: routine.id, name: routine.name, step: 0, total });
    try {
      for (let i = 0; i < routine.commands.length; i += 1) {
        if (routineAbortRef.current) break;
        setActiveRoutine((prev) => prev ? { ...prev, step: i + 1 } : prev);
        // eslint-disable-next-line no-await-in-loop
        await handleSend(routine.commands[i], 'text');
      }
      if (routineAbortRef.current) {
        toast.info(`Routine "${routine.name}" aborted`);
      } else {
        try { await recordRoutineRun(token, routine.id); } catch {}
        toast.success(`Routine "${routine.name}" complete`);
      }
    } catch (err) {
      toast.error(`Routine stopped: ${err?.message || 'error'}`);
    } finally {
      setActiveRoutine(null);
      routineAbortRef.current = false;
    }
  };

  const abortRoutine = () => {
    routineAbortRef.current = true;
  };

  const routeClassifiedIntent = async (intent, classified, rawMessage, source) => {
    // The backend returned a classified write intent. Build a preview for the user.
    if (classified?.needs_more_info) {
      return createAssistantMessage({
        role: 'assistant',
        content: classified.question || 'I need a bit more info — can you clarify?',
      });
    }

    const params = classified?.parameters || {};

    switch (intent) {
      case 'create_order':
      case 'create_job': {
        if (!params.customer_name && !params.company_name) {
          return createAssistantMessage({
            role: 'assistant',
            content: 'Who is this order for? Please give me a customer name or company.',
          });
        }
        const warnings = [];
        if (source === 'voice') warnings.push('Voice command — please confirm before I create this.');
        setPendingAction({
          type: 'create_order',
          params,
          source,
          description: `Create order for ${params.customer_name || params.company_name}`,
        });
        return createAssistantMessage({
          role: 'assistant',
          previewCard: {
            title: 'Create Order',
            fields: [
              { label: 'Customer', value: params.customer_name || params.company_name },
              { label: 'Company', value: params.company_name || '—' },
              { label: 'Due Date', value: params.requested_due_date || 'Not set' },
              { label: 'Description', value: params.description || '—' },
              { label: 'Pickup/Delivery', value: params.pickup_delivery_method || 'pickup' },
            ],
            warnings,
            confirmLabel: 'Create Order',
            intent: 'create_order',
          },
        });
      }

      case 'create_calendar_event': {
        if (!params.title || !params.date) {
          return createAssistantMessage({
            role: 'assistant',
            content: 'What should the appointment be titled, and what date and time?',
          });
        }
        const warnings = [];
        if (source === 'voice') warnings.push('Voice command — please confirm before I schedule.');
        setPendingAction({
          type: 'create_calendar_event',
          params,
          source,
          description: `Schedule "${params.title}" on ${params.date}`,
        });
        return createAssistantMessage({
          role: 'assistant',
          previewCard: {
            title: 'Schedule Appointment',
            fields: [
              { label: 'Title', value: params.title },
              { label: 'Date', value: params.date },
              { label: 'Time', value: params.time || 'TBD' },
              { label: 'Duration', value: params.duration_minutes ? `${params.duration_minutes} min` : '60 min' },
              { label: 'Customer', value: params.customer_name || '—' },
              { label: 'Location', value: params.location || '—' },
            ],
            warnings,
            confirmLabel: 'Schedule It',
            intent: 'create_calendar_event',
          },
        });
      }

      case 'create_invoice': {
        if (!params.order_id && !params.order_number) {
          return createAssistantMessage({
            role: 'assistant',
            content: 'To generate an invoice I need a specific order. Which order number should I invoice? (e.g., "invoice ORD-0042")',
          });
        }
        const warnings = ['This will pull all current job-ticket line items from the order.'];
        if (source === 'voice') warnings.push('Voice command — please confirm before I create this invoice.');
        setPendingAction({
          type: 'create_invoice',
          params,
          source,
          description: `Create invoice for order ${params.order_number || params.order_id}`,
        });
        return createAssistantMessage({
          role: 'assistant',
          previewCard: {
            title: 'Create Invoice',
            fields: [
              { label: 'From Order', value: params.order_number || params.order_id },
              { label: 'Notes', value: params.notes || '—' },
              { label: 'Due Date', value: params.due_date || 'Inherits from order' },
            ],
            warnings,
            confirmLabel: 'Create Invoice',
            intent: 'create_invoice',
          },
        });
      }

      case 'log_time_entry': {
        if (!params.hours) {
          return createAssistantMessage({
            role: 'assistant',
            content: 'How many hours should I log, and for which order?',
          });
        }
        const warnings = [];
        if (source === 'voice') warnings.push('Voice command — please confirm before logging time.');
        setPendingAction({
          type: 'log_time_entry',
          params,
          source,
          description: `Log ${params.hours} hours for ${params.job_name || 'job'}`,
        });
        return createAssistantMessage({
          role: 'assistant',
          previewCard: {
            title: 'Log Time Entry',
            fields: [
              { label: 'Hours', value: params.hours },
              { label: 'Job', value: params.job_name || 'TBD' },
              { label: 'Task', value: params.task || 'General work' },
              { label: 'Date', value: params.date || 'Today' },
              { label: 'Billable', value: params.billable },
            ],
            warnings,
            confirmLabel: 'Log It',
            intent: 'log_time_entry',
          },
        });
      }

      default:
        return null;
    }
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

  const handleActionButton = async (action) => {
    if (action === 'send_transcript' && pendingTranscript) {
      const transcript = pendingTranscript;
      setPendingTranscript(null);
      handleSend(transcript, 'voice');
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
            confirmed: true,
            source: pendingAction.source || 'text',
          },
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        
        const result = response.data;
        
        if (result.status === 'executed') {
          // Phase 5: fetch next-step suggestions for this action
          let nextSteps = [];
          try {
            const ns = await getNextStepSuggestions(token, pendingAction.type, result.result || {});
            nextSteps = ns?.suggestions || [];
          } catch { /* non-critical */ }

          setMessages(prev => [...prev, createAssistantMessage({
            role: 'assistant',
            content: `Done! ${pendingAction.description}.\n\n${result.result?.message || 'Action completed successfully.'}`,
            isSuccess: true,
            nextSteps,
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
          {!isMinimized && (
            <AssistantModeSwitcher token={token} value={mode} onChange={setMode} />
          )}
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
          {/* Phase 5: running-routine pill with abort */}
          {activeRoutine && (
            <div
              className="px-3 py-1.5 bg-indigo-50 border-b border-indigo-100 text-[11px] text-indigo-900 flex items-center justify-between gap-2"
              data-testid="assistant-active-routine-pill"
            >
              <div className="flex items-center gap-1.5 truncate">
                <Loader2 className="h-3 w-3 animate-spin flex-shrink-0" />
                <span className="truncate">
                  Running <span className="font-semibold">{activeRoutine.name}</span>
                  <span className="text-indigo-500"> · step {activeRoutine.step}/{activeRoutine.total}</span>
                </span>
              </div>
              <button
                type="button"
                onClick={abortRoutine}
                className="rounded-full border border-indigo-300 bg-white px-2 py-0.5 text-[10px] font-semibold text-indigo-700 hover:bg-indigo-100 flex-shrink-0"
                data-testid="assistant-routine-abort"
              >
                Abort
              </button>
            </div>
          )}

          {/* Phase 3: page-context chip so users trust what the assistant is acting on */}
          {(pageContext?.record_label || pageContext?.page) && (
            <div
              className="px-3 py-1.5 bg-violet-50 border-b border-violet-100 text-[11px] text-violet-800 flex items-center gap-1.5"
              data-testid="floating-assistant-context-chip"
            >
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-violet-400" />
              {pageContext.record_label ? (
                <>
                  Acting on: <span className="font-semibold">{pageContext.record_label}</span>
                  {pageContext.record_type && (
                    <span className="text-violet-500"> · {pageContext.record_type}</span>
                  )}
                </>
              ) : (
                <>Viewing: <span className="font-semibold">{pageContext.page.replace(/_/g, ' ')}</span></>
              )}
            </div>
          )}

          {/* Messages Area */}
          <ScrollArea className="flex-1 p-3">
            <div className="space-y-3">
              {/* Phase 4 empty / idle state */}
              {messages.length === 0 && !loading && (
                <AssistantEmptyState
                  token={token}
                  pageContext={pageContext}
                  recentCommands={recentCommands}
                  savedRefreshKey={savedRefreshKey}
                  onExampleClick={(text) => handleSend(text, 'text')}
                  onOpenRoutines={() => setRoutinesOpen(true)}
                  onTriggerBulkReminders={triggerBulkReminders}
                />
              )}
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
                  <div className="flex flex-col gap-2 max-w-[85%]">
                    {message.bulkAction?.kind === 'overdue_reminders' ? (
                      <AssistantBulkActionCard
                        token={token}
                        onDone={() => {}}
                        onCancel={() => {
                          setMessages((prev) => prev.filter((m) => m.id !== message.id));
                        }}
                      />
                    ) : message.previewCard ? (
                      <AssistantPreviewCard
                        title={message.previewCard.title}
                        fields={message.previewCard.fields}
                        warnings={message.previewCard.warnings}
                        confirmLabel={message.previewCard.confirmLabel}
                        loading={loading && pendingAction?.type === message.previewCard.intent}
                        onConfirm={() => handleActionButton('confirm')}
                        onCancel={() => handleActionButton('cancel')}
                      />
                    ) : message.errorBlock ? (
                      <AssistantErrorBlock
                        title={message.errorBlock.title}
                        message={message.errorBlock.message}
                        errorType={message.errorBlock.errorType}
                        onRetry={message.errorBlock.onRetry}
                      />
                    ) : message.queryResult ? (
                      <div className="rounded-xl px-3 py-2 text-sm bg-slate-100 text-slate-800">
                        <AssistantQueryResult data={message.queryResult} onActionClick={handleQueryActionClick} />
                      </div>
                    ) : (
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
                    )}
                    {/* Action buttons (legacy — only for non-preview-card messages) */}
                    {message.actions && !message.previewCard && (
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
                    {/* Phase 5: next-step suggestions after successful action */}
                    {message.nextSteps?.length > 0 && (
                      <AssistantNextSteps
                        suggestions={message.nextSteps}
                        onAction={handleNextStepClick}
                      />
                    )}
                    {/* Phase 5: "pin this command" for user messages */}
                    {message.role === 'user' && (
                      <button
                        type="button"
                        onClick={() => handlePinCommand(message.content)}
                        className="self-end inline-flex items-center gap-1 text-[10px] text-slate-400 hover:text-violet-600 transition"
                        data-testid={`assistant-pin-btn-${message.id}`}
                        title="Save as pinned command"
                      >
                        <Pin className="h-2.5 w-2.5" /> Pin
                      </button>
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

          {/* Quick Actions - redundant when the empty state is visible */}
          {messages.length > 0 && messages.length <= 2 && (
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
    <AssistantRoutinesModal
      token={token}
      open={routinesOpen}
      onOpenChange={setRoutinesOpen}
      onRunRoutine={runRoutine}
      disableRun={!!activeRoutine}
    />
    </>
  );
}
