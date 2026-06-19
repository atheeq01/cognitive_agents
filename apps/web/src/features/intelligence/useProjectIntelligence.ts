import { useEffect, useState } from 'react';
import { collection, query, onSnapshot } from 'firebase/firestore';
import { db } from '../../lib/firebase';
import { useProject } from '../../app/providers/ProjectProvider';
import { type DocumentIntelligenceStatus } from './useDocumentIntelligence';

export const useProjectIntelligence = () => {
  const { activeProject } = useProject();
  const [jobs, setJobs] = useState<DocumentIntelligenceStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!activeProject?.project_id) return;

    const projectId = activeProject.project_id;
    const q = query(
      collection(db, `projects/${projectId}/jobs`)
    );

    const unsubscribe = onSnapshot(
      q,
      (querySnapshot) => {
        const fetchedJobs: DocumentIntelligenceStatus[] = [];
        querySnapshot.forEach((doc) => {
          fetchedJobs.push({ id: doc.id, ...doc.data() } as DocumentIntelligenceStatus);
        });
        // Sort newest first manually if orderBy is complex due to missing indexes
        // Usually, jobs might have a createdAt, but let's just reverse for now
        setJobs(fetchedJobs.reverse());
        setIsLoading(false);
        setError(null);
      },
      (err) => {
        console.error('Error fetching project intelligence:', err);
        setError(err.message);
        setIsLoading(false);
      }
    );

    return () => unsubscribe();
  }, [activeProject]);

  return { jobs, isLoading, error };
};
