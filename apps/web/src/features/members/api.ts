import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../../lib/api';

export interface Member {
  project_id: string;
  user_id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  role: 'admin' | 'member' | 'viewer';
  joined_at: string;
  invited_by: string | null;
}

export interface Invitation {
  id: string;
  project_id: string;
  email: string;
  role: 'admin' | 'member' | 'viewer';
  status: string;
  invited_by: string | null;
  created_at: string;
  expires_at: string;
}

export interface UserInvitation extends Invitation {
  project_name: string;
  token: string;
}

export const useMembers = (projectId?: string) => {
  return useQuery<Member[]>({
    queryKey: ['members', projectId],
    queryFn: async () => {
      return await apiFetch(`/v1/projects/${projectId}/members`);
    },
    enabled: !!projectId,
  });
};

export const useInvitations = (projectId?: string) => {
  return useQuery<Invitation[]>({
    queryKey: ['invitations', projectId],
    queryFn: async () => {
      return await apiFetch(`/v1/projects/${projectId}/invitations`);
    },
    enabled: !!projectId,
  });
};

export const useInviteMember = (projectId?: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ email, role }: { email: string; role: string }) => {
      return await apiFetch(`/v1/projects/${projectId}/members`, {
        method: 'POST',
        body: JSON.stringify({ email, role }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invitations', projectId] });
    },
  });
};

export const useUpdateRole = (projectId?: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ userId, role }: { userId: string; role: string }) => {
      return await apiFetch(`/v1/projects/${projectId}/members/${userId}/role`, {
        method: 'PATCH',
        body: JSON.stringify({ role }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', projectId] });
    },
  });
};

export const useRemoveMember = (projectId?: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (userId: string) => {
      return await apiFetch(`/v1/projects/${projectId}/members/${userId}`, {
        method: 'DELETE',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', projectId] });
    },
  });
};

export const useAcceptInvite = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (token: string) => {
      return await apiFetch(`/v1/invitations/accept`, {
        method: 'POST',
        body: JSON.stringify({ token }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['my_invitations'] });
    },
  });
};

export const useMyInvitations = () => {
  return useQuery<UserInvitation[]>({
    queryKey: ['my_invitations'],
    queryFn: async () => {
      return await apiFetch(`/v1/invitations/me`);
    },
  });
};

export const useDeclineInvite = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (token: string) => {
      return await apiFetch(`/v1/invitations/decline`, {
        method: 'POST',
        body: JSON.stringify({ token }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my_invitations'] });
    },
  });
};

export const useDeleteInvitation = (projectId?: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (invitationId: string) => {
      return await apiFetch(`/v1/projects/${projectId}/invitations/${invitationId}`, {
        method: 'DELETE',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invitations', projectId] });
    },
  });
};
