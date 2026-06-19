import React, { useEffect, useState } from 'react';
import { X, ExternalLink, Loader2 } from 'lucide-react';

interface SourceLocation {
  document_id: string;
  document_name: string;
  modality: 'pdf' | 'docx' | 'audio' | 'video' | 'image';
  page_number?: number;
  timestamp_start_seconds?: number;
  exact_quote: string;
}

export const SourceViewer: React.FC<{ source: SourceLocation; onClose: () => void }> = ({ source, onClose }) => {
  // In a real implementation, this would fetch the actual file from a signed URL.
  // For the demo, we render a rich placeholder highlighting the concept.
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 800);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-background/80 backdrop-blur-sm">
      <div className="bg-card w-full max-w-4xl h-[80vh] flex flex-col rounded-2xl shadow-2xl overflow-hidden border border-border">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-muted/30">
          <div>
            <h3 className="font-semibold text-lg">{source.document_name}</h3>
            <p className="text-sm text-muted-foreground">
              {source.modality.toUpperCase()} 
              {source.page_number ? ` • Page ${source.page_number}` : ''}
              {source.timestamp_start_seconds !== undefined ? ` • Timestamp ${source.timestamp_start_seconds}s` : ''}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2 hover:bg-secondary rounded-lg transition-colors text-muted-foreground hover:text-foreground">
              <ExternalLink className="w-5 h-5" />
            </button>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-destructive/10 hover:text-destructive rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 bg-muted/10 relative overflow-hidden flex flex-col">
          {loading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground">
              <Loader2 className="w-8 h-8 animate-spin mb-4" />
              <p>Loading source document...</p>
            </div>
          ) : (
            <div className="flex-1 p-8 overflow-y-auto">
              <div className="max-w-2xl mx-auto bg-background rounded-lg shadow-sm border p-12 min-h-[600px] relative">
                {source.modality === 'pdf' || source.modality === 'docx' ? (
                  <div className="space-y-6 text-foreground/80">
                    <div className="w-3/4 h-4 bg-muted rounded"></div>
                    <div className="w-full h-4 bg-muted rounded"></div>
                    <div className="w-5/6 h-4 bg-muted rounded"></div>
                    
                    {/* Simulated highlighted quote */}
                    <div className="my-8 p-1 relative">
                      <div className="absolute -inset-1 bg-yellow-300/30 dark:bg-yellow-500/20 rounded"></div>
                      <p className="relative font-medium text-foreground leading-relaxed">
                        {source.exact_quote}
                      </p>
                    </div>

                    <div className="w-full h-4 bg-muted rounded"></div>
                    <div className="w-2/3 h-4 bg-muted rounded"></div>
                    <div className="w-full h-4 bg-muted rounded"></div>
                    <div className="w-4/5 h-4 bg-muted rounded"></div>
                  </div>
                ) : source.modality === 'audio' || source.modality === 'video' ? (
                  <div className="flex flex-col items-center justify-center h-full">
                    <div className="w-full aspect-video bg-black rounded-lg flex items-center justify-center overflow-hidden relative">
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-sm">
                          <div className="w-0 h-0 border-t-8 border-t-transparent border-l-[16px] border-l-white border-b-8 border-b-transparent ml-2"></div>
                        </div>
                      </div>
                    </div>
                    <div className="mt-8 p-4 bg-secondary rounded-lg w-full">
                      <p className="text-sm font-semibold text-muted-foreground mb-2">Transcript at {source.timestamp_start_seconds}s:</p>
                      <p className="font-medium text-lg text-foreground bg-yellow-300/30 dark:bg-yellow-500/20 inline-block">
                        "{source.exact_quote}"
                      </p>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
