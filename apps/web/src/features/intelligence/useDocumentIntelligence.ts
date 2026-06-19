import { useEffect, useState } from 'react';
import { doc, onSnapshot } from 'firebase/firestore';
import { db } from '../../lib/firebase';
import { useProject } from '../../app/providers/ProjectProvider';

export interface DocumentIntelligenceResults {
  summary: string;
  cognitive_insights: any;
  similarities: any[];
  contradictions: any[];
  markdown_report: string;
}

export interface DocumentIntelligenceStatus {
  id: string;
  projectId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  stage_name: string;
  progress: number;
  documentName?: string;
  results?: DocumentIntelligenceResults;
}

export const useDocumentIntelligence = (documentId: string | null) => {
  const { activeProject } = useProject();
  const [data, setData] = useState<DocumentIntelligenceStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!activeProject || !documentId) return;

    const projectId = activeProject.project_id;
    if (!projectId) return;



    const docRef = doc(db, `projects/${projectId}/jobs`, documentId);
    
    const unsubscribe = onSnapshot(docRef, (docSnap) => {
      if (docSnap.exists()) {
        setData({ id: docSnap.id, ...docSnap.data() } as DocumentIntelligenceStatus);
        setError(null);
      } else {
        // Document might not exist immediately after upload
        setError('Waiting for background job to initialize...');
      }
    }, (err) => {
      setError(err.message);
    });

    return () => unsubscribe();
  }, [activeProject, documentId]);

  return { data, error };
};
