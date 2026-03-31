import { useMemo } from 'react';
import { Badge } from '../ui/badge';
import { Card, CardContent } from '../ui/card';
import { sortItemsByDate } from '../../lib/productivity';

const DEFAULT_COLUMNS = ['to_do', 'open', 'pending', 'approved', 'in_progress', 'scheduled', 'waiting', 'complete', 'done'];

const WRITABLE_TYPES = new Set(['task', 'job', 'production_task']);

export const ProductivityKanbanView = ({ items, onOpenItem, onMoveItem }) => {
  const groups = useMemo(() => {
    const grouped = {};
    items.forEach((item) => {
      const column = item.board_column || 'open';
      if (!grouped[column]) grouped[column] = [];
      grouped[column].push(item);
    });
    return grouped;
  }, [items]);

  const columns = Array.from(new Set([...DEFAULT_COLUMNS, ...Object.keys(groups)])).filter((column) => groups[column]?.length || DEFAULT_COLUMNS.includes(column));

  return (
    <div className="overflow-x-auto" data-testid="productivity-kanban-view">
      <div className="grid min-w-[1200px] gap-4" style={{ gridTemplateColumns: `repeat(${columns.length}, minmax(220px, 1fr))` }}>
        {columns.map((column) => (
          <div key={column} className="rounded-2xl border border-gray-200 bg-white p-3" onDragOver={(event) => event.preventDefault()} onDrop={(event) => {
            event.preventDefault();
            const uid = event.dataTransfer.getData('text/plain');
            const item = items.find((current) => current.uid === uid);
            if (item && onMoveItem) onMoveItem(item, column);
          }} data-testid={`kanban-column-${column}`}>
            <div className="sticky top-0 z-10 mb-3 flex items-center justify-between rounded-xl bg-gray-50 px-3 py-2">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-700">{column.replace(/_/g, ' ')}</h3>
              <Badge variant="outline">{groups[column]?.length || 0}</Badge>
            </div>
            <div className="space-y-3">
              {sortItemsByDate(groups[column] || []).map((item) => (
                <Card key={item.uid} className="border-gray-200 hover:border-violet-300 transition-colors cursor-pointer" draggable={WRITABLE_TYPES.has(item.type)} onDragStart={(event) => event.dataTransfer.setData('text/plain', item.uid)} onClick={() => onOpenItem(item)} data-testid={`kanban-card-${item.uid}`}>
                  <CardContent className="p-3">
                    <p className="text-sm font-medium text-gray-900">{item.title}</p>
                    <p className="text-xs text-gray-500 mt-1">{item.customer_name || item.source_label || item.type}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-gray-500">
                      {item.priority && <span>{item.priority}</span>}
                      {item.due_datetime && <span>Due {new Date(item.due_datetime).toLocaleDateString()}</span>}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};