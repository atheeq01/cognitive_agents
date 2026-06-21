import React from 'react';
import { useAuth } from '../../app/providers/AuthProvider';
import { useProject } from '../../app/providers/ProjectProvider';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { MessageSquare, FileText, Users, Command, Sparkles } from 'lucide-react';

export const HomePage: React.FC = () => {
  const { user } = useAuth();
  const { activeProject } = useProject();

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1, 
      transition: { staggerChildren: 0.1 } 
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <div className="max-w-6xl mx-auto py-12 px-6 h-full flex flex-col">
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-16"
      >
        <motion.div variants={itemVariants} className="flex flex-col items-center text-center space-y-4 pt-8">
          <div className="w-16 h-16 bg-primary rounded-2xl flex items-center justify-center text-primary-foreground shadow-lg mb-4">
            <Sparkles className="w-8 h-8" />
          </div>
          <h1 className="text-3xl md:text-5xl font-bold tracking-tight text-foreground">
            Welcome back{user?.displayName ? `, ${user.displayName.split(' ')[0]}` : ''}
          </h1>
          <p className="text-lg text-muted-foreground">
            {activeProject ? (
              <>You are currently working in <span className="font-semibold text-foreground">{activeProject.name}</span></>
            ) : (
              <>Select a project to get started</>
            )}
          </p>
        </motion.div>

        {activeProject && (
          <motion.div variants={itemVariants} className="flex justify-center">
            <div className="flex flex-wrap justify-center gap-4 max-w-4xl">
              <Link to={`/projects/${activeProject.project_id}/chat`} className="group flex flex-col w-[280px] bg-card hover:bg-accent/30 border border-border/60 rounded-2xl p-5 transition-all duration-300 shadow-sm hover:shadow-md cursor-pointer">
                <div className="w-10 h-10 bg-[#e6f0ff] text-blue-600 rounded-xl flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <h3 className="text-base font-semibold text-foreground mb-1">
                  Knowledge Chat
                </h3>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  Interact with the AI agent and extract insights.
                </p>
              </Link>

              <Link to={`/projects/${activeProject.project_id}/admin`} className="group flex flex-col w-[280px] bg-card hover:bg-accent/30 border border-border/60 rounded-2xl p-5 transition-all duration-300 shadow-sm hover:shadow-md cursor-pointer">
                <div className="w-10 h-10 bg-[#e6fff0] text-emerald-600 rounded-xl flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                  <FileText className="w-5 h-5" />
                </div>
                <h3 className="text-base font-semibold text-foreground mb-1">
                  Documents
                </h3>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  Upload and manage your knowledge base.
                </p>
              </Link>

              <Link to={`/projects/${activeProject.project_id}/members`} className="group flex flex-col w-[280px] bg-card hover:bg-accent/30 border border-border/60 rounded-2xl p-5 transition-all duration-300 shadow-sm hover:shadow-md cursor-pointer">
                <div className="w-10 h-10 bg-[#f4e6ff] text-purple-600 rounded-xl flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                  <Users className="w-5 h-5" />
                </div>
                <h3 className="text-base font-semibold text-foreground mb-1">
                  Team Access
                </h3>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  Invite colleagues and manage roles.
                </p>
              </Link>
            </div>
          </motion.div>
        )}

        <motion.div variants={itemVariants} className="pt-12 pb-4 flex justify-center">
          <div className="flex items-center gap-2 text-xs text-muted-foreground bg-accent/50 px-4 py-2 rounded-full border border-border/50">
            <Command className="w-3.5 h-3.5" />
            <span>Press <kbd className="font-mono bg-background px-1.5 py-0.5 rounded border shadow-sm mx-1">Cmd</kbd> + <kbd className="font-mono bg-background px-1.5 py-0.5 rounded border shadow-sm mx-1">K</kbd> anywhere to quickly navigate</span>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
};
