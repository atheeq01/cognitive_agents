import React, { useState, useRef, useEffect } from 'react';
import { Bell, Check, X } from 'lucide-react';
import { useMyInvitations, useAcceptInvite, useDeclineInvite } from './api';
import { motion, AnimatePresence } from 'framer-motion';

export const PendingInvitationsDropdown: React.FC = () => {
  const { data: invitations, isLoading } = useMyInvitations();
  const acceptInvite = useAcceptInvite();
  const declineInvite = useDeclineInvite();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const pendingCount = invitations?.length || 0;

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
        title="Invitations"
      >
        <Bell className="w-5 h-5" />
        {pendingCount > 0 && (
          <span className="absolute top-1 right-1.5 flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500 border border-card"></span>
          </span>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 mt-2 w-80 bg-popover text-popover-foreground border rounded-xl shadow-xl z-50 overflow-hidden"
          >
            <div className="px-4 py-3 border-b bg-muted/30 flex justify-between items-center">
              <h3 className="font-semibold text-sm">Pending Invitations</h3>
              {pendingCount > 0 && (
                <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
                  {pendingCount}
                </span>
              )}
            </div>

            <div className="max-h-[300px] overflow-y-auto p-2">
              {isLoading ? (
                <div className="p-4 text-center text-sm text-muted-foreground animate-pulse">
                  Loading invitations...
                </div>
              ) : pendingCount === 0 ? (
                <div className="p-6 text-center flex flex-col items-center justify-center text-muted-foreground">
                  <div className="bg-muted/50 p-3 rounded-full mb-3">
                    <Bell className="w-6 h-6 opacity-50" />
                  </div>
                  <p className="text-sm">You have no pending invitations.</p>
                </div>
              ) : (
                <ul className="space-y-2">
                  {invitations?.map((inv) => (
                    <li key={inv.id} className="p-3 bg-card border rounded-lg hover:shadow-sm transition-shadow">
                      <div className="flex flex-col space-y-2">
                        <div>
                          <p className="text-sm font-medium">
                            {inv.project_name}
                          </p>
                          <p className="text-xs text-muted-foreground mt-0.5">
                            Role: <span className="capitalize text-foreground font-medium">{inv.role}</span>
                          </p>
                        </div>
                        <div className="flex items-center gap-2 pt-2">
                          <button
                            onClick={() => {
                              acceptInvite.mutate(inv.token);
                            }}
                            disabled={acceptInvite.isPending}
                            className="flex-1 flex items-center justify-center gap-1 bg-primary text-primary-foreground text-xs py-1.5 px-3 rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
                          >
                            <Check className="w-3 h-3" />
                            Accept
                          </button>
                          <button
                            onClick={() => {
                              declineInvite.mutate(inv.token);
                            }}
                            disabled={declineInvite.isPending}
                            className="flex-1 flex items-center justify-center gap-1 bg-secondary text-secondary-foreground text-xs py-1.5 px-3 rounded-md hover:bg-secondary/80 transition-colors disabled:opacity-50 border border-transparent hover:border-destructive/30 hover:text-destructive"
                          >
                            <X className="w-3 h-3" />
                            Decline
                          </button>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
