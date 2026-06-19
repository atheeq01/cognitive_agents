import React, { useState, useEffect } from 'react';
import { useJobStatus } from './useJobStatus';
import { type JobStatus } from '../../lib/firestoreListeners';

export const UploadQueueWidget: React.FC = () => {
  const { jobs } = useJobStatus();
  const [isMinimized, setIsMinimized] = useState(false);
  const [completionTimes, setCompletionTimes] = useState<Record<string, number>>({});
  const [currentTime, setCurrentTime] = useState(Date.now());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    setCompletionTimes(prev => {
      const newTimes = { ...prev };
      let updated = false;
      jobs.forEach(j => {
        if ((j.status === 'completed' || j.status === 'failed') && !newTimes[j.id]) {
          newTimes[j.id] = Date.now();
          updated = true;
        }
      });
      return updated ? newTimes : prev;
    });
  }, [jobs]);

  const visibleJobs = jobs.filter(j => {
    if (j.status === 'completed' || j.status === 'failed') {
      const completedAt = completionTimes[j.id];
      if (completedAt && currentTime - completedAt > 3000) {
        return false;
      }
    }
    return true;
  });

  // Only show the widget if there are active or recently completed jobs
  const activeJobs = visibleJobs.filter(j => j.status !== 'completed' && j.status !== 'failed');
  const recentJobs = visibleJobs.slice(0, 3); // Just show top 3 to prevent huge lists

  if (visibleJobs.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 w-80 bg-card text-card-foreground border rounded-lg shadow-xl overflow-hidden flex flex-col">
      <div 
        className="px-4 py-3 bg-secondary text-secondary-foreground flex justify-between items-center cursor-pointer border-b"
        onClick={() => setIsMinimized(!isMinimized)}
      >
        <div className="font-semibold text-sm flex items-center space-x-2">
          {activeJobs.length > 0 ? (
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
          ) : (
             <span className="h-2 w-2 rounded-full bg-muted-foreground"></span>
          )}
          <span>Upload Queue ({activeJobs.length} active)</span>
        </div>
        <button className="text-muted-foreground hover:text-foreground">
          <svg className={`w-4 h-4 transform transition-transform ${isMinimized ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
        </button>
      </div>
      
      {!isMinimized && (
        <div className="max-h-64 overflow-y-auto p-2 bg-card">
          <ul className="space-y-2">
            {recentJobs.map((job: JobStatus) => (
              <li key={job.id} className="p-3 bg-muted/30 border rounded-md text-sm flex flex-col space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-medium truncate mr-2" title={job.documentName}>{job.documentName}</span>
                  <span className="text-xs uppercase bg-background px-1.5 py-0.5 rounded border">
                    {job.status}
                  </span>
                </div>
                {job.status === 'processing' && (
                  <div className="w-full bg-secondary rounded-full h-1.5 overflow-hidden">
                    <div 
                      className="bg-primary h-1.5 transition-all duration-300 ease-out" 
                      style={{ width: `${job.progress}%` }}
                    ></div>
                  </div>
                )}
              </li>
            ))}
            {visibleJobs.length > 3 && (
              <li className="text-xs text-center text-muted-foreground pt-1">
                + {visibleJobs.length - 3} more jobs
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
};
