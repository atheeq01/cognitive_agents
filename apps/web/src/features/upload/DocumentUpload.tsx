import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, File, CheckCircle, AlertCircle } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useProject } from '../../app/providers/ProjectProvider';
import { toast } from 'sonner';

interface DocumentUploadProps {
  onUploadComplete?: (documentId: string) => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUploadComplete }) => {
  const { activeProject } = useProject();
  const queryClient = useQueryClient();
  const projectId = activeProject?.project_id;

  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      
      const { apiFetch } = await import('../../lib/api');
      const response = await apiFetch(`/v1/projects/${projectId}/documents`, {
        method: 'POST',
        body: formData,
      });

      return response;
    },
    onSuccess: (data) => {
      toast.success('Document uploaded successfully!');
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] });
      setTimeout(() => setSelectedFile(null), 2000); // Clear after 2 seconds showing success
      if (onUploadComplete && data?.document_id) {
        onUploadComplete(data.document_id);
      }
    },
    onError: (err) => {
      toast.error('Upload Failed', { description: err.message });
      setSelectedFile(null); // Reset on error to try again
    }
  });

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (file: File) => {
    // Validate file type
    const allowedTypes = [
      'application/pdf', 
      'text/plain', 
      'audio/mpeg', 
      'image/jpeg', 
      'image/png', 
      'audio/mp3',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/csv',
      'application/zip' // Sometimes magic libraries detect office docs as zip
    ];
    const allowedExtensions = ['pdf', 'txt', 'mp3', 'jpg', 'jpeg', 'png', 'docx', 'pptx', 'xlsx', 'csv'];
    const extension = file.name.split('.').pop()?.toLowerCase() || '';
    
    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(extension)) {
      toast.error('Unsupported file type. Please upload a PDF, TXT, MP3, JPG, PNG, DOCX, PPTX, XLSX, or CSV.');
      return;
    }
    
    // Validate size (50MB)
    if (file.size > 50 * 1024 * 1024) {
      toast.error('File too large. Maximum size is 50MB.');
      return;
    }

    setSelectedFile(file);
    uploadMutation.mutate(file);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelect(e.target.files[0]);
    }
    // Reset so the same file can be selected again
    e.target.value = '';
  };

  return (
    <div className="w-full">
      <motion.div
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        className={`relative overflow-hidden border-2 border-dashed rounded-2xl p-8 text-center transition-colors cursor-pointer
          ${isDragging ? 'border-primary bg-primary/10' : 'border-muted-foreground/30 bg-card hover:bg-muted/30 hover:border-primary/50'}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !selectedFile && !uploadMutation.isPending && fileInputRef.current?.click()}
      >
        <input 
          type="file" 
          className="hidden" 
          ref={fileInputRef} 
          onChange={handleFileInputChange}
          accept=".pdf,.txt,.mp3,.jpg,.jpeg,.png,.docx,.pptx,.xlsx,.csv"
        />

        <AnimatePresence mode="wait">
          {!selectedFile ? (
            <motion.div
              key="idle"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex flex-col items-center justify-center space-y-4 pointer-events-none"
            >
              <div className="p-4 bg-primary/10 text-primary rounded-full">
                <UploadCloud size={40} className={isDragging ? 'animate-bounce' : ''} />
              </div>
              <div>
                <p className="text-lg font-semibold text-foreground">Click or drag a file to upload</p>
                <p className="text-sm text-muted-foreground mt-1">PDF, TXT, Documents, Images, or Audio up to 50MB</p>
              </div>
            </motion.div>
          ) : uploadMutation.isPending ? (
            <motion.div
              key="uploading"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.1 }}
              className="flex flex-col items-center justify-center space-y-4"
            >
              <div className="p-4 bg-primary text-primary-foreground rounded-full relative">
                <div className="absolute inset-0 border-4 border-primary/30 border-t-primary-foreground rounded-full animate-spin"></div>
                <File size={32} />
              </div>
              <div className="text-center">
                <p className="text-lg font-semibold text-foreground animate-pulse">Uploading...</p>
                <p className="text-sm text-muted-foreground mt-1 break-words max-w-[300px] px-4">{selectedFile.name}</p>
              </div>
            </motion.div>
          ) : uploadMutation.isSuccess ? (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.5 }}
              className="flex flex-col items-center justify-center space-y-4"
            >
              <motion.div 
                initial={{ rotate: -90, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                transition={{ type: "spring", stiffness: 200, damping: 10 }}
                className="text-green-500"
              >
                <CheckCircle size={64} />
              </motion.div>
              <div>
                <p className="text-lg font-semibold text-foreground">Upload Complete</p>
                <p className="text-sm text-muted-foreground mt-1">File has been queued for processing.</p>
              </div>
            </motion.div>
          ) : uploadMutation.isError ? (
            <motion.div
              key="error"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="flex flex-col items-center justify-center space-y-4"
            >
              <div className="text-destructive">
                <AlertCircle size={64} />
              </div>
              <div>
                <p className="text-lg font-semibold text-foreground">Upload Failed</p>
                <p className="text-sm text-muted-foreground mt-1">Click to try again</p>
              </div>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};
