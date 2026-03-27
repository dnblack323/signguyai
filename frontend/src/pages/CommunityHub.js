import { useState, useEffect, useCallback, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import {
  Search, Bug, Lightbulb, MessageCircle, HelpCircle,
  Send, Pin, Check, ChevronUp, ChevronDown, X,
  ArrowLeft, Mail, Clock, Filter, Plus, Loader2,
  CheckCircle2, AlertCircle, Star
} from 'lucide-react';

const CATEGORIES = [
  { id: 'bug_report', label: 'Bug Report', icon: Bug, color: 'text-red-400', bg: 'bg-red-500/20' },
  { id: 'feature_request', label: 'Feature Request', icon: Lightbulb, color: 'text-amber-400', bg: 'bg-amber-500/20' },
  { id: 'question', label: 'Question', icon: HelpCircle, color: 'text-blue-400', bg: 'bg-blue-500/20' },
  { id: 'feedback', label: 'Feedback', icon: MessageCircle, color: 'text-green-400', bg: 'bg-green-500/20' },
];

const STATUS_LABELS = {
  open: { label: 'Open', color: 'bg-blue-500/20 text-blue-400' },
  in_progress: { label: 'In Progress', color: 'bg-amber-500/20 text-amber-400' },
  resolved: { label: 'Resolved', color: 'bg-green-500/20 text-green-400' },
  closed: { label: 'Closed', color: 'bg-gray-500/20 text-gray-500' },
};

const OWNER_EMAIL = 'thesigntistslab@gmail.com';

export default function CommunityHub() {
  const { api } = useApp();
  const { user } = useAuth();
  const [posts, setPosts] = useState([]);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState(null);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showNewPost, setShowNewPost] = useState(false);
  const [selectedPost, setSelectedPost] = useState(null);
  const [newPost, setNewPost] = useState({ title: '', body: '', category: 'question' });
  const [replyText, setReplyText] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const searchTimeout = useRef(null);

  const isAppOwner = user?.email === OWNER_EMAIL;

  const fetchPosts = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (categoryFilter) params.set('category', categoryFilter);
      if (statusFilter) params.set('status', statusFilter);
      const res = await api.get(`/community/posts?${params.toString()}`);
      setPosts(res.data.posts);
      setTotal(res.data.total);
    } catch { /* ignore */ } finally { setLoading(false); }
  }, [api, search, categoryFilter, statusFilter]);

  const fetchStats = useCallback(async () => {
    try {
      const res = await api.get('/community/stats');
      setStats(res.data);
    } catch { /* ignore */ }
  }, [api]);

  useEffect(() => { fetchPosts(); fetchStats(); }, [fetchPosts, fetchStats]);

  const handleSearch = (val) => {
    clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => setSearch(val), 400);
  };

  const handleCreatePost = async () => {
    if (!newPost.title.trim() || !newPost.body.trim()) {
      toast.error('Please fill in title and description');
      return;
    }
    setSubmitting(true);
    try {
      await api.post('/community/posts', newPost);
      toast.success('Post submitted!');
      setNewPost({ title: '', body: '', category: 'question' });
      setShowNewPost(false);
      fetchPosts();
      fetchStats();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create post');
    } finally { setSubmitting(false); }
  };

  const handleReply = async () => {
    if (!replyText.trim() || !selectedPost) return;
    setSubmitting(true);
    try {
      const res = await api.post(`/community/posts/${selectedPost.id}/reply`, { body: replyText });
      setSelectedPost(res.data);
      setReplyText('');
      fetchPosts();
      toast.success('Reply posted');
    } catch (err) {
      toast.error('Failed to post reply');
    } finally { setSubmitting(false); }
  };

  const handleUpvote = async (postId) => {
    try {
      const res = await api.post(`/community/posts/${postId}/upvote`);
      setPosts(prev => prev.map(p => p.id === postId ? { ...p, upvotes: res.data.upvotes, upvoted_by: res.data.upvoted ? [...(p.upvoted_by || []), user.id] : (p.upvoted_by || []).filter(id => id !== user.id) } : p));
      if (selectedPost?.id === postId) {
        setSelectedPost(prev => ({ ...prev, upvotes: res.data.upvotes }));
      }
    } catch { /* ignore */ }
  };

  const handlePin = async (postId, pinned) => {
    try {
      const res = await api.put(`/community/posts/${postId}`, { is_pinned: !pinned });
      fetchPosts();
      if (selectedPost?.id === postId) setSelectedPost(res.data);
    } catch { /* ignore */ }
  };

  const handleStatusChange = async (postId, status) => {
    try {
      const res = await api.put(`/community/posts/${postId}`, { status });
      fetchPosts();
      if (selectedPost?.id === postId) setSelectedPost(res.data);
      toast.success(`Status updated to ${status}`);
    } catch { /* ignore */ }
  };

  const getCat = (id) => CATEGORIES.find(c => c.id === id) || CATEGORIES[3];

  // Detail View
  if (selectedPost) {
    const cat = getCat(selectedPost.category);
    const CatIcon = cat.icon;
    const statusInfo = STATUS_LABELS[selectedPost.status] || STATUS_LABELS.open;

    return (
      <div className="p-6 max-w-4xl mx-auto space-y-4">
        <button onClick={() => setSelectedPost(null)} className="flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors" data-testid="back-to-list">
          <ArrowLeft className="w-4 h-4" /> Back to Community
        </button>

        <Card className="bg-white border-gray-200">
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${cat.bg}`}>
                  <CatIcon className={`w-5 h-5 ${cat.color}`} />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">{selectedPost.title}</h2>
                  <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
                    <span>{selectedPost.author_name}</span>
                    <span>-</span>
                    <span>{new Date(selectedPost.created_at).toLocaleDateString()}</span>
                    <Badge className={statusInfo.color}>{statusInfo.label}</Badge>
                    {selectedPost.is_pinned && <Badge className="bg-amber-500/20 text-amber-400"><Pin className="w-3 h-3 mr-1" />Pinned</Badge>}
                    {selectedPost.is_answered && <Badge className="bg-green-500/20 text-green-400"><CheckCircle2 className="w-3 h-3 mr-1" />Answered</Badge>}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="ghost" onClick={() => handleUpvote(selectedPost.id)} data-testid="upvote-btn">
                  <ChevronUp className="w-4 h-4 mr-1" /> {selectedPost.upvotes || 0}
                </Button>
                {isAppOwner && (
                  <>
                    <Button size="sm" variant="ghost" onClick={() => handlePin(selectedPost.id, selectedPost.is_pinned)}>
                      <Pin className={`w-4 h-4 ${selectedPost.is_pinned ? 'text-amber-400' : ''}`} />
                    </Button>
                    <select
                      value={selectedPost.status}
                      onChange={(e) => handleStatusChange(selectedPost.id, e.target.value)}
                      className="text-xs bg-gray-50 border border-gray-600 rounded px-2 py-1 text-gray-700"
                      data-testid="status-select"
                    >
                      <option value="open">Open</option>
                      <option value="in_progress">In Progress</option>
                      <option value="resolved">Resolved</option>
                      <option value="closed">Closed</option>
                    </select>
                  </>
                )}
              </div>
            </div>

            <div className="p-4 bg-gray-50 rounded-lg text-gray-700 whitespace-pre-wrap text-sm">
              {selectedPost.body}
            </div>
          </CardContent>
        </Card>

        {/* Replies */}
        <div className="space-y-3">
          <h3 className="text-gray-900 font-semibold">{selectedPost.replies?.length || 0} Replies</h3>
          {selectedPost.replies?.map((reply) => (
            <Card key={reply.id} className={`border ${reply.is_official ? 'border-green-500/30 bg-green-500/5' : 'border-gray-200 bg-white'}`}>
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-medium text-gray-900">{reply.author_name}</span>
                  {reply.is_official && <Badge className="bg-green-500/20 text-green-400 text-xs"><Star className="w-3 h-3 mr-1" />Official</Badge>}
                  <span className="text-xs text-gray-500">{new Date(reply.created_at).toLocaleDateString()}</span>
                </div>
                <p className="text-gray-700 text-sm whitespace-pre-wrap">{reply.body}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Reply Input */}
        <Card className="bg-white border-gray-200">
          <CardContent className="p-4">
            <Textarea
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder="Write a reply..."
              className="mb-3 bg-gray-50 border-gray-600 text-gray-900"
              rows={3}
              data-testid="reply-input"
            />
            <Button onClick={handleReply} disabled={submitting || !replyText.trim()} className="bg-blue-600 hover:bg-blue-700" data-testid="submit-reply-btn">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Send className="w-4 h-4 mr-2" />}
              Post Reply
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // List View
  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Community Hub</h1>
          <p className="text-gray-500 text-sm mt-1">Report bugs, request features, ask questions, and see answers</p>
        </div>
        <div className="flex gap-2">
          <a
            href="mailto:thesigntistslab@gmail.com?subject=SignGuy%20AI%20Support"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white border border-gray-200 text-gray-700 hover:text-gray-900 hover:border-gray-500 transition-colors text-sm"
            data-testid="contact-owner-btn"
          >
            <Mail className="w-4 h-4" /> Contact Support
          </a>
          <Button onClick={() => setShowNewPost(true)} className="bg-blue-600 hover:bg-blue-700" data-testid="new-post-btn">
            <Plus className="w-4 h-4 mr-2" /> New Post
          </Button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { label: 'Total Posts', value: stats.total_posts, color: 'text-gray-900' },
            { label: 'Answered', value: stats.answered, color: 'text-green-400' },
            { label: 'Open', value: stats.open, color: 'text-blue-400' },
            { label: 'Bug Reports', value: stats.bug_reports, color: 'text-red-400' },
            { label: 'Feature Requests', value: stats.feature_requests, color: 'text-amber-400' },
          ].map(s => (
            <div key={s.label} className="p-3 bg-white rounded-lg border border-gray-200 text-center">
              <p className={`text-xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-xs text-gray-500">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Search & Filters */}
      <div className="flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <Input
            placeholder="Search posts, answers, keywords..."
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-10 bg-white border-gray-200 text-gray-900"
            data-testid="community-search"
          />
        </div>
        <div className="flex gap-2">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700"
            data-testid="category-filter"
          >
            <option value="">All Categories</option>
            {CATEGORIES.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700"
            data-testid="status-filter"
          >
            <option value="">All Status</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      {/* New Post Form */}
      {showNewPost && (
        <Card className="bg-white border-blue-500/30">
          <CardHeader>
            <CardTitle className="text-gray-900 flex items-center justify-between">
              <span>Create a Post</span>
              <button onClick={() => setShowNewPost(false)}><X className="w-5 h-5 text-gray-500" /></button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              {CATEGORIES.map(c => {
                const Icon = c.icon;
                return (
                  <button
                    key={c.id}
                    onClick={() => setNewPost(p => ({ ...p, category: c.id }))}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm border transition-colors ${
                      newPost.category === c.id ? `${c.bg} border-current ${c.color}` : 'border-gray-200 text-gray-500 hover:border-gray-500'
                    }`}
                    data-testid={`category-${c.id}`}
                  >
                    <Icon className="w-4 h-4" /> {c.label}
                  </button>
                );
              })}
            </div>
            <div>
              <Label className="text-gray-700 text-xs mb-1">Title</Label>
              <Input
                value={newPost.title}
                onChange={(e) => setNewPost(p => ({ ...p, title: e.target.value }))}
                placeholder="Brief summary of your post"
                className="bg-gray-50 border-gray-600 text-gray-900"
                data-testid="post-title-input"
              />
            </div>
            <div>
              <Label className="text-gray-700 text-xs mb-1">Description</Label>
              <Textarea
                value={newPost.body}
                onChange={(e) => setNewPost(p => ({ ...p, body: e.target.value }))}
                placeholder="Provide details. For bugs, include steps to reproduce."
                className="bg-gray-50 border-gray-600 text-gray-900"
                rows={4}
                data-testid="post-body-input"
              />
            </div>
            <Button onClick={handleCreatePost} disabled={submitting} className="bg-blue-600 hover:bg-blue-700" data-testid="submit-post-btn">
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Send className="w-4 h-4 mr-2" />}
              Submit Post
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Posts List */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">
          <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" /> Loading...
        </div>
      ) : posts.length === 0 ? (
        <div className="text-center py-12">
          <MessageCircle className="w-10 h-10 mx-auto mb-3 text-gray-600" />
          <p className="text-gray-500">No posts yet. Be the first to share!</p>
        </div>
      ) : (
        <div className="space-y-2">
          {posts.map(post => {
            const cat = getCat(post.category);
            const CatIcon = cat.icon;
            const statusInfo = STATUS_LABELS[post.status] || STATUS_LABELS.open;
            const hasUpvoted = post.upvoted_by?.includes(user?.id);

            return (
              <Card
                key={post.id}
                className={`bg-white border-gray-200 hover:border-gray-500 transition-colors cursor-pointer ${post.is_pinned ? 'border-l-2 border-l-amber-400' : ''}`}
                onClick={() => setSelectedPost(post)}
                data-testid={`post-${post.id}`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    {/* Upvote */}
                    <div className="flex flex-col items-center gap-0" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => handleUpvote(post.id)}
                        className={`p-1 rounded hover:bg-gray-700 ${hasUpvoted ? 'text-blue-400' : 'text-gray-500'}`}
                        data-testid={`upvote-${post.id}`}
                      >
                        <ChevronUp className="w-5 h-5" />
                      </button>
                      <span className="text-sm font-medium text-gray-500">{post.upvotes || 0}</span>
                    </div>

                    {/* Category icon */}
                    <div className={`p-2 rounded-lg ${cat.bg} shrink-0`}>
                      <CatIcon className={`w-4 h-4 ${cat.color}`} />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-gray-900 font-medium truncate">{post.title}</h3>
                        {post.is_pinned && <Pin className="w-3 h-3 text-amber-400" />}
                        {post.is_answered && <CheckCircle2 className="w-3 h-3 text-green-400" />}
                      </div>
                      <p className="text-gray-500 text-sm truncate mt-0.5">{post.body}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        <span>{post.author_name}</span>
                        <span>{new Date(post.created_at).toLocaleDateString()}</span>
                        <Badge className={`${statusInfo.color} text-xs`}>{statusInfo.label}</Badge>
                        <Badge className={`${cat.bg} ${cat.color} text-xs`}>{cat.label}</Badge>
                        {post.replies?.length > 0 && (
                          <span className="flex items-center gap-1">
                            <MessageCircle className="w-3 h-3" /> {post.replies.length}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
