import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import WrapEmptyState from '../WrapEmptyState';
import WrapActionButtonGroup from '../WrapActionButtonGroup';
import { ClipboardList, Upload, Wand2, Eye, CheckCircle2 } from 'lucide-react';

export default function DesignTab() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard
          title="Design Questionnaire"
          icon={ClipboardList}
          testId="design-quest"
          action={<WrapActionButtonGroup actions={[{ label: 'Send Questionnaire', icon: ClipboardList }]} testId="design-quest-send" />}
        >
          <WrapEmptyState title="Questionnaire not sent yet" message="Customer answers will appear here once they submit the wrap design intake." />
        </WrapSectionCard>
        <WrapAIHelperCard
          title="Questionnaire AI"
          testId="design-quest-ai"
          actions={[
            { label: 'Summarize Answers' },
            { label: 'Create Design Brief' },
          ]}
        />
        <WrapSectionCard
          title="Artwork Uploads"
          icon={Upload}
          testId="design-art"
          action={<WrapActionButtonGroup actions={[{ label: 'Upload Artwork', icon: Upload }]} testId="design-art-upload" />}
        >
          <WrapEmptyState title="No artwork uploaded" />
        </WrapSectionCard>
        <WrapAIHelperCard
          title="Artwork AI"
          testId="design-art-ai"
          actions={[
            { label: 'Check Artwork Quality' },
            { label: 'Detect Missing Files' },
          ]}
        />
        <WrapSectionCard
          title="AI Mockup Generator"
          icon={Wand2}
          testId="design-mockup"
          action={<WrapActionButtonGroup actions={[{ label: 'Generate AI Mockup', icon: Wand2 }]} testId="design-mockup-gen" />}
        >
          <WrapEmptyState title="No mockups yet" message="Generated mockups will appear here." />
        </WrapSectionCard>
        <WrapAIHelperCard
          title="Mockup AI"
          testId="design-mockup-ai"
          actions={[
            { label: 'Generate Mockup' },
            { label: 'Create 3 Directions' },
            { label: 'Make Cleaner Version' },
            { label: 'Make Bolder Version' },
          ]}
        />
        <WrapSectionCard
          title="Proof Versions"
          icon={Eye}
          testId="design-proofs"
          action={<WrapActionButtonGroup
            testId="design-proof-actions"
            actions={[
              { label: 'Send Proof', icon: Eye },
              { label: 'Mark Proof Approved', icon: CheckCircle2 },
            ]}
          />}
        >
          <WrapEmptyState title="No proofs sent yet" />
        </WrapSectionCard>
        <WrapSectionCard title="Revision Notes" icon={ClipboardList} testId="design-revisions">
          <WrapEmptyState title="No revision requests" />
        </WrapSectionCard>
        <WrapAIHelperCard
          title="Proof / Revision AI"
          testId="design-proof-ai"
          actions={[
            { label: 'Summarize Revision' },
            { label: 'Write Proof Message' },
          ]}
        />
      </div>
      <WrapAIHelperCard
        title="Design AI Helper"
        description="Quick design actions"
        testId="design-ai-helper"
        actions={[
          { label: 'Summarize Answers' },
          { label: 'Create Design Brief' },
          { label: 'Check Artwork Quality' },
          { label: 'Generate Mockup' },
          { label: 'Create 3 Directions' },
          { label: 'Summarize Revision' },
          { label: 'Write Proof Message' },
        ]}
      />
    </div>
  );
}
