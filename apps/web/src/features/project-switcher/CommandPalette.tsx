import React, { useEffect, useState } from 'react';
import { Command } from 'cmdk';
import { useProject } from '../../app/providers/ProjectProvider';
import { useNavigate } from 'react-router-dom';

export const CommandPalette: React.FC = () => {
  const [open, setOpen] = useState(false);
  const { projects, setActiveProject } = useProject();
  const navigate = useNavigate();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex justify-center items-start pt-[15vh]">
      <div className="w-full max-w-lg shadow-2xl border rounded-lg bg-popover text-popover-foreground overflow-hidden">
        <Command label="Global Command Menu" onKeyDown={(e) => {
          if (e.key === 'Escape') setOpen(false);
        }}>
          <div className="flex items-center border-b px-3">
            <svg className="w-5 h-5 text-muted-foreground mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            <Command.Input 
              autoFocus
              className="flex h-12 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="Type a command or search..." 
            />
          </div>
          <Command.List className="max-h-[300px] overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-sm text-muted-foreground">No results found.</Command.Empty>
            
            <Command.Group heading="Projects" className="text-xs font-medium text-muted-foreground px-2 py-1.5">
              {projects.map(p => (
                  <Command.Item 
                    key={p.project_id} 
                    onSelect={() => {
                      setActiveProject(p);
                      setOpen(false);
                    }}
                    className="flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none aria-selected:bg-accent aria-selected:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                  >
                    Switch to {p.name}
                  </Command.Item>
                ))}
            </Command.Group>

            <Command.Group heading="Navigation & Actions" className="text-xs font-medium text-muted-foreground px-2 py-1.5 mt-2">
              <Command.Item 
                onSelect={() => { navigate(activeProject ? `/projects/${activeProject.project_id}` : '/'); setOpen(false); }}
                className="flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none aria-selected:bg-accent aria-selected:text-accent-foreground"
              >
                Go to Home
              </Command.Item>
              <Command.Item 
                onSelect={() => { navigate(activeProject ? `/projects/${activeProject.project_id}/admin` : '/'); setOpen(false); }}
                className="flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none aria-selected:bg-accent aria-selected:text-accent-foreground mt-1"
              >
                Go to Dashboard
              </Command.Item>
              <Command.Item 
                onSelect={() => { navigate(activeProject ? `/projects/${activeProject.project_id}/chat` : '/'); setOpen(false); }}
                className="flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none aria-selected:bg-accent aria-selected:text-accent-foreground mt-1"
              >
                Go to Knowledge Chat
              </Command.Item>
              <Command.Item 
                onSelect={() => { navigate(activeProject ? `/projects/${activeProject.project_id}/members` : '/'); setOpen(false); }}
                className="flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none aria-selected:bg-accent aria-selected:text-accent-foreground mt-1"
              >
                Go to Member Management
              </Command.Item>
              <Command.Item 
                onSelect={() => { 
                  document.documentElement.classList.toggle('dark');
                  setOpen(false); 
                }}
                className="flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none aria-selected:bg-accent aria-selected:text-accent-foreground mt-1"
              >
                Toggle Theme (Light/Dark)
              </Command.Item>
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
};
