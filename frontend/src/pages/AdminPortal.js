import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription
} from '../components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '../components/ui/select';
import {
  MessageSquare, Send, Mail, FileText, Image, Upload, Clock, CheckCircle,
  AlertTriangle, RefreshCw, Eye, Plus, Search, User, Briefcase, X,
  ChevronRight, Paperclip, FolderOpen, Bell
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

export default function AdminPortal() {
  const { user, customers, fetchCustomers } = useApp();
  const [activeTab, setActiveTab] = useState('messages');
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);

  // Messages state
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  
  // New conversation dialog
  const [showNewConversation, setShowNewConversation] = useState(false);
  const [newConvCustomerId, setNewConvCustomerId] = useState('');
  const [newConvSubject, setNewConvSubject] = useState('');
  const [newConvMessage, setNewConvMessage] = useState('');
  const [creatingConversation, setCreatingConversation] = useState(false);

  // Artwork approvals state
  const [artworkQueue, setArtworkQueue] = useState([]);
  const [artworkFilter, setArtworkFilter] = useState('all');
  const [showSendArtwork, setShowSendArtwork] = useState(false);
  const [artworkCustomerId, setArtworkCustomerId] = useState('');
  const [artworkJobId, setArtworkJobId] = useState('');
  const [artworkFile, setArtworkFile] = useState(null);
  const [artworkDescription, setArtworkDescription] = useState('');
  const [uploadingArtwork, setUploadingArtwork] = useState(false);
  const [customerJobs, setCustomerJobs] = useState([]);

  // Documents state
  const [sharedDocuments, setSharedDocuments] = useState([]);

  // Forms state
  const [formRequests, setFormRequests] = useState([]);
  const [showSendForm, setShowSendForm] = useState(false);
  const [questionnaires, setQuestionnaires] = useState([]);
  const [formCustomerId, setFormCustomerId] = useState('');
  const [formJobId, setFormJobId] = useState('');
  const [selectedQuestionnaireId, setSelectedQuestionnaireId] = useState('');
  const [formInstructions, setFormInstructions] = useState('');
  const [formDueDate, setFormDueDate] = useState('');
  const [sendingForm, setSendingForm] = useState(false);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadDashboard();
    fetchCustomers();
  }, []);

  useEffect(() => {
    if (activeTab === 'messages') loadConversations();
    if (activeTab === 'artwork') loadArtworkQueue();
    if (activeTab === 'documents') loadSharedDocuments();
    if (activeTab === 'forms') loadFormRequests();
  }, [activeTab]);

  useEffect(() => {
    loadArtworkQueue();
  }, [artworkFilter]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadDashboard = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API}/api/admin-portal/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDashboard(data);
      }
    } catch (err) {
      console.error('Error loading dashboard:', err);
    }
    setLoading(false);
  };

  const loadConversations = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API}/api/admin-portal/conversations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
      }
    } catch (err) {
      console.error('Error loading conversations:', err);
    }
  };

  const loadConversationMessages = async (conversationId) => {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API}/api/admin-portal/conversations/${conversationId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedConversation(data.conversation);
        setMessages(data.messages);
        // Refresh conversation list to update unread counts
        loadConversations();
      }
    } catch (err) {
      console.error('Error loading messages:', err);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !selectedConversation) return;
    
    setSendingMessage(true);
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API}/api/admin-portal/conversations/${selectedConversation.id}/messages?content=${encodeURIComponent(newMessage)}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.ok) {
        const msg = await res.json();
        setMessages([...messages, msg]);
        setNewMessage('');
      } else {
        toast.error('Failed to send message');
      }
    } catch (err) {
      toast.error('Network error');
    }
    setSendingMessage(false);
  };

  const handleCreateConversation = async () => {
    if (!newConvCustomerId || !newConvMessage.trim()) {
      toast.error('Please select a customer and enter a message');
      return;
    }

    setCreatingConversation(true);
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API}/api/admin-portal/conversations`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          customer_id: newConvCustomerId,
          subject: newConvSubject || 'New Message',
          content: newConvMessage
        })
      });

      if (res.ok) {
        const data = await res.json();
        toast.success('Message sent to customer');
        setShowNewConversation(false);
        setNewConvCustomerId('');
        setNewConvSubject('');
        setNewConvMessage('');
        loadConversations();
        loadConversationMessages(data.conversation_id);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to send message');
      }
    } catch (err) {
      toast.error('Network error');
    }
    setCreatingConversation(false);
  };

  const loadArtworkQueue = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const url = artworkFilter === 'all' 
        ? `${API}/api/admin-portal/artwork-queue`
        : `${API}/api/admin-portal/artwork-queue?status=${artworkFilter}`;
      
      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setArtworkQueue(data);
      }
    } catch (err) {
      console.error('Error loading artwork queue:', err);
    }
  };

  const loadCustomerJobs = async (customerId) => {
    if (!customerId) {
      setCustomerJobs([]);
      return;
    }
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API}/api/admin-portal/jobs?customer_id=${customerId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCustomerJobs(data);
      }
    } catch (err) {
      console.error('Error loading jobs:', err);
    }
  };

  const handleUploadArtwork = async () => {
    if (!artworkCustomerId || !artworkJobId || !artworkFile) {
      toast.error('Please select customer, job, and upload a file');
      return;
    }

    setUploadingArtwork(true);
    try {
      const token = localStorage.getItem('auth_token');
      
      // First upload the file
      const formData = new FormData();
      formData.append('file', artworkFile);
      
      const uploadRes = await fetch(`${API}/api/documents/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (!uploadRes.ok) {
        throw new Error('Failed to upload file');
      }

      const uploadData = await uploadRes.json();
      
      // Now send the artwork for approval
      const sendRes = await fetch(`${API}/api/admin-portal/artwork/send`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          job_id: artworkJobId,
          customer_id: artworkCustomerId,
          file_url: uploadData.file_url,
          file_name: artworkFile.name,
          description: artworkDescription
        })
      });

      if (sendRes.ok) {
        const data = await sendRes.json();
        toast.success(`Artwork (Version ${data.version}) sent for approval`);
        setShowSendArtwork(false);
        setArtworkCustomerId('');
        setArtworkJobId('');
        setArtworkFile(null);
        setArtworkDescription('');
        loadArtworkQueue();
        loadDashboard();
      } else {
        const err = await sendRes.json();
        toast.error(err.detail || 'Failed to send artwork');
      }
    } catch (err) {
      toast.error(err.message || 'Error uploading artwork');
    }
    setUploadingArtwork(false);
  };

  const loadSharedDocuments = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API}/api/admin-portal/documents`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSharedDocuments(data);
      }
    } catch (err) {
      console.error('Error loading documents:', err);
    }
  };

  const loadQuestionnaires = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API}/api/questionnaires`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setQuestionnaires(data.filter((item) => item.status === 'active'));
      }
    } catch (err) {
      console.error('Error loading questionnaires:', err);
    }
  };

  const loadFormRequests = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API}/api/admin-portal/forms`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setFormRequests(await res.json());
      }
      loadQuestionnaires();
    } catch (err) {
      console.error('Error loading form requests:', err);
    }
  };

  const handleSendForm = async () => {
    if (!formCustomerId || !selectedQuestionnaireId) {
      toast.error('Select a customer and questionnaire');
      return;
    }
    setSendingForm(true);
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API}/api/admin-portal/forms/send`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          customer_id: formCustomerId,
          questionnaire_id: selectedQuestionnaireId,
          job_id: formJobId || null,
          instructions: formInstructions,
          due_date: formDueDate || null
        })
      });
      if (res.ok) {
        toast.success('Form sent to customer portal');
        setShowSendForm(false);
        setFormCustomerId('');
        setFormJobId('');
        setSelectedQuestionnaireId('');
        setFormInstructions('');
        setFormDueDate('');
        loadFormRequests();
        loadDashboard();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to send form');
      }
    } catch (err) {
      toast.error('Network error');
    }
    setSendingForm(false);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 86400000) {
      return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    } else if (diff < 604800000) {
      return date.toLocaleDateString('en-US', { weekday: 'short', hour: 'numeric', minute: '2-digit' });
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      revision_requested: 'bg-orange-100 text-orange-800'
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Communications Hub</h1>
          <p className="text-slate-300">Manage customer communications, documents, and artwork approvals</p>
        </div>
      </div>

      {/* Stats Cards */}
      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="border-l-4 border-l-blue-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Unread Messages</p>
                  <p className="text-2xl font-bold">{dashboard.messages.unread}</p>
                </div>
                <MessageSquare className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-yellow-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Pending Approvals</p>
                  <p className="text-2xl font-bold">{dashboard.approvals.pending}</p>
                </div>
                <Clock className="h-8 w-8 text-yellow-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-orange-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Revisions Requested</p>
                  <p className="text-2xl font-bold">{dashboard.approvals.revision_requested}</p>
                </div>
                <RefreshCw className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-green-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Recently Approved</p>
                  <p className="text-2xl font-bold">{dashboard.approvals.recent_approved}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4 max-w-2xl">
          <TabsTrigger value="messages" className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            Messages
            {dashboard?.messages.unread > 0 && (
              <Badge className="bg-blue-500 text-xs">{dashboard.messages.unread}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="artwork" className="flex items-center gap-2">
            <Image className="h-4 w-4" />
            Artwork
            {dashboard?.approvals.pending > 0 && (
              <Badge className="bg-yellow-500 text-xs">{dashboard.approvals.pending}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="documents" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Documents
          </TabsTrigger>
          <TabsTrigger value="forms" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Forms
            {dashboard?.forms?.pending > 0 && (
              <Badge className="bg-cyan-500 text-xs">{dashboard.forms.pending}</Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Messages Tab */}
        <TabsContent value="messages" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-[600px]">
            {/* Conversation List */}
            <Card className="lg:col-span-1 flex flex-col">
              <CardHeader className="pb-2 flex-shrink-0">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Conversations</CardTitle>
                  <Button 
                    size="sm" 
                    className="bg-teal-500 hover:bg-teal-600"
                    onClick={() => setShowNewConversation(true)}
                  >
                    <Plus className="h-4 w-4 mr-1" /> New
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto p-0">
                {conversations.length === 0 ? (
                  <div className="p-4 text-center text-slate-500">
                    <MessageSquare className="h-8 w-8 mx-auto mb-2 text-slate-300" />
                    <p>No conversations yet</p>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {conversations.map((conv) => (
                      <div
                        key={conv.id}
                        className={`p-3 cursor-pointer hover:bg-slate-50 transition-colors ${
                          selectedConversation?.id === conv.id ? 'bg-teal-50 border-l-2 border-l-teal-500' : ''
                        }`}
                        onClick={() => loadConversationMessages(conv.id)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <p className="font-medium text-sm truncate">
                                {conv.customer?.name || 'Unknown Customer'}
                              </p>
                              {conv.unread_shop > 0 && (
                                <Badge className="bg-blue-500 text-xs">{conv.unread_shop}</Badge>
                              )}
                            </div>
                            <p className="text-xs text-slate-600 truncate">{conv.subject}</p>
                            <p className="text-xs text-slate-400 truncate mt-1">{conv.last_message_preview}</p>
                          </div>
                          <span className="text-xs text-slate-400 flex-shrink-0 ml-2">
                            {formatDate(conv.last_message_at)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Message Thread */}
            <Card className="lg:col-span-2 flex flex-col">
              {selectedConversation ? (
                <>
                  <CardHeader className="pb-2 border-b flex-shrink-0">
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-lg">{selectedConversation.subject}</CardTitle>
                        <p className="text-sm text-slate-500">
                          {selectedConversation.customer?.name} • {selectedConversation.customer?.email}
                        </p>
                      </div>
                      {selectedConversation.is_closed && (
                        <Badge variant="outline">Closed</Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex ${msg.sender_type === 'shop' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[70%] rounded-lg px-4 py-2 ${
                            msg.sender_type === 'shop'
                              ? 'bg-teal-500 text-white'
                              : 'bg-slate-100 text-slate-900'
                          }`}
                        >
                          {msg.sender_type === 'customer' && (
                            <p className="text-xs font-medium text-teal-600 mb-1">{msg.sender_name}</p>
                          )}
                          <p className="whitespace-pre-wrap">{msg.content}</p>
                          {msg.file_url && (
                            <a
                              href={msg.file_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1 mt-2 text-sm underline"
                            >
                              <Paperclip className="h-3 w-3" />
                              {msg.file_name || 'Attachment'}
                            </a>
                          )}
                          <p className={`text-xs mt-1 ${msg.sender_type === 'shop' ? 'text-teal-100' : 'text-slate-400'}`}>
                            {formatDate(msg.created_at)}
                          </p>
                        </div>
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </CardContent>
                  {!selectedConversation.is_closed && (
                    <div className="p-4 border-t flex-shrink-0">
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
                          disabled={sendingMessage || !newMessage.trim()}
                        >
                          <Send className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <CardContent className="flex-1 flex items-center justify-center">
                  <div className="text-center text-slate-400">
                    <MessageSquare className="h-12 w-12 mx-auto mb-4" />
                    <p>Select a conversation to view messages</p>
                  </div>
                </CardContent>
              )}
            </Card>
          </div>
        </TabsContent>

        {/* Artwork Tab */}
        <TabsContent value="artwork" className="mt-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Artwork Approval Queue</CardTitle>
                <div className="flex items-center gap-2">
                  <Select value={artworkFilter} onValueChange={setArtworkFilter}>
                    <SelectTrigger className="w-40">
                      <SelectValue placeholder="Filter" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="approved">Approved</SelectItem>
                      <SelectItem value="revision_requested">Revisions</SelectItem>
                      <SelectItem value="rejected">Rejected</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button
                    className="bg-teal-500 hover:bg-teal-600"
                    onClick={() => setShowSendArtwork(true)}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Send Artwork
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {artworkQueue.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <Image className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                  <p>No artwork proofs in queue</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {artworkQueue.map((proof) => (
                    <div
                      key={proof.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-16 h-16 bg-slate-100 rounded overflow-hidden flex-shrink-0">
                          {proof.thumbnail_url || proof.file_url ? (
                            <img
                              src={proof.thumbnail_url || proof.file_url}
                              alt="Proof thumbnail"
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <Image className="h-6 w-6 text-slate-400" />
                            </div>
                          )}
                        </div>
                        <div>
                          <p className="font-medium">{proof.job?.name || 'Unknown Job'}</p>
                          <p className="text-sm text-slate-600">{proof.customer?.name}</p>
                          <p className="text-xs text-slate-400">
                            Version {proof.version} • {formatDate(proof.created_at)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <Badge className={getStatusBadge(proof.status)}>
                          {proof.status.replace('_', ' ')}
                        </Badge>
                        {proof.customer_comment && (
                          <div className="max-w-xs">
                            <p className="text-xs text-slate-500 italic truncate">
                              "{proof.customer_comment}"
                            </p>
                          </div>
                        )}
                        <Button variant="outline" size="sm" asChild>
                          <a href={proof.file_url} target="_blank" rel="noopener noreferrer">
                            <Eye className="h-4 w-4 mr-1" /> View
                          </a>
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Documents Tab */}
        <TabsContent value="documents" className="mt-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Shared Documents</CardTitle>
                <p className="text-sm text-slate-500">
                  {sharedDocuments.filter(d => !d.viewed_at).length} unviewed
                </p>
              </div>
            </CardHeader>
            <CardContent>
              {sharedDocuments.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                  <p>No documents shared yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {sharedDocuments.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-blue-100 rounded flex items-center justify-center">
                          <FileText className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium">{doc.document?.name || 'Document'}</p>
                          <p className="text-sm text-slate-600">
                            Shared with {doc.customer?.name} • {formatDate(doc.created_at)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {doc.viewed_at ? (
                          <Badge variant="outline" className="text-green-600">
                            <Eye className="h-3 w-3 mr-1" /> Viewed
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-yellow-600">
                            <Clock className="h-3 w-3 mr-1" /> Not viewed
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="forms" className="mt-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Forms / Questionnaires</CardTitle>
                <Button className="bg-teal-500 hover:bg-teal-600" onClick={() => setShowSendForm(true)}>
                  <Plus className="h-4 w-4 mr-2" /> Send Form
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {formRequests.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                  <p>No portal forms sent yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {formRequests.map((request) => (
                    <div key={request.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50">
                      <div>
                        <p className="font-medium">{request.questionnaire_name}</p>
                        <p className="text-sm text-slate-600">{request.customer?.name} {request.job?.name ? `• ${request.job.name}` : ''}</p>
                        <p className="text-xs text-slate-400">Sent {formatDate(request.sent_at)} {request.due_date ? `• Due ${formatDate(request.due_date)}` : ''}</p>
                      </div>
                      <Badge className={request.status === 'completed' ? 'bg-green-100 text-green-800' : request.status === 'overdue' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'}>
                        {request.status.replace('_', ' ')}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={showSendForm} onOpenChange={setShowSendForm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send Questionnaire</DialogTitle>
            <DialogDescription>Send a form to a customer and optionally tie it to a job.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Customer</Label>
              <Select value={formCustomerId} onValueChange={(value) => { setFormCustomerId(value); setFormJobId(''); loadCustomerJobs(value); }}>
                <SelectTrigger><SelectValue placeholder="Select customer" /></SelectTrigger>
                <SelectContent>{customers.map((c) => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div>
              <Label>Job (optional)</Label>
              <Select value={formJobId} onValueChange={setFormJobId}>
                <SelectTrigger><SelectValue placeholder="Select job" /></SelectTrigger>
                <SelectContent>{customerJobs.map((j) => <SelectItem key={j.id} value={j.id}>{j.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div>
              <Label>Questionnaire</Label>
              <Select value={selectedQuestionnaireId} onValueChange={setSelectedQuestionnaireId}>
                <SelectTrigger><SelectValue placeholder="Select questionnaire" /></SelectTrigger>
                <SelectContent>{questionnaires.map((q) => <SelectItem key={q.id} value={q.id}>{q.name}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div>
              <Label>Due Date</Label>
              <Input type="date" value={formDueDate} onChange={(e) => setFormDueDate(e.target.value)} />
            </div>
            <div>
              <Label>Instructions</Label>
              <Textarea value={formInstructions} onChange={(e) => setFormInstructions(e.target.value)} rows={3} placeholder="Add instructions for the customer..." />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSendForm(false)}>Cancel</Button>
            <Button className="bg-teal-500 hover:bg-teal-600" onClick={handleSendForm} disabled={sendingForm}>{sendingForm ? 'Sending...' : 'Send Form'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* New Conversation Dialog */}
      <Dialog open={showNewConversation} onOpenChange={setShowNewConversation}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Message to Customer</DialogTitle>
            <DialogDescription>
              Start a conversation with a customer through their portal
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Customer</Label>
              <Select value={newConvCustomerId} onValueChange={setNewConvCustomerId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select customer" />
                </SelectTrigger>
                <SelectContent>
                  {customers.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.name} {c.company && `(${c.company})`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Subject (optional)</Label>
              <Input
                value={newConvSubject}
                onChange={(e) => setNewConvSubject(e.target.value)}
                placeholder="What's this about?"
              />
            </div>
            <div>
              <Label>Message</Label>
              <Textarea
                value={newConvMessage}
                onChange={(e) => setNewConvMessage(e.target.value)}
                placeholder="Type your message..."
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewConversation(false)}>
              Cancel
            </Button>
            <Button
              className="bg-teal-500 hover:bg-teal-600"
              onClick={handleCreateConversation}
              disabled={creatingConversation}
            >
              {creatingConversation ? 'Sending...' : 'Send Message'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Send Artwork Dialog */}
      <Dialog open={showSendArtwork} onOpenChange={setShowSendArtwork}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send Artwork for Approval</DialogTitle>
            <DialogDescription>
              Upload artwork and send it to the customer for review
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Customer</Label>
              <Select 
                value={artworkCustomerId} 
                onValueChange={(v) => {
                  setArtworkCustomerId(v);
                  setArtworkJobId('');
                  loadCustomerJobs(v);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select customer" />
                </SelectTrigger>
                <SelectContent>
                  {customers.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.name} {c.company && `(${c.company})`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Job</Label>
              <Select value={artworkJobId} onValueChange={setArtworkJobId} disabled={!artworkCustomerId}>
                <SelectTrigger>
                  <SelectValue placeholder={artworkCustomerId ? "Select job" : "Select customer first"} />
                </SelectTrigger>
                <SelectContent>
                  {customerJobs.map((j) => (
                    <SelectItem key={j.id} value={j.id}>
                      {j.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Artwork File</Label>
              <div className="mt-1">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={(e) => setArtworkFile(e.target.files[0])}
                  accept="image/*,.pdf,.ai,.eps,.psd"
                  className="hidden"
                />
                <Button
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full justify-start"
                >
                  <Upload className="h-4 w-4 mr-2" />
                  {artworkFile ? artworkFile.name : 'Choose file...'}
                </Button>
              </div>
            </div>
            <div>
              <Label>Description (optional)</Label>
              <Textarea
                value={artworkDescription}
                onChange={(e) => setArtworkDescription(e.target.value)}
                placeholder="Any notes for the customer..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSendArtwork(false)}>
              Cancel
            </Button>
            <Button
              className="bg-teal-500 hover:bg-teal-600"
              onClick={handleUploadArtwork}
              disabled={uploadingArtwork}
            >
              {uploadingArtwork ? 'Uploading...' : 'Send for Approval'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
