// Global AI summary/control tab. Lives alongside the contextual per-tab helpers
// so customers can deep-link to any specific helper from one place.
import { Bot, ArrowRight } from 'lucide-react';
import { Button } from '../../ui/button';
import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';

const QUICK_LINKS = [
  ['vehicle',      'Go to Vehicle AI Helper'],
  ['measurements', 'Go to Measurement AI Helper'],
  ['pricing',      'Go to Pricing AI Helper'],
  ['design',       'Go to Design AI Helper'],
  ['contract',     'Go to Contract AI Helper'],
  ['inspection',   'Go to Inspection AI Helper'],
  ['production',   'Go to Production AI Helper'],
  ['install',      'Go to Install AI Helper'],
  ['photos',       'Go to Photos AI Helper'],
  ['aftercare',    'Go to Aftercare AI Helper'],
];

export default function AIAssistantTab({ onJumpToTab }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard title="Job Health Summary" icon={Bot} testId="ai-job-health">
          <p className="text-sm text-slate-700">Phase 2 will analyze each tab's completeness and surface a one-line health score here.</p>
        </WrapSectionCard>
        <WrapSectionCard title="Missing Information Summary" icon={Bot} testId="ai-missing">
          <p className="text-sm text-slate-700">Highlights which fields/photos/approvals are still required to move to the next workflow stage.</p>
        </WrapSectionCard>
        <WrapSectionCard title="Suggested Next Action" icon={Bot} testId="ai-next-action">
          <p className="text-sm text-slate-700">Send design questionnaire to customer.</p>
        </WrapSectionCard>
        <WrapSectionCard title="Profit Risk Warning" icon={Bot} testId="ai-profit-risk">
          <p className="text-sm text-slate-700">Quoted margin will be compared to shop defaults in phase 2.</p>
        </WrapSectionCard>
        <WrapSectionCard title="Customer Communication Suggestions" icon={Bot} testId="ai-comms">
          <p className="text-sm text-slate-700">AI-drafted follow-up, status update, and review-request emails will appear here.</p>
        </WrapSectionCard>
        <WrapSectionCard title="Quick Links" icon={Bot} testId="ai-quick-links">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {QUICK_LINKS.map(([tabId, label]) => (
              <Button
                key={tabId}
                size="sm"
                variant="outline"
                className="justify-between text-xs"
                onClick={() => onJumpToTab && onJumpToTab(tabId)}
                data-testid={`ai-quicklink-${tabId}`}
              >
                {label}
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            ))}
          </div>
        </WrapSectionCard>
      </div>
      <WrapAIHelperCard
        title="AI Assistant"
        description="Global wrap AI controls"
        testId="ai-global-helper"
        actions={[
          { label: 'Run Job Health Check' },
          { label: 'Find Missing Info' },
          { label: 'Suggest Next Step' },
          { label: 'Check Profit Risk' },
        ]}
      />
    </div>
  );
}
