import { FileSearch } from 'lucide-react';
import Button from './Button';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export default function EmptyState({
  title = '暂无数据',
  description = '当前还没有相关内容，请先进行其他操作。',
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-8 text-center">
      <div className="w-16 h-16 rounded-full bg-beige-200 flex items-center justify-center mb-6">
        <FileSearch size={28} className="text-beige-500" />
      </div>
      <h3 className="font-serif text-xl font-normal text-brand-900 mb-2">{title}</h3>
      <p className="font-sans text-sm font-light text-beige-600 max-w-sm mb-6">{description}</p>
      {actionLabel && onAction && (
        <Button variant="primary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
