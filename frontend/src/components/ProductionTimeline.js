import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { ScrollArea } from './ui/scroll-area';
import {
  Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription
} from './ui/sheet';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription
} from './ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from './ui/select';
import {
  Clock, CheckCircle2, Circle, Play, Pause, ChevronRight,
  User, Calendar, Edit2, BarChart3, AlertTriangle, Timer, X
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { getAuthToken } from '../lib/authStorage';

const API = process.env.REACT_APP_BACKEND_URL;

// Production category options
const CATEGORIES = [
  { value: 'vehicle_wrap', label: 'Vehicle Wrap' },
  { value: 'printed_signs', label: 'Printed Signs' },
  { value: 'cut_vinyl', label: 'Cut Vinyl / Decals' },
  { value: 'banners', label: 'Banners' },
  { value: 'apparel', label: 'Apparel' }
];

export function ProductionTimelinePanel({ 
  isOpen, 
  onClose, 
  timeline, 
  onTimelineUpdate,
  lineItemName 
}) {
  const [stages, setStages] = useState([]);
  const [currentStageOrder, setCurrentStageOrder] = useState(1);
  const [advancing, setAdvancing] = useState(false);
  const [editingStage, setEditingStage] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [employees, setEmployees] = useState([]);

  useEffect(() => {
    if (timeline) {
      setStages(timeline.stages || []);
      setCurrentStageOrder(timeline.current_stage_order || 1);
    }
  }, [timeline]);

  useEffect(() => {
    const loadEmployees = async () => {
      try {
        const token = getAuthToken();
        const res = await axios.get(`${API}/api/employees`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        setEmployees(res.data || []);
      } catch (err) {
        console.error('Failed to load employees for timeline editor:', err);
      }
    };

    if (isOpen) {
      loadEmployees();
    }
  }, [isOpen]);

  const formatDuration = (minutes) => {
    if (!minutes && minutes !== 0) return '-';
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours < 24) return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
    const days = Math.floor(hours / 24);
    const remainingHours = hours % 24;
    return remainingHours > 0 ? `${days}d ${remainingHours}h` : `${days}d`;
  };

  const formatDateTime = (isoString) => {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const getStageIcon = (stage) => {
    if (stage.status === 'completed') {
      return <CheckCircle2 className="h-5 w-5 text-green-500" />;
    } else if (stage.status === 'in_progress') {
      return <Play className="h-5 w-5 text-blue-500 animate-pulse" />;
    } else if (stage.status === 'skipped') {
      return <X className="h-5 w-5 text-gray-400" />;
    }
    return <Circle className="h-5 w-5 text-gray-300" />;
  };

  const handleAdvanceStage = async () => {
    if (!timeline) return;
    setAdvancing(true);
    
    try {
      const token = getAuthToken();
      const res = await axios.post(
        `${API}/api/production-timeline/${timeline.id}/advance`,
        {},
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      toast.success('Stage advanced');
      onTimelineUpdate?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to advance stage');
    } finally {
      setAdvancing(false);
    }
  };

  const handleEditStage = (stage) => {
    setEditingStage(stage);
    setEditForm({
      assigned_user_id: stage.assigned_user_id || '',
      notes: stage.notes || '',
      manual_start_override: stage.started_at ? stage.started_at.slice(0, 16) : '',
      manual_end_override: stage.completed_at ? stage.completed_at.slice(0, 16) : ''
    });
  };

  const handleSaveStageEdit = async () => {
    if (!timeline || !editingStage) return;
    
    try {
      const token = getAuthToken();
      const updateData = {};
      
      if (editForm.notes !== editingStage.notes) {
        updateData.notes = editForm.notes;
      }
      if (editForm.assigned_user_id !== (editingStage.assigned_user_id || '')) {
        const assignedEmployee = employees.find((employee) => employee.id === editForm.assigned_user_id);
        updateData.assigned_user_id = editForm.assigned_user_id || null;
        updateData.assigned_user_name = assignedEmployee?.name || null;
      }
      if (editForm.manual_start_override && editForm.manual_start_override !== editingStage.started_at?.slice(0, 16)) {
        updateData.manual_start_override = new Date(editForm.manual_start_override).toISOString();
      }
      if (editForm.manual_end_override && editForm.manual_end_override !== editingStage.completed_at?.slice(0, 16)) {
        updateData.manual_end_override = new Date(editForm.manual_end_override).toISOString();
      }
      
      if (Object.keys(updateData).length > 0) {
        await axios.put(
          `${API}/api/production-timeline/${timeline.id}/stage/${editingStage.stage_order}`,
          updateData,
          { headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } }
        );
        
        toast.success('Stage updated');
        onTimelineUpdate?.();
      }
      
      setEditingStage(null);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update stage');
    }
  };

  const isCompleted = timeline?.completed_at;
  const currentStage = stages.find(s => s.stage_order === currentStageOrder);

  return (
    <>
      <Sheet open={isOpen} onOpenChange={onClose}>
        <SheetContent className="w-[450px] sm:max-w-[450px]">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              <Timer className="h-5 w-5 text-teal-500" />
              Production Timeline
            </SheetTitle>
            <SheetDescription>
              {lineItemName || 'Line Item'}
            </SheetDescription>
          </SheetHeader>

          <div className="mt-4">
            {/* Current Stage Card */}
            {!isCompleted && currentStage && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-blue-600 font-medium">CURRENT STAGE</p>
                    <p className="text-lg font-semibold text-blue-900">{currentStage.stage_name}</p>
                    {currentStage.started_at && (
                      <p className="text-xs text-blue-600">
                        Started {formatDateTime(currentStage.started_at)}
                      </p>
                    )}
                  </div>
                  <Button
                    onClick={handleAdvanceStage}
                    disabled={advancing}
                    className="bg-blue-500 hover:bg-blue-600"
                    size="sm"
                  >
                    {advancing ? 'Advancing...' : 'Complete Stage'}
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </div>
            )}

            {/* Completed Banner */}
            {isCompleted && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  <div>
                    <p className="font-medium text-green-800">Production Complete</p>
                    <p className="text-sm text-green-600">
                      Total time: {formatDuration(timeline?.total_duration_minutes)}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Timeline */}
            <ScrollArea className="h-[calc(100vh-280px)]">
              <div className="relative pl-6 pr-2">
                {/* Vertical line */}
                <div className="absolute left-[11px] top-0 bottom-0 w-0.5 bg-gray-200" />

                {stages.map((stage, index) => (
                  <div key={stage.id || index} className="relative pb-6 last:pb-0">
                    {/* Stage icon */}
                    <div className="absolute left-[-13px] bg-white p-0.5">
                      {getStageIcon(stage)}
                    </div>

                    {/* Stage content */}
                    <div className={`ml-4 p-3 rounded-lg border ${
                      stage.status === 'in_progress' 
                        ? 'bg-blue-50 border-blue-200' 
                        : stage.status === 'completed'
                        ? 'bg-gray-50 border-gray-200'
                        : 'bg-white border-gray-100'
                    }`}>
                      <div className="flex items-start justify-between">
                        <div>
                          <p className={`font-medium ${
                            stage.status === 'in_progress' ? 'text-blue-900' : 'text-gray-900'
                          }`}>
                            {stage.stage_name}
                          </p>
                          
                          {stage.assigned_user_name && (
                            <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                              <User className="h-3 w-3" />
                              {stage.assigned_user_name}
                            </p>
                          )}
                          
                          {stage.started_at && (
                            <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                              <Calendar className="h-3 w-3" />
                              {formatDateTime(stage.started_at)}
                            </p>
                          )}
                          
                          {stage.duration_minutes !== null && stage.duration_minutes !== undefined && (
                            <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                              <Clock className="h-3 w-3" />
                              Duration: {formatDuration(stage.duration_minutes)}
                              {stage.manually_adjusted && (
                                <Badge variant="outline" className="text-xs ml-1">Manual</Badge>
                              )}
                            </p>
                          )}
                          
                          {stage.notes && (
                            <p className="text-xs text-gray-600 mt-2 italic">"{stage.notes}"</p>
                          )}
                        </div>
                        
                        {stage.status !== 'pending' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEditStage(stage)}
                            className="h-7 w-7 p-0"
                          >
                            <Edit2 className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        </SheetContent>
      </Sheet>

      {/* Edit Stage Dialog */}
      <Dialog open={!!editingStage} onOpenChange={() => setEditingStage(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Stage: {editingStage?.stage_name}</DialogTitle>
            <DialogDescription>
              Update times and notes for this stage
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label>Assigned Employee</Label>
              <Select value={editForm.assigned_user_id || 'unassigned'} onValueChange={(value) => setEditForm({...editForm, assigned_user_id: value === 'unassigned' ? '' : value})}>
                <SelectTrigger className="mt-2" data-testid="timeline-stage-assigned-employee-select">
                  <SelectValue placeholder="Unassigned" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="unassigned">Unassigned</SelectItem>
                  {employees.map((employee) => (
                    <SelectItem key={employee.id} value={employee.id}>{employee.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Start Time (Override)</Label>
              <Input
                type="datetime-local"
                value={editForm.manual_start_override || ''}
                onChange={(e) => setEditForm({...editForm, manual_start_override: e.target.value})}
              />
            </div>
            
            <div>
              <Label>End Time (Override)</Label>
              <Input
                type="datetime-local"
                value={editForm.manual_end_override || ''}
                onChange={(e) => setEditForm({...editForm, manual_end_override: e.target.value})}
              />
            </div>
            
            <div>
              <Label>Notes</Label>
              <Textarea
                value={editForm.notes || ''}
                onChange={(e) => setEditForm({...editForm, notes: e.target.value})}
                placeholder="Add notes about this stage..."
                rows={3}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingStage(null)}>Cancel</Button>
            <Button onClick={handleSaveStageEdit} className="bg-teal-500 hover:bg-teal-600">
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}


export function EnableTimelineDialog({
  isOpen,
  onClose,
  jobId,
  lineItemId,
  lineItemName,
  onEnabled
}) {
  const [category, setCategory] = useState('printed_signs');
  const [enabling, setEnabling] = useState(false);

  const handleEnable = async () => {
    setEnabling(true);
    try {
      const token = getAuthToken();
      const res = await axios.post(
        `${API}/api/production-timeline/enable`,
        null,
        {
          params: { job_id: jobId, line_item_id: lineItemId, category },
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      toast.success('Production timeline enabled');
      onEnabled?.(res.data);
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to enable timeline');
    } finally {
      setEnabling(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Enable Production Timeline</DialogTitle>
          <DialogDescription>
            Track production stages for: {lineItemName}
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          <Label>Select Workflow Type</Label>
          <Select value={category} onValueChange={setCategory}>
            <SelectTrigger className="mt-2">
              <SelectValue placeholder="Select category" />
            </SelectTrigger>
            <SelectContent>
              {CATEGORIES.map((cat) => (
                <SelectItem key={cat.value} value={cat.value}>
                  {cat.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-gray-500 mt-2">
            Different workflows have different production stages
          </p>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button 
            onClick={handleEnable} 
            disabled={enabling}
            className="bg-teal-500 hover:bg-teal-600"
          >
            {enabling ? 'Enabling...' : 'Enable Timeline'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}


export function TimelineToggle({ 
  jobId, 
  lineItemId, 
  lineItemName,
  timelineEnabled,
  onTimelineChange 
}) {
  const [timeline, setTimeline] = useState(null);
  const [showPanel, setShowPanel] = useState(false);
  const [showEnableDialog, setShowEnableDialog] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (timelineEnabled && lineItemId) {
      loadTimeline();
    }
  }, [timelineEnabled, lineItemId]);

  const loadTimeline = async () => {
    try {
      const token = getAuthToken();
      const res = await axios.get(
        `${API}/api/production-timeline/line-item/${lineItemId}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      setTimeline(res.data);
    } catch (err) {
      console.error('Failed to load timeline:', err);
    }
  };

  const handleDisable = async () => {
    if (!window.confirm('Are you sure you want to disable the timeline? All tracking data will be lost.')) {
      return;
    }
    
    setLoading(true);
    try {
      const token = getAuthToken();
      await axios.delete(
        `${API}/api/production-timeline/line-item/${lineItemId}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      toast.success('Timeline disabled');
      setTimeline(null);
      onTimelineChange?.(false);
    } catch (err) {
      toast.error('Failed to disable timeline');
    } finally {
      setLoading(false);
    }
  };

  const handleEnabled = (newTimeline) => {
    setTimeline(newTimeline);
    onTimelineChange?.(true);
  };

  const currentStage = timeline?.stages?.find(s => s.stage_order === timeline.current_stage_order);
  const isCompleted = timeline?.completed_at;

  if (timelineEnabled && timeline) {
    return (
      <>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowPanel(true)}
            className="text-teal-600 border-teal-200 hover:bg-teal-50"
          >
            <Clock className="h-4 w-4 mr-1" />
            {isCompleted ? (
              <span className="flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3 text-green-500" />
                Complete
              </span>
            ) : (
              <span className="truncate max-w-[120px]">{currentStage?.stage_name || 'View Timeline'}</span>
            )}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDisable}
            disabled={loading}
            className="text-gray-400 hover:text-red-500 h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <ProductionTimelinePanel
          isOpen={showPanel}
          onClose={() => setShowPanel(false)}
          timeline={timeline}
          onTimelineUpdate={loadTimeline}
          lineItemName={lineItemName}
        />
      </>
    );
  }

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setShowEnableDialog(true)}
        className="text-gray-500 hover:text-teal-600"
      >
        <Clock className="h-4 w-4 mr-1" />
        Enable Timeline
      </Button>

      <EnableTimelineDialog
        isOpen={showEnableDialog}
        onClose={() => setShowEnableDialog(false)}
        jobId={jobId}
        lineItemId={lineItemId}
        lineItemName={lineItemName}
        onEnabled={handleEnabled}
      />
    </>
  );
}
