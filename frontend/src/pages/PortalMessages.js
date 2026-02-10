import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { PortalLayout } from './PortalDashboard';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { 
  Loader2, MessageSquare, Send, ChevronLeft, Plus, Paperclip,
  AlertCircle, CheckCircle, Clock
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export function PortalMessages() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [conversations, setConversations] = useState([]);
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [newConv, setNewConv] = useState({ subject: '', message: '' });
  const [creating, setCreating] = useState(false);
  const customerName = localStorage.getItem('portal_customer_name') || 'Customer';

  const fetchConversations = useCallback(async () => {
    const token = localStorage.getItem('portal_token');
    if (!token) {
      navigate('/customer-portal/login');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/portal/conversations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setConversations(data);
      } else if (response.status === 401) {
        navigate('/customer-portal/login');
      }
    } catch (err) {
      console.error('Error fetching conversations:', err);
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const handleCreateConversation = async () => {
    if (!newConv.subject.trim() || !newConv.message.trim()) {
      toast.error('Please enter a subject and message');
      return;
    }

    const token = localStorage.getItem('portal_token');
    setCreating(true);

    try {
      const response = await fetch(`${API_URL}/api/portal/conversations`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newConv)
      });

      if (response.ok) {
        const created = await response.json();
        setShowNewDialog(false);
        setNewConv({ subject: '', message: '' });
        navigate(`/customer-portal/messages/${created.id}`);
        toast.success('Message sent!');
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Failed to send message');
      }
    } catch (err) {
      toast.error('Network error. Please try again.');
    } finally {
      setCreating(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 86400000) { // Less than 24 hours
      return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    } else if (diff < 604800000) { // Less than a week
      return date.toLocaleDateString('en-US', { weekday: 'short' });
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  return (
    <PortalLayout activeNav="messages" customerName={customerName}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Messages</h2>
            <p className="text-slate-600 mt-1">Communicate with the sign shop</p>
          </div>
          <Button 
            className="bg-teal-500 hover:bg-teal-600"
            onClick={() => setShowNewDialog(true)}
          >
            <Plus className="h-4 w-4 mr-2" />
            New Message
          </Button>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
          </div>
        ) : conversations.length > 0 ? (
          <Card className="border-slate-200">
            <CardContent className="p-0 divide-y divide-slate-100">
              {conversations.map((conv) => (
                <Link 
                  key={conv.id}
                  to={`/customer-portal/messages/${conv.id}`}
                  className="block p-4 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                        conv.unread_customer > 0 ? 'bg-teal-100' : 'bg-slate-100'
                      }`}>
                        <MessageSquare className={`h-5 w-5 ${
                          conv.unread_customer > 0 ? 'text-teal-600' : 'text-slate-400'
                        }`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className={`font-medium truncate ${
                            conv.unread_customer > 0 ? 'text-slate-900' : 'text-slate-700'
                          }`}>
                            {conv.subject}
                          </p>
                          {conv.is_closed && (
                            <Badge variant="outline" className="text-xs">Closed</Badge>
                          )}
                        </div>
                        <p className="text-sm text-slate-500 truncate mt-1">
                          {conv.last_message_preview}
                        </p>
                      </div>
                    </div>
                    <div className="flex flex-col items-end ml-4">
                      <span className="text-xs text-slate-500">{formatDate(conv.last_message_at)}</span>
                      {conv.unread_customer > 0 && (
                        <Badge className="bg-teal-500 mt-1">
                          {conv.unread_customer}
                        </Badge>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </CardContent>
          </Card>
        ) : (
          <Card className="border-slate-200">
            <CardContent className="py-12 text-center">
              <MessageSquare className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500 mb-4">No conversations yet</p>
              <Button 
                className="bg-teal-500 hover:bg-teal-600"
                onClick={() => setShowNewDialog(true)}
              >
                <Plus className="h-4 w-4 mr-2" />
                Start a Conversation
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* New Conversation Dialog */}
      <Dialog open={showNewDialog} onOpenChange={setShowNewDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Message</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium text-slate-700">Subject</label>
              <Input
                value={newConv.subject}
                onChange={(e) => setNewConv({ ...newConv, subject: e.target.value })}
                placeholder="What's this about?"
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Message</label>
              <Textarea
                value={newConv.message}
                onChange={(e) => setNewConv({ ...newConv, message: e.target.value })}
                placeholder="Type your message..."
                className="mt-1"
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewDialog(false)}>
              Cancel
            </Button>
            <Button 
              className="bg-teal-500 hover:bg-teal-600"
              onClick={handleCreateConversation}
              disabled={creating}
            >
              {creating && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Send Message
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </PortalLayout>
  );
}

export function PortalConversation() {
  const navigate = useNavigate();
  const { conversationId } = useParams();
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [conversation, setConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef(null);
  const customerName = localStorage.getItem('portal_customer_name') || 'Customer';

  const fetchMessages = useCallback(async () => {
    const token = localStorage.getItem('portal_token');
    if (!token) {
      navigate('/customer-portal/login');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/portal/conversations/${conversationId}/messages`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setConversation(data.conversation);
        setMessages(data.messages);
      } else if (response.status === 401) {
        navigate('/customer-portal/login');
      }
    } catch (err) {
      console.error('Error fetching messages:', err);
    } finally {
      setLoading(false);
    }
  }, [navigate, conversationId]);

  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!newMessage.trim() || conversation?.is_closed) return;

    const token = localStorage.getItem('portal_token');
    setSending(true);

    try {
      const response = await fetch(`${API_URL}/api/portal/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: newMessage })
      });

      if (response.ok) {
        const msg = await response.json();
        setMessages([...messages, msg]);
        setNewMessage('');
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Failed to send message');
      }
    } catch (err) {
      toast.error('Network error. Please try again.');
    } finally {
      setSending(false);
    }
  };

  const formatTime = (dateStr) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <PortalLayout activeNav="messages" customerName={customerName}>
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
        </div>
      </PortalLayout>
    );
  }

  if (!conversation) {
    return (
      <PortalLayout activeNav="messages" customerName={customerName}>
        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <p className="text-slate-700">Conversation not found</p>
            <Link to="/customer-portal/messages">
              <Button className="mt-4">Back to Messages</Button>
            </Link>
          </CardContent>
        </Card>
      </PortalLayout>
    );
  }

  return (
    <PortalLayout activeNav="messages" customerName={customerName}>
      <div className="h-[calc(100vh-280px)] flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-4 pb-4 border-b border-slate-200">
          <Link to="/customer-portal/messages" className="text-slate-600 hover:text-teal-600">
            <ChevronLeft className="h-6 w-6" />
          </Link>
          <div className="flex-1">
            <h2 className="font-semibold text-slate-900">{conversation.subject}</h2>
            {conversation.is_closed && (
              <Badge variant="outline" className="mt-1">Closed</Badge>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto py-4 space-y-4">
          {messages.map((msg) => (
            <div 
              key={msg.id}
              className={`flex ${msg.sender_type === 'customer' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[70%] ${
                msg.sender_type === 'customer'
                  ? 'bg-teal-500 text-white rounded-l-xl rounded-tr-xl'
                  : 'bg-slate-100 text-slate-900 rounded-r-xl rounded-tl-xl'
              } px-4 py-3`}>
                {msg.sender_type === 'shop' && (
                  <p className="text-xs font-medium text-teal-600 mb-1">{msg.sender_name}</p>
                )}
                <p className="whitespace-pre-wrap">{msg.content}</p>
                {msg.file_url && (
                  <a 
                    href={msg.file_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className={`flex items-center gap-2 mt-2 text-sm ${
                      msg.sender_type === 'customer' ? 'text-teal-100' : 'text-teal-600'
                    }`}
                  >
                    <Paperclip className="h-4 w-4" />
                    {msg.file_name || 'Attachment'}
                  </a>
                )}
                <p className={`text-xs mt-1 ${
                  msg.sender_type === 'customer' ? 'text-teal-100' : 'text-slate-400'
                }`}>
                  {formatTime(msg.created_at)}
                </p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        {!conversation.is_closed ? (
          <div className="border-t border-slate-200 pt-4">
            <div className="flex gap-2">
              <Input
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type your message..."
                className="flex-1"
                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
              />
              <Button 
                className="bg-teal-500 hover:bg-teal-600"
                onClick={handleSendMessage}
                disabled={sending || !newMessage.trim()}
              >
                {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        ) : (
          <div className="border-t border-slate-200 pt-4 text-center">
            <p className="text-slate-500">This conversation is closed</p>
          </div>
        )}
      </div>
    </PortalLayout>
  );
}

export default PortalMessages;
