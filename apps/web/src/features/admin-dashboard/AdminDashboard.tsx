import React, { useState } from 'react';
import { useProject } from '../../app/providers/ProjectProvider';
import { DocumentUpload } from '../upload/DocumentUpload';
import { DocumentsList } from '../documents/DocumentsList';
import { ProjectIntelligenceOverview } from '../intelligence/ProjectIntelligenceOverview';

const AdminDashboard: React.FC = () => {
  const { activeProject } = useProject();
  const role = activeProject?.role;
  const isAdmin = role === 'admin';
  const canApprove = role === 'admin' || role === 'member';
  const canUpload = role === 'admin' || role === 'member';

  const projectId = activeProject?.project_id;
  const [activeTab, setActiveTab] = useState<'overview' | 'intelligence'>('overview');



  // No project selected at all
  if (!activeProject) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        <p className="text-sm">Select a project from the top-right dropdown to get started.</p>
      </div>
    );
  }



  return (
    <div className="space-y-8 max-w-7xl mx-auto pt-2">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-end border-b border-border/50 pb-5 mb-8 gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Documents</h2>
          <p className="text-muted-foreground mt-1.5">Manage and analyze your project's knowledge base.</p>
        </div>
        
        <div className="flex space-x-1.5 bg-muted/60 p-1.5 rounded-xl border border-border/50">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-5 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
              activeTab === 'overview' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
            }`}
          >
            Library
          </button>
          <button
            onClick={() => setActiveTab('intelligence')}
            className={`px-5 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
              activeTab === 'intelligence' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
            }`}
          >
            Intelligence
          </button>
        </div>
      </div>
      
      {activeTab === 'intelligence' ? (
        <div className="mt-8">
          <ProjectIntelligenceOverview />
        </div>
      ) : (
        <>
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {canUpload && (
            <div className="lg:col-span-1">
              <div className="sticky top-6 space-y-4">
                <h3 className="text-lg font-semibold tracking-tight">Upload Files</h3>
                <div className="bg-card rounded-[1.5rem] border border-border/60 shadow-sm p-5 hover:border-primary/20 transition-colors">
                  <DocumentUpload onUploadComplete={() => setActiveTab('intelligence')} />
                </div>
              </div>
            </div>
          )}
          <div className={canUpload ? "lg:col-span-3" : "lg:col-span-4"}>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold tracking-tight">All Documents</h3>
              <div className="bg-card rounded-[1.5rem] border border-border/60 shadow-sm p-2">
                <DocumentsList onSelectDocument={() => setActiveTab('intelligence')} />
              </div>
            </div>
          </div>
        </div>
        </>
      )}
    </div>
  );
};

export default AdminDashboard;
