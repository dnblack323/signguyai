import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription
} from '../../components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '../../components/ui/select';
import {
  Timer, Plus, Trash2, GripVertical, Save, ArrowUp, ArrowDown,
  Edit2, Copy, BarChart3, Clock, CheckCircle2, AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { getAuthToken } from '../../lib/authStorage';

const API = process.env.REACT_APP_BACKEND_URL;

const CATEGORIES = [
  { value: 'vehicle_wrap', label: 'Vehicle Wrap' },
  { value: 'printed_signs', label: 'Printed Signs' },
  { value: 'cut_vinyl', label: 'Cut Vinyl / Decals' },
  { value: 'banners', label: 'Banners' },
  { value: 'apparel', label: 'Apparel' },
  { value: 'custom', label: 'Custom' }
];

export default function ProductionSettings() {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [workflowMode, setWorkflowMode] = useState('simple');
  const [savingWorkflowMode, setSavingWorkflowMode] = useState(false);
  const [categoryTemplateMap, setCategoryTemplateMap] = useState({});
  
  // Edit mode
  const [editingStages, setEditingStages] = useState([]);
  const [editingName, setEditingName] = useState('');
  
  // New template dialog
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [newTemplateName, setNewTemplateName] = useState('');
  const [newTemplateCategory, setNewTemplateCategory] = useState('custom');
  const [copyFromTemplate, setCopyFromTemplate] = useState('');
  
  // Analytics
  const [analytics, setAnalytics] = useState(null);
  const [stageReport, setStageReport] = useState([]);
  const selectedTemplateRef = useRef(null);

  useEffect(() => {
    selectedTemplateRef.current = selectedTemplate;
  }, [selectedTemplate]);

  const selectTemplate = useCallback((template) => {
    setSelectedTemplate(template);
    setEditingName(template.name);
    setEditingStages([...template.stages]);
  }, []);

  const loadWorkflowSettings = useCallback(async () => {
    try {
      const token = getAuthToken();
      const res = await axios.get(`${API}/api/production-timeline/settings`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setWorkflowMode(res.data?.workflow_mode || 'detailed');
      setCategoryTemplateMap(res.data?.category_template_map || {});
    } catch (err) {
      console.error('Failed to load workflow settings:', err);
    }
  }, []);

  const loadTemplates = useCallback(async () => {
    try {
      const token = getAuthToken();
      const res = await axios.get(`${API}/api/production-timeline/templates`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setTemplates(res.data);
      if (res.data.length > 0 && !selectedTemplateRef.current) {
        selectTemplate(res.data[0]);
      }
    } catch (err) {
      toast.error('Failed to load templates');
    } finally {
      setLoading(false);
    }
  }, [selectTemplate]);

  const loadAnalytics = useCallback(async () => {
    try {
      const token = getAuthToken();
      const [analyticsRes, reportRes] = await Promise.all([
        axios.get(`${API}/api/production-timeline/analytics`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        axios.get(`${API}/api/production-timeline/analytics/stage-report`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      setAnalytics(analyticsRes.data);
      setStageReport(reportRes.data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    }
  }, []);

  useEffect(() => {
    loadWorkflowSettings();
    loadTemplates();
    loadAnalytics();
  }, [loadWorkflowSettings, loadTemplates, loadAnalytics]);

  const handleStageChange = (index, field, value) => {
    const updated = [...editingStages];
    updated[index] = { ...updated[index], [field]: value };
    setEditingStages(updated);
  };

  const handleAddStage = () => {
    setEditingStages([
      ...editingStages,
      {
        name: `Stage ${editingStages.length + 1}`,
        order: editingStages.length + 1,
        auto_trigger: null,
        is_final: false
      }
    ]);
  };

  const handleRemoveStage = (index) => {
    const updated = editingStages.filter((_, i) => i !== index);
    // Reorder
    updated.forEach((s, i) => { s.order = i + 1; });
    setEditingStages(updated);
  };

  const handleMoveStage = (index, direction) => {
    if (direction === 'up' && index === 0) return;
    if (direction === 'down' && index === editingStages.length - 1) return;
    
    const updated = [...editingStages];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    [updated[index], updated[targetIndex]] = [updated[targetIndex], updated[index]];
    // Reorder
    updated.forEach((s, i) => { s.order = i + 1; });
    setEditingStages(updated);
  };

  const handleSaveTemplate = async () => {
    if (!selectedTemplate) return;
    
    // Can't save default templates - need to create custom
    if (selectedTemplate.is_default) {
      toast.error('Cannot edit default templates. Create a custom template instead.');
      return;
    }
    
    setSaving(true);
    try {
      const token = getAuthToken();
      await axios.put(
        `${API}/api/production-timeline/templates/${selectedTemplate.id}`,
        null,
        {
          params: { name: editingName },
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          data: { stages: editingStages }
        }
      );
      
      // Actually need to send stages in body
      await axios.put(
        `${API}/api/production-timeline/templates/${selectedTemplate.id}?name=${encodeURIComponent(editingName)}`,
        { stages: editingStages },
        { headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } }
      );
      
      toast.success('Template saved');
      loadTemplates();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save template');
    } finally {
      setSaving(false);
    }
  };

  const handleCreateTemplate = async () => {
    if (!newTemplateName.trim()) {
      toast.error('Please enter a template name');
      return;
    }
    
    setSaving(true);
    try {
      const token = getAuthToken();
      
      // Get stages to copy
      let stages = [];
      if (copyFromTemplate) {
        const sourceTemplate = templates.find(t => t.id === copyFromTemplate);
        if (sourceTemplate) {
          stages = sourceTemplate.stages.map(s => ({
            name: s.name,
            order: s.order,
            auto_trigger: s.auto_trigger,
            is_final: s.is_final
          }));
        }
      }
      
      if (stages.length === 0) {
        // Default stages
        stages = [
          { name: 'Design', order: 1 },
          { name: 'Production', order: 2 },
          { name: 'Waiting on Customer Input', order: 3 },
          { name: 'On Hold', order: 4 },
          { name: 'Ready', order: 5, is_final: true }
        ];
      }
      
      const res = await axios.post(
        `${API}/api/production-timeline/templates`,
        { stages },
        {
          params: { name: newTemplateName, category: newTemplateCategory },
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
        }
      );
      
      toast.success('Template created');
      setShowNewDialog(false);
      setNewTemplateName('');
      setCopyFromTemplate('');
      loadTemplates();
      selectTemplate(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create template');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteTemplate = async () => {
    if (!selectedTemplate || selectedTemplate.is_default) return;
    
    if (!window.confirm('Are you sure you want to delete this template?')) return;
    
    try {
      const token = getAuthToken();
      await axios.delete(
        `${API}/api/production-timeline/templates/${selectedTemplate.id}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      toast.success('Template deleted');
      setSelectedTemplate(null);
      loadTemplates();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete template');
    }
  };

  const formatDuration = (minutes) => {
    if (!minutes && minutes !== 0) return '-';
    if (minutes < 60) return `${Math.round(minutes)}m`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    if (hours < 24) return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
    const days = Math.floor(hours / 24);
    return `${days}d`;
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Production Timeline Settings</h1>
          <p className="text-slate-300">Manage workflow templates and view production analytics</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Workflow Mode</CardTitle>
          <CardDescription>Choose a simple, detailed, or custom production workflow mode for new timelines.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="w-full md:max-w-sm">
            <Label>Workflow Mode</Label>
            <Select value={workflowMode} onValueChange={setWorkflowMode}>
              <SelectTrigger className="mt-2" data-testid="production-workflow-mode-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="simple">Simple Workflow</SelectItem>
                <SelectItem value="detailed">Detailed Workflow</SelectItem>
                <SelectItem value="custom">Custom Workflow</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button
            onClick={async () => {
              setSavingWorkflowMode(true);
              try {
                const token = getAuthToken();
                await axios.put(
                  `${API}/api/production-timeline/settings`,
                  { workflow_mode: workflowMode, category_template_map: categoryTemplateMap },
                  { headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } }
                );
                toast.success('Workflow mode saved');
              } catch (err) {
                toast.error('Failed to save workflow mode');
              } finally {
                setSavingWorkflowMode(false);
              }
            }}
            disabled={savingWorkflowMode}
            data-testid="production-workflow-mode-save-button"
          >
            <Save className="h-4 w-4 mr-2" />
            {savingWorkflowMode ? 'Saving...' : 'Save Workflow Mode'}
          </Button>
        </CardContent>
      </Card>

      <Tabs defaultValue="templates">
        <TabsList>
          <TabsTrigger value="templates" className="flex items-center gap-2">
            <Timer className="h-4 w-4" />
            Workflow Templates
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Analytics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="templates" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Template List */}
            <Card className="lg:col-span-1">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Templates</CardTitle>
                  <Button size="sm" onClick={() => setShowNewDialog(true)}>
                    <Plus className="h-4 w-4 mr-1" />
                    New
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y">
                  {templates.map((template) => (
                    <div
                      key={template.id}
                      className={`p-3 cursor-pointer hover:bg-slate-50 transition-colors ${
                        selectedTemplate?.id === template.id ? 'bg-teal-50 border-l-2 border-l-teal-500' : ''
                      }`}
                      onClick={() => selectTemplate(template)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-sm">{template.name}</p>
                          <p className="text-xs text-slate-500">
                            {template.stages?.length || 0} stages
                          </p>
                        </div>
                        {template.is_default && (
                          <Badge variant="outline" className="text-xs">Default</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Template Editor */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    {selectedTemplate ? (
                      selectedTemplate.is_default ? (
                        <div>
                          <CardTitle>{selectedTemplate.name}</CardTitle>
                          <CardDescription>Default template (read-only)</CardDescription>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <Input
                            value={editingName}
                            onChange={(e) => setEditingName(e.target.value)}
                            className="text-lg font-semibold"
                          />
                          {categoryTemplateMap[selectedTemplate.category] === selectedTemplate.id && (
                            <Badge variant="outline" data-testid="production-template-active-badge">Active for category</Badge>
                          )}
                        </div>
                      )
                    ) : (
                      <CardTitle className="text-slate-400">Select a template</CardTitle>
                    )}
                  </div>
                  {selectedTemplate && !selectedTemplate.is_default && (
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={async () => {
                          const nextMap = { ...categoryTemplateMap, [selectedTemplate.category]: selectedTemplate.id };
                          setCategoryTemplateMap(nextMap);
                          try {
                            const token = getAuthToken();
                            await axios.put(
                              `${API}/api/production-timeline/settings`,
                              { workflow_mode: workflowMode, category_template_map: nextMap },
                              { headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } }
                            );
                            toast.success('Template set as active workflow for this category');
                          } catch (err) {
                            toast.error('Failed to assign template to category');
                          }
                        }}
                        data-testid="production-template-assign-button"
                      >
                        Use for Category
                      </Button>
                      <Button variant="outline" size="sm" onClick={handleDeleteTemplate}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      <Button size="sm" onClick={handleSaveTemplate} disabled={saving}>
                        <Save className="h-4 w-4 mr-1" />
                        {saving ? 'Saving...' : 'Save'}
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {selectedTemplate ? (
                  <div className="space-y-3">
                    {editingStages.map((stage, index) => (
                      <div
                        key={`${stage.name}-${stage.order}`}
                        className="flex items-center gap-2 p-3 border rounded-lg bg-slate-50"
                      >
                        <div className="text-slate-400 cursor-move">
                          <GripVertical className="h-4 w-4" />
                        </div>
                        
                        <Badge variant="outline" className="w-8 justify-center">
                          {stage.order}
                        </Badge>
                        
                        <Input
                          value={stage.name}
                          onChange={(e) => handleStageChange(index, 'name', e.target.value)}
                          className="flex-1"
                          disabled={selectedTemplate.is_default}
                        />
                        
                        {stage.auto_trigger && (
                          <Badge className="bg-blue-100 text-blue-700 text-xs">
                            Auto: {stage.auto_trigger}
                          </Badge>
                        )}
                        
                        {stage.is_final && (
                          <Badge className="bg-green-100 text-green-700 text-xs">
                            Final
                          </Badge>
                        )}
                        
                        {!selectedTemplate.is_default && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleMoveStage(index, 'up')}
                              disabled={index === 0}
                              className="h-8 w-8 p-0"
                            >
                              <ArrowUp className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleMoveStage(index, 'down')}
                              disabled={index === editingStages.length - 1}
                              className="h-8 w-8 p-0"
                            >
                              <ArrowDown className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleRemoveStage(index)}
                              className="h-8 w-8 p-0 text-red-500 hover:text-red-600"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    ))}
                    
                    {!selectedTemplate.is_default && (
                      <Button
                        variant="outline"
                        onClick={handleAddStage}
                        className="w-full"
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        Add Stage
                      </Button>
                    )}
                    
                    {selectedTemplate.is_default && (
                      <div className="text-center py-4 text-slate-500">
                        <p className="text-sm">This is a default template and cannot be edited.</p>
                        <Button
                          variant="outline"
                          size="sm"
                          className="mt-2"
                          onClick={() => {
                            setShowNewDialog(true);
                            setCopyFromTemplate(selectedTemplate.id);
                          }}
                        >
                          <Copy className="h-4 w-4 mr-1" />
                          Create Copy
                        </Button>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-400">
                    <Timer className="h-12 w-12 mx-auto mb-4" />
                    <p>Select a template to edit</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="mt-4">
          <div className="space-y-6">
            {/* Summary Cards */}
            {analytics && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-500">Total Timelines</p>
                        <p className="text-2xl font-bold">{analytics.total_timelines}</p>
                      </div>
                      <Timer className="h-8 w-8 text-slate-300" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-500">Completed</p>
                        <p className="text-2xl font-bold">{analytics.completed_timelines}</p>
                      </div>
                      <CheckCircle2 className="h-8 w-8 text-green-300" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-500">Avg Completion</p>
                        <p className="text-2xl font-bold">
                          {analytics.average_completion_time_minutes 
                            ? formatDuration(analytics.average_completion_time_minutes)
                            : '-'}
                        </p>
                      </div>
                      <Clock className="h-8 w-8 text-blue-300" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-500">Bottlenecks</p>
                        <p className="text-2xl font-bold">
                          {analytics.bottlenecks?.filter(b => b.is_bottleneck).length || 0}
                        </p>
                      </div>
                      <AlertTriangle className="h-8 w-8 text-yellow-300" />
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Stage Time Report */}
            <Card>
              <CardHeader>
                <CardTitle>Stage Time Report</CardTitle>
                <CardDescription>Average time spent in each production stage</CardDescription>
              </CardHeader>
              <CardContent>
                {stageReport.length > 0 ? (
                  <div className="space-y-3">
                    {stageReport.map((stage) => (
                      <div key={stage.stage_name} className="flex items-center gap-4">
                        <div className="w-48 flex-shrink-0">
                          <p className="font-medium text-sm">{stage.stage_name}</p>
                          <p className="text-xs text-slate-500">{stage.count} samples</p>
                        </div>
                        <div className="flex-1">
                          <div className="h-4 bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                analytics?.bottlenecks?.find(b => b.stage_name === stage.stage_name && b.is_bottleneck)
                                  ? 'bg-yellow-500'
                                  : 'bg-teal-500'
                              }`}
                              style={{
                                width: `${Math.min(100, (stage.avg_minutes / (stageReport[0]?.avg_minutes || 1)) * 100)}%`
                              }}
                            />
                          </div>
                        </div>
                        <div className="w-24 text-right">
                          <p className="font-medium">{formatDuration(stage.avg_minutes)}</p>
                          <p className="text-xs text-slate-500">
                            {formatDuration(stage.min_minutes)} - {formatDuration(stage.max_minutes)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-400">
                    <BarChart3 className="h-12 w-12 mx-auto mb-4" />
                    <p>No production data yet</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Bottlenecks */}
            {analytics?.bottlenecks?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Identified Bottlenecks</CardTitle>
                  <CardDescription>Stages that take significantly longer than average</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {analytics.bottlenecks.filter(b => b.is_bottleneck).map((bottleneck) => (
                      <div
                        key={bottleneck.stage_name}
                        className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <AlertTriangle className="h-5 w-5 text-yellow-600" />
                          <p className="font-medium">{bottleneck.stage_name}</p>
                        </div>
                        <Badge className="bg-yellow-100 text-yellow-800">
                          Avg: {formatDuration(bottleneck.avg_minutes)}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* New Template Dialog */}
      <Dialog open={showNewDialog} onOpenChange={setShowNewDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Template</DialogTitle>
            <DialogDescription>
              Create a custom workflow template for your production process
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label>Template Name</Label>
              <Input
                value={newTemplateName}
                onChange={(e) => setNewTemplateName(e.target.value)}
                placeholder="e.g., Large Format Printing"
              />
            </div>
            
            <div>
              <Label>Category</Label>
              <Select value={newTemplateCategory} onValueChange={setNewTemplateCategory}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>
                      {cat.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label>Copy Stages From (Optional)</Label>
              <Select value={copyFromTemplate} onValueChange={setCopyFromTemplate}>
                <SelectTrigger>
                  <SelectValue placeholder="Start from scratch" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Start from scratch</SelectItem>
                  {templates.map((t) => (
                    <SelectItem key={t.id} value={t.id}>
                      {t.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateTemplate} disabled={saving}>
              {saving ? 'Creating...' : 'Create Template'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
