import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import WrapEmptyState from '../WrapEmptyState';
import { Image as ImageIcon } from 'lucide-react';

const GROUPS = [
  'Customer Uploads', 'Logo Files', 'Vehicle Photos', 'Inspection Photos',
  'Damage Photos', 'Mockups', 'Proofs', 'Print Files',
  'Before Photos', 'During Photos', 'After Photos',
  'Signed Documents', 'Aftercare Documents',
];

export default function PhotosFilesTab() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {GROUPS.map((g) => (
          <WrapSectionCard
            key={g}
            title={g}
            icon={ImageIcon}
            testId={`files-${g.toLowerCase().replace(/\W+/g, '-')}`}
          >
            <WrapEmptyState title="No files yet" />
          </WrapSectionCard>
        ))}
      </div>
      <WrapAIHelperCard
        title="Photos & Files AI Helper"
        testId="files-ai-helper"
        actions={[
          { label: 'Sort Files' },
          { label: 'Label Photos' },
          { label: 'Pick Best Photos' },
          { label: 'Create Caption' },
          { label: 'Create Social Post' },
          { label: 'Create Portfolio Description' },
        ]}
      />
    </div>
  );
}
