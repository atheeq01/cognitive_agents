import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../../lib/api';
import { useProject } from '../../app/providers/ProjectProvider';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, File as FileIcon, Clock, CheckCircle, AlertCircle, Loader2, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

interface Document {
  document_id: string;
  filename: string;
  status: string;
  uploaded_at: string;
  mime_type: string;
  size_bytes: number;
}

interface DocumentsListProps {
  onSelectDocument?: (id: string) => void;
}

export const DocumentsList: React.FC<DocumentsListProps> = ({ onSelectDocument }) => {
  const { activeProject } = useProject();
  const projectId = activeProject?.project_id;
  const queryClient = useQueryClient();
  const [documentToDelete, setDocumentToDelete] = useState<string | null>(null);

  const deleteMutation = useMutation({
    mutationFn: async (documentId: string) => {
      await apiFetch(`/v1/projects/${projectId}/documents/${documentId}`, {
        method: 'DELETE',
      });
    },
    onSuccess: () => {
      toast.success('Document deleted successfully');
      void queryClient.invalidateQueries({ queryKey: ['documents', projectId] });
      void queryClient.invalidateQueries({ queryKey: ['project_report', projectId] });
    },
    onError: (err: Error) => {
      toast.error('Failed to delete document', { description: err.message });
    }
  });

  const { data: documents = [], isLoading } = useQuery<Document[]>({
    queryKey: ['documents', projectId],
    queryFn: async () => {
      // Fetch all documents without a status filter
      return await apiFetch(`/v1/projects/${projectId}/documents`);
    },
    enabled: !!projectId,
    refetchInterval: 5000, // Poll every 5 seconds to update statuses
  });

  if (!activeProject) return null;

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-48 space-y-4">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
        <p className="text-sm text-muted-foreground">Loading documents...</p>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col items-center justify-center p-12 text-center border rounded-xl bg-card border-dashed"
      >
        <div className="p-4 bg-muted/50 rounded-full mb-4">
          <FileText className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium text-foreground mb-1">No documents yet</h3>
        <p className="text-sm text-muted-foreground max-w-[300px]">
          Upload your first document above to start building the knowledge base for this project.
        </p>
      </motion.div>
    );
  }

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'ready':
        return { color: 'text-green-500', bg: 'bg-green-500/10', icon: CheckCircle, label: 'Ready' };
      case 'processing':
        return { color: 'text-blue-500', bg: 'bg-blue-500/10', icon: Loader2, label: 'Processing', animate: 'animate-spin' };
      case 'pending_approval':
        return { color: 'text-amber-500', bg: 'bg-amber-500/10', icon: Clock, label: 'Pending' };
      case 'failed':
        return { color: 'text-destructive', bg: 'bg-destructive/10', icon: AlertCircle, label: 'Failed' };
      default:
        return { color: 'text-muted-foreground', bg: 'bg-muted', icon: FileIcon, label: status };
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-end mb-4">
        <div>
          <h3 className="text-lg font-semibold">Project Documents</h3>
          <p className="text-sm text-muted-foreground">All uploaded files for {activeProject.name}</p>
        </div>
        <span className="text-xs font-medium px-2 py-1 bg-secondary rounded-full">
          {documents.length} File{documents.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {documents.map((doc, i) => {
          const statusConfig = getStatusConfig(doc.status);
          const StatusIcon = statusConfig.icon;
          
          return (
            <motion.div
              key={doc.document_id}
              onClick={() => onSelectDocument?.(doc.document_id)}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
              className={`group flex flex-col p-4 border rounded-xl bg-card shadow-sm hover:shadow-md transition-shadow ${onSelectDocument ? 'cursor-pointer hover:border-primary/50' : ''}`}
            >
              <div className="flex justify-between items-start mb-3">
                <div className={`p-2 rounded-lg ${statusConfig.bg} ${statusConfig.color}`}>
                  <FileText className="w-5 h-5" />
                </div>
                <div className="flex items-center gap-2">
                  <div className={`flex items-center space-x-1.5 px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bg} ${statusConfig.color}`}>
                    <StatusIcon className={`w-3.5 h-3.5 ${statusConfig.animate || ''}`} />
                    <span>{statusConfig.label}</span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setDocumentToDelete(doc.document_id);
                    }}
                    disabled={deleteMutation.isPending}
                    className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-md transition-colors"
                    title="Delete document"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              
              <h4 className="font-medium text-sm break-words mb-2 leading-tight" title={doc.filename}>
                {doc.filename}
              </h4>
              
              <div className="flex justify-between text-xs text-muted-foreground mt-auto pt-2 border-t">
                <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                <span>{formatSize(doc.size_bytes)}</span>
              </div>
            </motion.div>
          );
        })}
      </div>

      <AnimatePresence>
        {documentToDelete && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-background/80 backdrop-blur-sm"
              onClick={() => setDocumentToDelete(null)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-card border shadow-2xl rounded-2xl p-6 w-full max-w-md"
            >
              <div className="flex flex-col items-center text-center space-y-4">
                <div className="p-4 bg-destructive/10 text-destructive rounded-full">
                  <AlertCircle className="w-8 h-8" />
                </div>
                <div>
                  <h2 className="text-xl font-bold">Delete Document?</h2>
                  <p className="text-sm text-muted-foreground mt-2">
                    This action cannot be undone. This will permanently delete the document from the knowledge base.
                  </p>
                </div>
                <div className="flex gap-3 w-full pt-4 mt-4 border-t border-border/50">
                  <button
                    onClick={() => setDocumentToDelete(null)}
                    disabled={deleteMutation.isPending}
                    className="flex-1 px-4 py-2.5 bg-secondary text-secondary-foreground rounded-xl font-medium hover:bg-secondary/80 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      deleteMutation.mutate(documentToDelete, {
                        onSuccess: () => setDocumentToDelete(null)
                      });
                    }}
                    disabled={deleteMutation.isPending}
                    className="flex-1 px-4 py-2.5 bg-destructive text-destructive-foreground rounded-xl font-medium hover:bg-destructive/90 transition-colors flex justify-center items-center"
                  >
                    {deleteMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Yes, Delete'}
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
