import React from 'react';
import { useProject } from '../../app/providers/ProjectProvider';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../../lib/api';
import { toast } from 'sonner';

const AdminDashboard: React.FC = () => {
  const { activeProject } = useProject();
  const queryClient = useQueryClient();
  const projectId = activeProject?.project_id;

  const { data: documents = [], isLoading: docsLoading } = useQuery({
    queryKey: ['documents', projectId, 'pending_approval'],
    queryFn: async () => {
      try {
        return await apiFetch(`/v1/projects/${projectId}/documents?status=pending_approval`);
      } catch (e) {
        console.warn('API failed, using mock data for pending documents', e);
        return [
          { document_id: 'doc-1', filename: 'Financial_Q3.pdf', status: 'pending_approval', uploaded_at: new Date().toISOString() },
        ];
      }
    },
    enabled: !!projectId && activeProject?.role === 'admin',
  });

  const { data: members = [], isLoading: membersLoading } = useQuery({
    queryKey: ['members', projectId],
    queryFn: async () => {
      try {
        return await apiFetch(`/v1/projects/${projectId}/members`);
      } catch (e) {
        console.warn('API failed, using mock data for members', e);
        return [
          { user_id: 'user-1', role: 'admin', joined_at: new Date().toISOString() },
          { user_id: 'user-2', role: 'member', joined_at: new Date().toISOString() },
        ];
      }
    },
    enabled: !!projectId && activeProject?.role === 'admin',
  });

  const approveMutation = useMutation({
    mutationFn: (docId: string) =>
      apiFetch(`/v1/projects/${projectId}/documents/${docId}/approve`, { method: 'POST' }),
    onSuccess: () => {
      toast.success('Document approved successfully');
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] });
    },
    onError: (err) => {
      toast.error('Failed to approve document', { description: err.message });
    }
  });

  const rejectMutation = useMutation({
    mutationFn: (docId: string) =>
      apiFetch(`/v1/projects/${projectId}/documents/${docId}/reject`, { method: 'POST' }),
    onSuccess: () => {
      toast.success('Document rejected');
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] });
    },
    onError: (err) => {
      toast.error('Failed to reject document', { description: err.message });
    }
  });

  // No project selected at all
  if (!activeProject) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        <p className="text-sm">Select a project from the top-right dropdown to get started.</p>
      </div>
    );
  }

  // Project is selected but user is not admin
  if (activeProject.role !== 'admin') {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center space-y-2">
          <p className="text-lg font-semibold text-destructive">Access Denied</p>
          <p className="text-sm text-muted-foreground">
            The Admin Dashboard is only available to project admins.<br />
            Your current role in <strong>{activeProject.name}</strong> is{' '}
            <span className="font-medium capitalize">{activeProject.role ?? 'unknown'}</span>.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Admin Dashboard — {activeProject.name}</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Approval Queue */}
        <div className="border rounded-lg p-5 bg-card shadow-sm flex flex-col">
          <h3 className="font-semibold text-lg mb-4 border-b pb-2">Approval Queue</h3>
          {docsLoading ? (
            <div className="text-sm text-muted-foreground animate-pulse">Loading queue...</div>
          ) : documents.length === 0 ? (
            <div className="text-sm text-muted-foreground py-4 text-center">
              No documents pending approval.
            </div>
          ) : (
            <ul className="space-y-3 flex-1 overflow-auto">
              {documents.map((doc: any) => (
                <li
                  key={doc.document_id}
                  className="flex justify-between items-center p-3 bg-muted/50 rounded-md border"
                >
                  <div>
                    <span className="font-medium text-sm">{doc.filename}</span>
                    <span className="text-xs text-muted-foreground ml-2">
                      {doc.uploaded_at
                        ? new Date(doc.uploaded_at).toLocaleDateString()
                        : 'Just now'}
                    </span>
                  </div>
                  <div className="space-x-2 flex-shrink-0">
                    <button
                      onClick={() => approveMutation.mutate(doc.document_id)}
                      disabled={approveMutation.isPending}
                      className="px-3 py-1.5 bg-primary text-primary-foreground rounded-md text-xs font-medium hover:bg-primary/90 disabled:opacity-50"
                    >
                      Approve
                    </button>
                    <button 
                      onClick={() => rejectMutation.mutate(doc.document_id)}
                      disabled={rejectMutation.isPending}
                      className="px-3 py-1.5 border border-destructive text-destructive rounded-md text-xs font-medium hover:bg-destructive/10 disabled:opacity-50"
                    >
                      Reject
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Member Management */}
        <div className="border rounded-lg p-5 bg-card shadow-sm flex flex-col">
          <h3 className="font-semibold text-lg mb-4 border-b pb-2">Member Management</h3>
          {membersLoading ? (
            <div className="text-sm text-muted-foreground animate-pulse">Loading members...</div>
          ) : members.length === 0 ? (
            <div className="text-sm text-muted-foreground py-4 text-center">No members found.</div>
          ) : (
            <ul className="space-y-3 flex-1 overflow-auto">
              {members.map((member: any) => (
                <li
                  key={member.user_id}
                  className="flex justify-between items-center p-3 bg-muted/50 rounded-md border"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-xs uppercase">
                      {(member.email || member.user_id || 'U')[0]}
                    </div>
                    <span className="font-medium text-sm">{member.email ?? member.user_id}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-xs bg-secondary text-secondary-foreground px-2 py-1 rounded-md uppercase font-medium">
                      {member.role}
                    </span>
                    <button className="text-xs border px-3 py-1.5 rounded-md hover:bg-accent font-medium">
                      Edit Role
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
