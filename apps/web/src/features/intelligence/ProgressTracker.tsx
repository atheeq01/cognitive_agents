import React from 'react';
import { motion } from 'framer-motion';

interface ProgressTrackerProps {
  stageName: string;
  progress: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
}

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({ stageName, progress, status }) => {
  return (
    <div className="w-full max-w-3xl mx-auto my-8 p-8 bg-card border rounded-2xl shadow-sm">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-foreground">
          {status === 'completed' ? 'Processing Complete' : status === 'failed' ? 'Processing Failed' : 'AI Analysis in Progress'}
        </h3>
        <span className="text-lg font-bold text-primary">{progress}%</span>
      </div>
      
      <div className="w-full h-4 bg-secondary rounded-full overflow-hidden shadow-inner">
        <motion.div
          className={`h-full ${status === 'failed' ? 'bg-destructive' : status === 'completed' ? 'bg-green-500' : 'bg-primary'}`}
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />
      </div>
      
      <div className="mt-6 text-center">
        <p className={`text-base font-medium ${status === 'failed' ? 'text-destructive' : status === 'completed' ? 'text-green-600 dark:text-green-400' : 'text-muted-foreground animate-pulse'}`}>
          {stageName || 'Initializing pipeline...'}
        </p>
      </div>
    </div>
  );
};
