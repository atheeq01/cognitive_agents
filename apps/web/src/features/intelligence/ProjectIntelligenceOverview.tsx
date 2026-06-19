import React from 'react';
import { motion } from 'framer-motion';
import { useProjectIntelligence } from './useProjectIntelligence';
import { Brain, Loader2, AlertCircle } from 'lucide-react';
import { ResultsPanel } from './ResultsPanel';

export const ProjectIntelligenceOverview: React.FC = () => {
  const { jobs, isLoading, error } = useProjectIntelligence();

  const completedJobs = jobs.filter(j => j.status === 'completed' && j.results);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-20 text-muted-foreground space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p>Loading Intelligence Data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-destructive/10 border border-destructive/20 rounded-xl flex items-start space-x-3 text-destructive">
        <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold">Failed to load intelligence data</p>
          <p className="text-sm opacity-90">{error}</p>
        </div>
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="p-12 text-center bg-card border rounded-2xl">
        <Brain className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
        <h3 className="text-lg font-medium">No Analysis Available</h3>
        <p className="text-muted-foreground mt-2 max-w-sm mx-auto">
          Upload documents to the project to start building the intelligence dashboard.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Per Document Analysis */}
      <h3 className="text-xl font-bold pt-4">Document Insights</h3>
      <div className="grid gap-8">
        {completedJobs.map(job => (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            key={job.id} 
            className="border rounded-2xl overflow-hidden bg-card"
          >
            <div className="bg-secondary px-6 py-4 border-b flex justify-between items-center">
              <h4 className="font-bold text-lg">{job.documentName || job.id}</h4>
              {job.results?.cognitive_insights?.intent && (
                <span className="text-xs font-medium px-2.5 py-1 bg-background rounded-full border text-muted-foreground truncate max-w-[200px]">
                  {job.results.cognitive_insights.intent}
                </span>
              )}
            </div>
            <div className="p-0 border-t-0 border-x-0 border-b-0">
              <ResultsPanel results={job.results!} />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};


