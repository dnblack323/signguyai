import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from './ui/sheet';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import {
  Activity,
  Calendar,
  CheckCircle2,
  Clock,
  DollarSign,
  FileCheck,
  FileText,
  FolderOpen,
  Loader2,
  MessageSquare,
  Paintbrush,
  Settings2,
  Truck,
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const filterOptions = [
  { value: 'all', label: 'All Events' },
  { value: 'production', label: 'Production Stages' },
  { value: 'artwork', label: 'Artwork / Proofs' },
  { value: 'customer', label: 'Customer Actions' },
  { value: 'financial', label: 'Financial Events' },
  { value: 'documents', label: 'Documents' },
  { value: 'general', label: 'General' },
];

const iconMap = {
  created: Activity,
  status_changed: Settings2,
  invoice_created: DollarSign,
  invoice_paid: DollarSign,
  artwork_uploaded: Paintbrush,
  approved: FileCheck,
  revision_requested: FileCheck,
  production_stage_started: Truck,
  production_stage_completed: CheckCircle2,
  document_uploaded: FolderOpen,
  note_added: MessageSquare,
};

const formatDateTime = (value) => {
  if (!value) return '-';
  return new Date(value).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
};

export const JobHistoryPanel = ({ isOpen, onClose, jobId, jobName, onOpenInvoice }) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState([]);
  const [filterGroup, setFilterGroup] = useState('all');

  useEffect(() => {
    const loadHistory = async () => {
      if (!isOpen || !jobId) return;
      setLoading(true);
      try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch(`${API}/jobs/${jobId}/history`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await response.json();
        setEvents(Array.isArray(data) ? data : []);
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
  }, [isOpen, jobId]);

  const visibleEvents = useMemo(() => {
    if (filterGroup === 'all') return events;
    return events.filter((event) => event.filter_group === filterGroup);
  }, [events, filterGroup]);

  const handleOpenRelated = (event) => {
    if (event.related_type === 'invoice' && event.related_id && onOpenInvoice) {
      onOpenInvoice(event.related_id);
      return;
    }
    if (event.related_type === 'proof') {
      navigate('/approvals');
      return;
    }
    if (event.related_type === 'document') {
      navigate('/documents');
    }
  };

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="w-[520px] sm:max-w-[520px]" data-testid="job-history-panel">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-teal-500" /> Job Timeline / History
          </SheetTitle>
          <SheetDescription>{jobName || 'Job history'}</SheetDescription>
        </SheetHeader>

        <div className="mt-5 space-y-4">
          <div className="space-y-2">
            <span className="text-sm text-muted-foreground">Filter</span>
            <Select value={filterGroup} onValueChange={setFilterGroup}>
              <SelectTrigger data-testid="job-history-filter-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                {filterOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-teal-500" /></div>
          ) : visibleEvents.length === 0 ? (
            <div className="rounded-xl border border-dashed p-6 text-center text-muted-foreground" data-testid="job-history-empty-state">
              No timeline events found for this filter.
            </div>
          ) : (
            <ScrollArea className="h-[calc(100vh-220px)] pr-3">
              <div className="space-y-4">
                {visibleEvents.map((event) => {
                  const Icon = iconMap[event.event_type] || Activity;
                  const isRelatedClickable = ['invoice', 'proof', 'document'].includes(event.related_type);
                  return (
                    <button
                      key={event.id}
                      type="button"
                      onClick={() => isRelatedClickable && handleOpenRelated(event)}
                      className={`w-full rounded-xl border p-4 text-left ${isRelatedClickable ? 'hover:border-teal-400 transition-colors' : ''}`}
                      data-testid={`job-history-event-${event.id}`}
                    >
                      <div className="flex items-start gap-3">
                        <div className="mt-1 rounded-full bg-muted/50 p-2">
                          <Icon className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div className="flex-1 space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-medium text-foreground">{event.title}</p>
                            <Badge variant="outline">{event.filter_group}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">{event.description}</p>
                          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                            <span>{event.user_name || 'System'}</span>
                            <span className="flex items-center gap-1"><Calendar className="h-3 w-3" /> {formatDateTime(event.timestamp)}</span>
                            {event.duration_minutes !== undefined && event.duration_minutes !== null && (
                              <span>Duration: {event.duration_minutes} min</span>
                            )}
                          </div>
                          {isRelatedClickable && <p className="text-xs text-teal-500">Open related record</p>}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </ScrollArea>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
};
