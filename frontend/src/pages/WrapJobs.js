import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import {
  Car, Search, RefreshCw, ExternalLink, ChevronRight,
  AlertCircle, Wrench
} from 'lucide-react';
import { useApp } from '../context/AppContext';

const STAGE_COLORS = {
  'New':            'bg-gray-100 text-gray-700',
  'Contract':       'bg-yellow-100 text-yellow-800',
  'Design / Proof': 'bg-purple-100 text-purple-800',
  'Production':     'bg-blue-100 text-blue-800',
  'Install':        'bg-indigo-100 text-indigo-800',
  'Inspection':     'bg-orange-100 text-orange-800',
  'Aftercare':      'bg-green-100 text-green-800',
};

export default function WrapJobs() {
  const navigate = useNavigate();
  const { api } = useApp();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [stageFilter, setStageFilter] = useState('all');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/wrap/jobs');
      setItems(res.data?.items || []);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load wrap jobs');
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => { load(); }, [load]);

  const stages = ['all', ...Array.from(new Set(items.map(i => i.pipeline_stage)))];

  const filtered = items.filter(item => {
    const q = search.toLowerCase();
    const matchSearch = !q
      || (item.customer_name || '').toLowerCase().includes(q)
      || (item.item_name || '').toLowerCase().includes(q)
      || (item.vehicle || '').toLowerCase().includes(q)
      || (item.order_number || '').toLowerCase().includes(q);
    const matchStage = stageFilter === 'all' || item.pipeline_stage === stageFilter;
    return matchSearch && matchStage;
  });

  return (
    <div className="p-6 space-y-5" data-testid="wrap-jobs-page">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-violet-100 rounded-lg">
            <Car className="w-5 h-5 text-violet-700" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Wrap Jobs</h1>
            <p className="text-sm text-gray-500">All active vehicle &amp; fleet wrap projects</p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={load}
          disabled={loading}
          data-testid="wrap-jobs-refresh"
        >
          <RefreshCw className={`w-4 h-4 mr-1.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Search customer, vehicle, order #..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-9"
            data-testid="wrap-jobs-search"
          />
        </div>
        <Select value={stageFilter} onValueChange={setStageFilter}>
          <SelectTrigger className="w-44" data-testid="wrap-jobs-stage-filter">
            <SelectValue placeholder="All Stages" />
          </SelectTrigger>
          <SelectContent>
            {stages.map(s => (
              <SelectItem key={s} value={s}>
                {s === 'all' ? 'All Stages' : s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Count */}
      {!loading && !error && (
        <p className="text-sm text-gray-500" data-testid="wrap-jobs-count">
          {filtered.length} {filtered.length === 1 ? 'job' : 'jobs'}
          {search || stageFilter !== 'all' ? ` (filtered from ${items.length})` : ''}
        </p>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-lg p-3" data-testid="wrap-jobs-error">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span className="text-sm">{error}</span>
          <Button variant="ghost" size="sm" onClick={load} className="ml-auto text-red-600">Retry</Button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="space-y-3">
          {[1,2,3].map(i => (
            <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      )}

      {/* Empty */}
      {!loading && !error && filtered.length === 0 && (
        <Card data-testid="wrap-jobs-empty">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <Car className="w-12 h-12 text-gray-300 mb-3" />
            <p className="font-medium text-gray-700">
              {items.length === 0 ? 'No wrap jobs yet' : 'No jobs match your filters'}
            </p>
            <p className="text-sm text-gray-500 mt-1 max-w-xs">
              {items.length === 0
                ? 'Create an order and add an item with a wrap category (Vehicle Wrap, Fleet Graphics, etc.) to get started.'
                : 'Try clearing the search or stage filter.'}
            </p>
            {items.length === 0 && (
              <Button className="mt-4" onClick={() => navigate('/orders')} data-testid="wrap-jobs-go-orders">
                Go to Orders
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Job list */}
      {!loading && !error && filtered.length > 0 && (
        <div className="space-y-2" data-testid="wrap-jobs-list">
          {filtered.map(item => (
            <div
              key={item.ticket_id}
              className="flex items-center gap-4 bg-white border border-gray-200 rounded-xl px-4 py-3 hover:border-violet-300 hover:shadow-sm transition-all group"
              data-testid={`wrap-job-row-${item.ticket_id}`}
            >
              {/* Stage icon */}
              <div className="flex-shrink-0 p-2 bg-violet-50 rounded-lg group-hover:bg-violet-100 transition-colors">
                <Wrench className="w-4 h-4 text-violet-600" />
              </div>

              {/* Main info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-gray-900 text-sm">
                    {item.customer_name}
                  </span>
                  {item.order_number && (
                    <span className="text-xs text-gray-400">· {item.order_number}</span>
                  )}
                  <Badge
                    className={`text-xs px-2 py-0 ${STAGE_COLORS[item.pipeline_stage] || 'bg-gray-100 text-gray-600'}`}
                    data-testid={`wrap-stage-badge-${item.ticket_id}`}
                  >
                    {item.pipeline_stage}
                  </Badge>
                </div>
                <p className="text-xs text-gray-500 mt-0.5 truncate">
                  {item.item_name}
                  {item.vehicle && <span className="ml-1.5 text-gray-400">· {item.vehicle}</span>}
                  {item.wrap_type && <span className="ml-1.5 text-gray-400">· {item.wrap_type}</span>}
                </p>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 flex-shrink-0">
                {item.order_id && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 text-xs text-gray-500 hidden sm:inline-flex"
                    onClick={() => navigate(`/orders/${item.order_id}`)}
                    data-testid={`wrap-job-view-order-${item.ticket_id}`}
                  >
                    <ExternalLink className="w-3 h-3 mr-1" />
                    Order
                  </Button>
                )}
                <Button
                  size="sm"
                  className="h-8 text-xs bg-violet-600 hover:bg-violet-700 text-white"
                  onClick={() => navigate(`/orders/${item.order_id}/items/${item.ticket_id}/wrap-command-center`)}
                  data-testid={`wrap-job-open-cc-${item.ticket_id}`}
                >
                  Open Command Center
                  <ChevronRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
