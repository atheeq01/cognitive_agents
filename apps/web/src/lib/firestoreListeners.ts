import { collection, query, onSnapshot } from 'firebase/firestore';
import { db } from './firebase';

export interface JobStatus {
  id: string;
  projectId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  documentName: string;
  progress: number;
}

export const subscribeToProjectJobs = (projectId: string, callback: (jobs: JobStatus[]) => void) => {
  if (import.meta.env.DEV && !import.meta.env.VITE_FIREBASE_PROJECT_ID) {
    // Mock listener
    setTimeout(() => {
      callback([
        { id: 'job-1', projectId, status: 'processing', documentName: 'Q3_Earnings.pdf', progress: 45 },
        { id: 'job-2', projectId, status: 'completed', documentName: 'Employee_Handbook.docx', progress: 100 },
      ]);
    }, 1000);
    return () => {};
  }

  const q = query(collection(db, `projects/${projectId}/jobs`));
  const unsubscribe = onSnapshot(q, (querySnapshot) => {
    const jobs: JobStatus[] = [];
    querySnapshot.forEach((doc) => {
      jobs.push({ id: doc.id, ...doc.data() } as JobStatus);
    });
    callback(jobs);
  });

  return unsubscribe;
};
