// Phase 2E: AI Assistant tab — rule-based summary shell, NO real AI dispatch yet.
import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import { Button } from '../../ui/button';
import { Sparkles, AlertTriangle, Send, BarChart3, MessageSquare, LinkIcon } from 'lucide-react';
import {
  getNextBestAction,
  getMissingItems,
  getProfitRisk,
  getCommunicationSuggestions,
} from '../summaryHelpers';
import { toast } from 'sonner';

const TAB_LINKS = [
  ['vehicle', 'Vehicle Info'],
  ['measurements', 'Measurements'],
  ['pricing', 'Pricing'],
  ['design', 'Design'],
  ['contract', 'Contract'],
  ['inspection', 'Inspection'],
  ['production', 'Production'],
  ['install', 'Install'],
  ['aftercare', 'Aftercare'],
];

export default function AIAssistantTab({ wrapData, onJumpToTab }) {
  const nba = getNextBestAction(wrapData);
  const missing = getMissingItems(wrapData);
  const profit = getProfitRisk(wrapData);
  const suggestions = getCommunicationSuggestions(wrapData);

  const placeholderToast = (label) => toast.message(label, { description: 'AI dispatch will be connected in a later phase.' });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard title="Job Health" icon={Sparkles} testId="ai-job-health">
          <p className="text-sm text-slate-700">
            Workflow status: <span className="font-medium" data-testid="ai-job-health-status">{(wrapData?.pipeline_state?.workflow_complete) ? 'Complete' : `${missing.length} item(s) outstanding`}</span>
          </p>
          <p className="text-xs text-slate-500 mt-1">Next best action: <span className="font-medium text-slate-700" data-testid="ai-next-action-label">{nba.label}</span></p>
          {onJumpToTab && nba.tab !== 'overview' && (
            <Button size="sm" className="mt-2 bg-violet-600 hover:bg-violet-700 text-white" onClick={() => onJumpToTab(nba.tab)} data-testid="ai-next-action-go">
              Open {nba.tab}
            </Button>
          )}
        </WrapSectionCard>

        <WrapSectionCard title="Missing Information" icon={AlertTriangle} testId="ai-missing">
          {missing.length === 0 ? (
            <p className="text-sm text-emerald-700" data-testid="ai-missing-none">Nothing missing — workflow is on track.</p>
          ) : (
            <ul className="list-disc list-inside text-sm text-slate-700 space-y-0.5" data-testid="ai-missing-list">
              {missing.map((m) => <li key={m}>{m}</li>)}
            </ul>
          )}
        </WrapSectionCard>

        <WrapSectionCard title="Suggested Next Action" icon={Send} testId="ai-next-action">
          <p className="text-sm text-slate-700" data-testid="ai-suggested-action">{nba.label}</p>
        </WrapSectionCard>

        <WrapSectionCard title="Profit Risk" icon={BarChart3} testId="ai-profit-risk">
          <p className={`text-sm ${profit.level === 'warning' ? 'text-rose-700' : profit.level === 'ok' ? 'text-emerald-700' : 'text-slate-500'}`} data-testid="ai-profit-risk-text">
            {profit.message}
          </p>
        </WrapSectionCard>

        <WrapSectionCard title="Customer Communication Suggestions" icon={MessageSquare} testId="ai-comms">
          {suggestions.length === 0 ? (
            <p className="text-sm text-slate-500 italic">No suggested communications right now.</p>
          ) : (
            <div className="space-y-1" data-testid="ai-comms-list">
              {suggestions.map((s) => (
                <Button
                  key={s.key}
                  size="sm"
                  variant="outline"
                  className="w-full justify-start text-xs"
                  onClick={() => placeholderToast(s.label)}
                  data-testid={`ai-comm-${s.key}`}
                >
                  {s.label}
                </Button>
              ))}
            </div>
          )}
        </WrapSectionCard>

        <WrapSectionCard title="Quick Links" icon={LinkIcon} testId="ai-quick-links">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2" data-testid="ai-quicklinks-grid">
            {TAB_LINKS.map(([tab, label]) => (
              <Button
                key={tab}
                size="sm"
                variant="outline"
                onClick={() => onJumpToTab?.(tab)}
                className="text-xs h-8"
                data-testid={`ai-quicklink-${tab}`}
              >
                Go to {label}
              </Button>
            ))}
          </div>
        </WrapSectionCard>
      </div>

      <WrapAIHelperCard
        title="Workflow Completion Summary AI"
        testId="ai-global-helper"
        actions={[
          { label: 'Generate Full Job Summary' },
          { label: 'Draft Customer Update' },
          { label: 'Suggest Workflow Optimization' },
          { label: 'Find Profit Risk' },
          { label: 'Recommend Final Packet' },
        ]}
      />
    </div>
  );
}
