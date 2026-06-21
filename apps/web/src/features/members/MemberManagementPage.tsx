import React, { useState } from 'react';
import { useProject } from '../../app/providers/ProjectProvider';
import { useMembers, useInvitations, useInviteMember, useUpdateRole, useRemoveMember, useDeleteInvitation } from './api';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { UserPlus, UserMinus, Shield, Eye, Loader2, Mail, Users, Trash2 } from 'lucide-react';

const MemberManagementPage = () => {
  const { activeProject } = useProject();
  const projectId = activeProject?.project_id;
  const isAdmin = activeProject?.role === 'admin';

  const { data: members = [], isLoading: membersLoading } = useMembers(projectId);
  const { data: invitations = [] } = useInvitations(projectId);
  
  const inviteMutation = useInviteMember(projectId);
  const updateRoleMutation = useUpdateRole(projectId);
  const removeMemberMutation = useRemoveMember(projectId);
  const deleteInvitationMutation = useDeleteInvitation(projectId);

  const [activeTab, setActiveTab] = useState<'members' | 'viewers'>('members');
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'admin' | 'member' | 'viewer'>('member');

  if (!projectId) {
    return <div className="p-8 text-center text-muted-foreground">Please select a project first.</div>;
  }

  const adminsAndMembers = members.filter(m => m.role === 'admin' || m.role === 'member');
  const viewers = members.filter(m => m.role === 'viewer');
  const adminCount = members.filter(m => m.role === 'admin').length;

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail) return;
    try {
      await inviteMutation.mutateAsync({ email: inviteEmail, role: inviteRole });
      toast.success(`Invitation sent to ${inviteEmail}`);
      setIsInviteModalOpen(false);
      setInviteEmail('');
      setInviteRole('member');
    } catch (err: any) {
      toast.error('Failed to send invitation', { description: err.message });
    }
  };

  const handleRoleUpdate = async (userId: string, newRole: string) => {
    try {
      await updateRoleMutation.mutateAsync({ userId, role: newRole });
      toast.success('Role updated successfully');
    } catch (err: any) {
      toast.error('Failed to update role', { description: err.message });
    }
  };

  const handleRemoveMember = async (userId: string) => {
    if (!window.confirm('Are you sure you want to remove this member?')) return;
    try {
      await removeMemberMutation.mutateAsync(userId);
      toast.success('Member removed');
    } catch (err: any) {
      toast.error('Failed to remove member', { description: err.message });
    }
  };

  const handleDeleteInvitation = async (invitationId: string) => {
    if (!window.confirm('Are you sure you want to cancel this invitation?')) return;
    try {
      await deleteInvitationMutation.mutateAsync(invitationId);
      toast.success('Invitation cancelled');
    } catch (err: any) {
      toast.error('Failed to cancel invitation', { description: err.message });
    }
  };

  const listVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.05 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Member Management</h1>
          <p className="text-muted-foreground mt-1 text-sm">Manage who has access to {activeProject?.name}</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => setIsInviteModalOpen(true)}
            className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 flex items-center gap-2 rounded-lg text-sm font-medium transition-colors shadow-sm"
          >
            <UserPlus className="w-4 h-4" />
            Invite People
          </button>
        )}
      </div>

      <div className="flex space-x-1 border-b mb-6">
        <button
          onClick={() => setActiveTab('members')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors relative ${
            activeTab === 'members'
              ? 'border-primary text-foreground'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Members ({adminsAndMembers.length})
          </div>
        </button>
        <button
          onClick={() => setActiveTab('viewers')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors relative ${
            activeTab === 'viewers'
              ? 'border-primary text-foreground'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4" />
            Viewers ({viewers.length})
          </div>
        </button>
      </div>

      <div className="bg-card border rounded-xl overflow-hidden shadow-sm">
        {membersLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <motion.ul
            variants={listVariants}
            initial="hidden"
            animate="visible"
            className="divide-y"
          >
            {(activeTab === 'members' ? adminsAndMembers : viewers).length === 0 ? (
              <div className="py-12 text-center text-muted-foreground flex flex-col items-center">
                <Users className="w-12 h-12 mb-3 opacity-20" />
                <p>No {activeTab} found in this project.</p>
              </div>
            ) : (
              (activeTab === 'members' ? adminsAndMembers : viewers).map((member) => (
                <motion.li key={member.user_id} variants={itemVariants} className="flex items-center justify-between p-4 hover:bg-muted/30 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-sm uppercase">
                      {member.avatar_url ? (
                        <img src={member.avatar_url} alt={member.name || member.email} className="w-full h-full rounded-full object-cover" />
                      ) : (
                        ((member.name || member.email) || 'U')[0]
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-sm text-foreground">{member.name || 'Unknown Name'}</p>
                      <p className="text-xs text-muted-foreground">{member.email}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    {isAdmin ? (
                      <select
                        value={member.role}
                        onChange={(e) => handleRoleUpdate(member.user_id, e.target.value)}
                        disabled={member.role === 'admin' && adminCount <= 1}
                        title={member.role === 'admin' && adminCount <= 1 ? "Cannot change role of the last admin" : ""}
                        className="text-xs border bg-background px-2 py-1.5 rounded-md text-foreground outline-none focus:ring-2 focus:ring-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <option value="admin">Admin</option>
                        <option value="member">Member</option>
                        <option value="viewer">Viewer</option>
                      </select>
                    ) : (
                      <span className="text-xs bg-secondary text-secondary-foreground px-2 py-1 rounded-md capitalize font-medium flex items-center gap-1">
                        {member.role === 'admin' && <Shield className="w-3 h-3" />}
                        {member.role}
                      </span>
                    )}
                    
                    {isAdmin && member.role !== 'admin' && (
                      <button
                        onClick={() => handleRemoveMember(member.user_id)}
                        className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-md transition-colors"
                        title="Remove member"
                      >
                        <UserMinus className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </motion.li>
              ))
            )}
          </motion.ul>
        )}
      </div>

      {isAdmin && invitations.length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-semibold mb-4">Pending Invitations</h3>
          <div className="bg-card border rounded-xl overflow-hidden shadow-sm">
            <ul className="divide-y">
              {invitations.map((invite) => (
                <li key={invite.id} className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-secondary text-secondary-foreground flex items-center justify-center font-bold text-sm">
                      <Mail className="w-4 h-4 opacity-50" />
                    </div>
                    <div>
                      <p className="font-medium text-sm text-foreground">{invite.email}</p>
                      <p className="text-xs text-muted-foreground flex gap-2">
                        <span>Invited to be {invite.role}</span>
                        <span>•</span>
                        <span>Sent {new Date(invite.created_at).toLocaleDateString()}</span>
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-xs bg-amber-500/15 text-amber-700 dark:text-amber-400 px-2 py-1 rounded-full font-medium">
                      Pending
                    </span>
                    <button
                      onClick={() => handleDeleteInvitation(invite.id)}
                      className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-md transition-colors"
                      title="Cancel invitation"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <AnimatePresence>
        {isInviteModalOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40"
              onClick={() => setIsInviteModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="fixed left-[50%] top-[50%] z-50 grid w-full max-w-md translate-x-[-50%] translate-y-[-50%] gap-4 border bg-card p-6 shadow-lg sm:rounded-xl"
            >
              <div className="flex flex-col space-y-1.5 text-center sm:text-left mb-4">
                <h2 className="text-lg font-semibold leading-none tracking-tight">Invite to Project</h2>
                <p className="text-sm text-muted-foreground">
                  Send an email invitation to collaborate on this project.
                </p>
              </div>
              <form onSubmit={handleInvite} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium leading-none">Email address</label>
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="colleague@example.com"
                    required
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium leading-none">Role</label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as any)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  >
                    <option value="admin">Admin - Full access</option>
                    <option value="member">Member - Can edit content</option>
                    <option value="viewer">Viewer - Read only</option>
                  </select>
                </div>
                <div className="flex items-center justify-end space-x-2 pt-4 border-t">
                  <button
                    type="button"
                    onClick={() => setIsInviteModalOpen(false)}
                    className="h-10 px-4 py-2 border rounded-md text-sm font-medium hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={inviteMutation.isPending}
                    className="h-10 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2"
                  >
                    {inviteMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                    Send Invitation
                  </button>
                </div>
              </form>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MemberManagementPage;
