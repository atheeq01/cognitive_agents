import React, { useState } from 'react';
import { useProject } from '../../app/providers/ProjectProvider';

export const ProjectSwitcher: React.FC = () => {
  const { activeProject, setActiveProject, projects, isLoading, createProject, isCreating } = useProject();
  const [isOpen, setIsOpen] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    try {
      await createProject(newProjectName.trim(), newProjectDesc.trim() || undefined);
      setNewProjectName('');
      setNewProjectDesc('');
      setShowCreate(false);
      setIsOpen(false);
    } catch (err) {
      console.error('Failed to create project', err);
    }
  };

  if (isLoading) {
    return <div className="text-sm text-muted-foreground animate-pulse">Loading projects...</div>;
  }

  // No active project AND no projects at all → offer to create one
  if (!activeProject && projects.length === 0) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">No projects yet.</span>
        <button
          onClick={() => setShowCreate(true)}
          className="text-sm px-3 py-1.5 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          + New Project
        </button>
        {showCreate && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
            <div className="bg-card border rounded-xl shadow-2xl p-6 w-full max-w-md">
              <h2 className="text-lg font-bold mb-4">Create your first project</h2>
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1" htmlFor="proj-name">Project name</label>
                  <input
                    id="proj-name"
                    autoFocus
                    required
                    className="w-full px-3 py-2 border rounded-md bg-input text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="e.g. Legal Review 2025"
                    value={newProjectName}
                    onChange={e => setNewProjectName(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1" htmlFor="proj-desc">Description (optional)</label>
                  <input
                    id="proj-desc"
                    className="w-full px-3 py-2 border rounded-md bg-input text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="Short description..."
                    value={newProjectDesc}
                    onChange={e => setNewProjectDesc(e.target.value)}
                  />
                </div>
                <div className="flex gap-2 justify-end pt-2">
                  <button
                    type="button"
                    onClick={() => setShowCreate(false)}
                    className="px-4 py-2 text-sm rounded-md border hover:bg-muted transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isCreating || !newProjectName.trim()}
                    className="px-4 py-2 text-sm rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                  >
                    {isCreating ? 'Creating...' : 'Create Project'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    );
  }

  if (!activeProject) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 border px-3 py-1.5 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
      >
        <span className="font-medium">{activeProject.name}</span>
        {activeProject.role && (
          <span className="text-xs px-1.5 py-0.5 rounded bg-primary/10 text-primary uppercase">
            {activeProject.role}
          </span>
        )}
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-1 w-64 bg-popover text-popover-foreground border rounded-md shadow-lg overflow-hidden z-50">
          <div className="px-3 py-2 text-xs text-muted-foreground bg-muted/50 border-b">Select Project</div>
          <ul className="py-1 max-h-60 overflow-auto">
            {projects.map(p => (
              <li key={p.project_id}>
                <button
                  className={`w-full text-left px-4 py-2 hover:bg-accent hover:text-accent-foreground ${
                    p.project_id === activeProject.project_id ? 'bg-accent/50' : ''
                  }`}
                  onClick={() => { setActiveProject(p); setIsOpen(false); }}
                >
                  <div className="flex justify-between items-center">
                    <span>{p.name}</span>
                    {p.project_id === activeProject.project_id && (
                      <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                </button>
              </li>
            ))}
          </ul>
          <div className="border-t p-2 space-y-1 bg-muted/30">
            <button
              onClick={() => { setShowCreate(true); setIsOpen(false); }}
              className="w-full text-left px-2 py-1.5 text-sm text-primary hover:bg-primary/10 rounded transition-colors"
            >
              + New Project
            </button>
          </div>
        </div>
      )}

      {/* Create Project Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="bg-card border rounded-xl shadow-2xl p-6 w-full max-w-md">
            <h2 className="text-lg font-bold mb-4">Create New Project</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1" htmlFor="proj-name2">Project name</label>
                <input
                  id="proj-name2"
                  autoFocus
                  required
                  className="w-full px-3 py-2 border rounded-md bg-input text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="e.g. Legal Review 2025"
                  value={newProjectName}
                  onChange={e => setNewProjectName(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1" htmlFor="proj-desc2">Description (optional)</label>
                <input
                  id="proj-desc2"
                  className="w-full px-3 py-2 border rounded-md bg-input text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Short description..."
                  value={newProjectDesc}
                  onChange={e => setNewProjectDesc(e.target.value)}
                />
              </div>
              <div className="flex gap-2 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 text-sm rounded-md border hover:bg-muted transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreating || !newProjectName.trim()}
                  className="px-4 py-2 text-sm rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  {isCreating ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
