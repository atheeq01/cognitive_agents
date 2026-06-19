import React, { useState } from 'react';
import { FileText, Headphones, Video, Image as ImageIcon } from 'lucide-react';
import { SourceViewer } from './SourceViewer';

interface SourceLocation {
  document_id: string;
  document_name: string;
  modality: 'pdf' | 'docx' | 'audio' | 'video' | 'image';
  page_number?: number;
  line_number?: number;
  timestamp_start_seconds?: number;
  timestamp_end_seconds?: number;
  speaker_id?: string;
  bounding_box?: number[];
  exact_quote: string;
}

export const CitationChip: React.FC<{ source: SourceLocation }> = ({ source }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!source) return null;

  const getIcon = () => {
    switch (source.modality) {
      case 'pdf':
      case 'docx':
        return <FileText className="w-3.5 h-3.5" />;
      case 'audio':
        return <Headphones className="w-3.5 h-3.5" />;
      case 'video':
        return <Video className="w-3.5 h-3.5" />;
      case 'image':
        return <ImageIcon className="w-3.5 h-3.5" />;
      default:
        return <FileText className="w-3.5 h-3.5" />;
    }
  };

  const getLabel = () => {
    let label = source.document_name || 'PDF';
    if (source.page_number) label += ` - Page ${source.page_number}`;
    if (source.timestamp_start_seconds !== undefined) {
      const mins = Math.floor(source.timestamp_start_seconds / 60);
      const secs = Math.floor(source.timestamp_start_seconds % 60);
      label += `, ${mins}:${secs.toString().padStart(2, '0')}`;
    }
    return label;
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center gap-1.5 px-2 py-1 bg-secondary hover:bg-secondary/80 text-secondary-foreground text-xs font-medium rounded-md transition-colors border border-border/50"
      >
        {getIcon()}
        <span className="truncate max-w-[150px]">{getLabel()}</span>
      </button>

      {isOpen && (
        <SourceViewer source={source} onClose={() => setIsOpen(false)} />
      )}
    </>
  );
};
