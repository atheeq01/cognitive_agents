import React from 'react';
import { useAuth } from '../../app/providers/AuthProvider';
import { useProject } from '../../app/providers/ProjectProvider';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { MessageSquare, FileText, Users, Command, ArrowRight } from 'lucide-react';

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
    <div className="max-w-5xl mx-auto py-12 px-4 h-full flex flex-col justify-center min-h-[80vh]">
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-12"
      >
        <motion.div variants={itemVariants} className="text-center max-w-3xl mx-auto space-y-4">
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-foreground">
            Welcome back{user?.displayName ? `, ${user.displayName.split(' ')[0]}` : ''}.
          </h1>
          <p className="text-xl text-muted-foreground">
            {activeProject ? (
              <>You are currently working in <span className="font-medium text-foreground">{activeProject.name}</span>.</>
            ) : (
              <>Select a project from the top right to get started.</>
            )}
          </p>
          
          <div className="pt-4 flex items-center justify-center gap-2 text-sm text-muted-foreground bg-muted/50 w-fit mx-auto px-4 py-2 rounded-full border">
            <Command className="w-4 h-4" />
            <span>Press <kbd className="font-mono bg-background px-1.5 py-0.5 rounded border shadow-sm mx-1">Cmd</kbd> + <kbd className="font-mono bg-background px-1.5 py-0.5 rounded border shadow-sm mx-1">K</kbd> anywhere to quickly navigate</span>
          </div>
        </motion.div>

        {activeProject && (
          <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-8">
            <Link to="/chat" className="group flex flex-col h-full bg-card hover:bg-accent/50 border rounded-2xl p-6 transition-all duration-300 shadow-sm hover:shadow-md">
              <div className="w-12 h-12 bg-blue-500/10 text-blue-500 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <MessageSquare className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold mb-2 flex items-center justify-between">
                Knowledge Chat
                <ArrowRight className="w-4 h-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
              </h3>
              <p className="text-sm text-muted-foreground flex-1">
                Interact with the AI agent to ask questions and extract insights from your project's documents.
              </p>
            </Link>

            <Link to="/admin" className="group flex flex-col h-full bg-card hover:bg-accent/50 border rounded-2xl p-6 transition-all duration-300 shadow-sm hover:shadow-md">
              <div className="w-12 h-12 bg-emerald-500/10 text-emerald-500 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <FileText className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold mb-2 flex items-center justify-between">
                Document Hub
                <ArrowRight className="w-4 h-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
              </h3>
              <p className="text-sm text-muted-foreground flex-1">
                Upload new knowledge bases, review pending documents, and manage your library.
              </p>
            </Link>

            <Link to="/members" className="group flex flex-col h-full bg-card hover:bg-accent/50 border rounded-2xl p-6 transition-all duration-300 shadow-sm hover:shadow-md">
              <div className="w-12 h-12 bg-purple-500/10 text-purple-500 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Users className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold mb-2 flex items-center justify-between">
                Team Access
                <ArrowRight className="w-4 h-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
              </h3>
              <p className="text-sm text-muted-foreground flex-1">
                Invite colleagues, manage project roles, and review pending invitations.
              </p>
            </Link>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
};
