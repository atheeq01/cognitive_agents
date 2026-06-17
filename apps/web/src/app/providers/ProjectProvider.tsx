import React, { createContext, useContext, useState, useEffect } from 'react';
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



export const ProjectProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: fetchedProjects, isLoading, error } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: async () => {
      try {
        const data = await apiFetch('/v1/projects');
        return data;
      } catch (e) {
        throw e;
      }
    },
    enabled: !!user,
  });

  const createMutation = useMutation({
    mutationFn: async ({ name, description }: { name: string; description?: string }) => {
      return apiFetch('/v1/projects', {
        method: 'POST',
        body: JSON.stringify({ name, description }),
      });
    },
    onSuccess: (newProject: Project) => {
      queryClient.setQueryData<Project[]>(['projects'], (old = []) => [...old, newProject]);
      setActiveProject(newProject);
    },
  });

  const projects = fetchedProjects ?? [];

  useEffect(() => {
    if (!activeProject && projects.length > 0) {
      setActiveProject(projects[0]);
    }
  }, [projects, activeProject]);

  const createProject = async (name: string, description?: string) => {
    await createMutation.mutateAsync({ name, description });
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
