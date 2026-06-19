import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { type DocumentIntelligenceResults } from './useDocumentIntelligence';
import { FileText, Brain } from 'lucide-react';

interface ResultsPanelProps {
  results: DocumentIntelligenceResults;
}

export const ResultsPanel: React.FC<ResultsPanelProps> = ({ results }) => {
  const [activeTab, setActiveTab] = useState<'summary' | 'cognitive'>('summary');

  const tabs = [
    { id: 'summary', label: 'Summary', icon: FileText },
    { id: 'cognitive', label: 'Cognitive Insights', icon: Brain },
  ];

  return (
    <div className="w-full mt-8 border rounded-2xl overflow-hidden bg-card shadow-lg">
      {/* Tabs */}
      <div className="flex border-b overflow-x-auto bg-muted/20 hide-scrollbar">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`flex items-center space-x-2 px-6 py-4 text-sm font-medium transition-colors relative whitespace-nowrap
              ${activeTab === tab.id ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}
          >
            <tab.icon className="w-4 h-4" />
            <span>{tab.label}</span>
            {activeTab === tab.id && (
              <motion.div
                layoutId="activeTabIndicator"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"
                initial={false}
              />
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-6 md:p-8 min-h-[400px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'summary' && (
              <div className="space-y-4">
                <h3 className="text-xl font-bold">Executive Summary</h3>
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  {results.summary ? results.summary.split('\n').map((paragraph, idx) => (
                    <p key={idx} className="text-muted-foreground leading-relaxed">{paragraph}</p>
                  )) : <p className="text-muted-foreground">No summary available.</p>}
                </div>
              </div>
            )}

            {activeTab === 'cognitive' && (
              <div className="space-y-8">
                <div>
                  <h4 className="text-lg font-semibold mb-2 flex items-center"><Brain className="w-5 h-5 mr-2 text-blue-500" /> Primary Intent</h4>
                  <p className="p-4 bg-blue-500/10 text-blue-700 dark:text-blue-300 rounded-lg border border-blue-500/20">{results.cognitive_insights?.intent || 'No intent extracted.'}</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold mb-3">Reasoning Patterns</h4>
                    <ul className="space-y-2">
                      {results.cognitive_insights?.reasoning_patterns?.length > 0 ? results.cognitive_insights.reasoning_patterns.map((p: string, i: number) => (
                        <li key={i} className="flex items-start"><span className="mr-2 text-primary">•</span><span className="text-sm text-muted-foreground">{p}</span></li>
                      )) : <p className="text-sm text-muted-foreground">None identified.</p>}
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-3">Unstated Assumptions</h4>
                    <ul className="space-y-2">
                      {results.cognitive_insights?.assumptions?.length > 0 ? results.cognitive_insights.assumptions.map((a: string, i: number) => (
                        <li key={i} className="flex items-start"><span className="mr-2 text-amber-500">•</span><span className="text-sm text-muted-foreground">{a}</span></li>
                      )) : <p className="text-sm text-muted-foreground">None identified.</p>}
                    </ul>
                  </div>
                </div>
              </div>
            )}



          </motion.div>
        </AnimatePresence>
        
        <div className="mt-8 pt-6 border-t border-border flex justify-center">
          <a href="./report" className="inline-flex items-center text-sm font-medium text-primary hover:text-primary/80 transition-colors">
            See how this fits into the project →
          </a>
        </div>
      </div>
    </div>
  );
};
