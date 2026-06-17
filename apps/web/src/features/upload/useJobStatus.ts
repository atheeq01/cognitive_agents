import { useEffect, useState } from 'react';
import { type JobStatus, subscribeToProjectJobs } from '../../lib/firestoreListeners';
import { useProject } from '../../app/providers/ProjectProvider';

export const useJobStatus = () => {
  const { activeProject } = useProject();
  const [jobs, setJobs] = useState<JobStatus[]>([]);

  useEffect(() => {
    if (!activeProject) return;

    const projectId = activeProject.project_id;
    if (!projectId) return;
    
    const unsubscribe = subscribeToProjectJobs(projectId, (updatedJobs) => {
      setJobs(updatedJobs);
    });

    return () => unsubscribe();
  }, [activeProject]);

  return { jobs };
};
