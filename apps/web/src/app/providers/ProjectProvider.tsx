import React, { createContext, useContext, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../../lib/api';
import { useAuth } from './AuthProvider';

interface Project {
  project_id: string;
  name: string;
  description?: string;
  role?: string;
}

interface ProjectContextType {
  activeProject: Project | null;
  setActiveProject: (project: Project) => void;
  projects: Project[];
  isLoading: boolean;
  error: Error | null;
  createProject: (name: string, description?: string) => Promise<void>;
  isCreating: boolean;
}

const ProjectContext = createContext<ProjectContextType>({
  activeProject: null,
  setActiveProject: () => {},
  projects: [],
  isLoading: false,
  error: null,
  createProject: async () => {},
  isCreating: false,
});



import { useMatch, useNavigate } from 'react-router-dom';

export const ProjectProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const match = useMatch('/projects/:projectId/*');
  const urlProjectId = match?.params.projectId;

  const { data: fetchedProjects, isLoading, error } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: async () => {
      return await apiFetch('/v1/projects');
    },
    enabled: !!user,
  });

  const projects = fetchedProjects || [];
  
  // Find active project from URL, or fallback to first project if URL doesn't have one
  const activeProject = projects.find(p => p.project_id === urlProjectId) || null;

  useEffect(() => {
    // If we have projects but no valid active project in URL, redirect to the first project.
    // This handles both the `/` root case and invalid project IDs.
    if (!isLoading && projects.length > 0 && (!urlProjectId || !activeProject)) {
      navigate(`/projects/${projects[0].project_id}`, { replace: true });
    }
  }, [isLoading, projects, urlProjectId, activeProject, navigate]);

  const createMutation = useMutation({
    mutationFn: async ({ name, description }: { name: string; description?: string }) => {
      return apiFetch('/v1/projects', {
        method: 'POST',
        body: JSON.stringify({ name, description }),
      });
    },
    onSuccess: (newProject: Project) => {
      queryClient.setQueryData<Project[]>(['projects'], (old = []) => [...old, newProject]);
      navigate(`/projects/${newProject.project_id}`);
    },
  });

  const createProject = async (name: string, description?: string) => {
    await createMutation.mutateAsync({ name, description });
  };

  const setActiveProject = (project: Project) => {
    navigate(`/projects/${project.project_id}`);
  };

  return (
    <ProjectContext.Provider
      value={{
        activeProject,
        setActiveProject,
        projects,
        isLoading,
        error: error as Error | null,
        createProject,
        isCreating: createMutation.isPending,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};

export const useProject = () => useContext(ProjectContext);
