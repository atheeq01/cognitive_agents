import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDocumentIntelligence } from './useDocumentIntelligence';
import { ProgressTracker } from './ProgressTracker';
import { ResultsPanel } from './ResultsPanel';
import { ArrowLeft, Loader2 } from 'lucide-react';

interface DashboardProps {
  documentId: string;
  onBack: () => void;
}

export const DocumentIntelligenceDashboard: React.FC<DashboardProps> = ({ documentId, onBack }) => {
  const { data, error } = useDocumentIntelligence(documentId);

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6">
      <div className="flex items-center space-x-4 mb-8">
        <button 
          onClick={onBack}
          className="p-2 hover:bg-secondary rounded-full transition-colors text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Real-Time Intelligence</h2>
          <p className="text-muted-foreground text-sm">
            {data?.documentName || 'Analyzing Document...'}
          </p>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {!data && !error ? (
          <motion.div 
            key="loading"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center py-20 text-muted-foreground space-y-4"
          >
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p>Initializing AI Pipeline...</p>
          </motion.div>
        ) : error ? (
          <motion.div 
            key="error"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="p-6 bg-destructive/10 text-destructive border border-destructive/20 rounded-xl"
          >
            <p className="font-semibold">Error connecting to pipeline</p>
            <p className="text-sm opacity-90">{error}</p>
          </motion.div>
        ) : data && (
          <motion.div 
            key="tracking"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="w-full"
          >
            <ProgressTracker 
              stageName={data.stage_name} 
              progress={data.progress} 
              status={data.status} 
            />

            {data.status === 'completed' && data.results && (
              <motion.div
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                <ResultsPanel results={data.results} />
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
