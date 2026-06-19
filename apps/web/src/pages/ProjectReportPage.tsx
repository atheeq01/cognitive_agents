import React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useProject } from '../app/providers/ProjectProvider';
import { apiFetch } from '../lib/api';
import { Loader2, RefreshCw, FileText, Brain, ShieldAlert, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { CitationChip } from '../components/CitationChip';

export const ProjectReportPage: React.FC = () => {
  const { activeProject } = useProject();
  const projectId = activeProject?.project_id;

  const { data: report, isLoading, refetch } = useQuery({
    queryKey: ['project_report', projectId],
    queryFn: async () => {
      return await apiFetch(`/v1/projects/${projectId}/report`);
    },
    enabled: !!projectId,
  });



  const filteredReport = React.useMemo(() => {
    return report;
  }, [report]);

  const refreshMutation = useMutation({
    mutationFn: () => apiFetch(`/v1/projects/${projectId}/report/refresh`, { method: 'POST' }),
    onSuccess: () => {
      toast.success('Report refresh triggered');
      refetch();
    },
    onError: (err: Error) => {
      toast.error('Failed to refresh report', { description: err.message });
    }
  });

  if (!projectId) {
    return <div className="p-8 text-center text-muted-foreground">Please select a project first.</div>;
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-20 text-muted-foreground space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p>Loading Intelligence Report...</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      <div className="flex justify-between items-center bg-card p-6 rounded-2xl border shadow-sm">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Project Intelligence Report</h1>
          <p className="text-muted-foreground mt-2">
            Synthesized insights across {filteredReport?.document_count || 0} documents.
            {filteredReport?.generated_at && <span className="ml-2">• Last generated: {new Date(filteredReport.generated_at).toLocaleString()}</span>}
          </p>
        </div>
        <button
          onClick={() => refreshMutation.mutate()}
          disabled={refreshMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshMutation.isPending ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {filteredReport?.unified_summary && (
        <section className="bg-card p-8 rounded-2xl border shadow-sm space-y-4">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <FileText className="w-6 h-6 text-primary" />
            Unified Summary
          </h2>
          <div className="prose dark:prose-invert max-w-none text-lg leading-relaxed text-foreground/90">
            {filteredReport.unified_summary}
          </div>
        </section>
      )}

      {filteredReport?.contradictions && filteredReport.contradictions.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-2xl font-bold flex items-center gap-2 text-destructive">
            <ShieldAlert className="w-6 h-6" />
            Where the Documents Disagree
          </h2>
          <div className="grid gap-6">
            {filteredReport.contradictions.map((c: any, i: number) => (
              <div key={i} className="bg-destructive/5 border border-destructive/20 rounded-2xl p-6 hover:shadow-xl hover:border-destructive/40 transition-all duration-300 transform hover:-translate-y-1">
                <div className="flex justify-between items-start mb-6">
                  <h3 className="font-bold text-lg text-destructive/90">{c.topic}</h3>
                  <span className="px-3 py-1 bg-destructive/10 text-destructive text-xs font-bold uppercase rounded-full tracking-wider shadow-sm">
                    {c.conflict_type}
                  </span>
                </div>
                
                <div className="grid md:grid-cols-2 gap-6 mb-6">
                  <div className="bg-background rounded-xl p-5 border shadow-sm hover:shadow-md transition-shadow duration-300">
                    <p className="font-medium mb-4 italic text-foreground/80">"{c.claim_a}"</p>
                    <CitationChip source={c.claim_a_source} />
                  </div>
                  <div className="bg-background rounded-xl p-5 border shadow-sm hover:shadow-md transition-shadow duration-300">
                    <p className="font-medium mb-4 italic text-foreground/80">"{c.claim_b}"</p>
                    <CitationChip source={c.claim_b_source} />
                  </div>
                </div>

                <div className="bg-background/50 rounded-xl p-4 border border-border/50 hover:bg-background transition-colors duration-300">
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider block mb-2">Why this matters</span>
                  <p className="text-foreground/90">{c.explanation}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {filteredReport?.agreements && filteredReport.agreements.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-2xl font-bold flex items-center gap-2 text-green-600 dark:text-green-500">
            <CheckCircle className="w-6 h-6" />
            Similarities Across Documents
          </h2>
          <div className="grid gap-6">
            {filteredReport.agreements.map((a: any, i: number) => (
              <div key={i} className="bg-green-500/5 border border-green-500/20 rounded-2xl p-6 hover:shadow-lg hover:border-green-500/40 transition-all duration-300 transform hover:-translate-y-1">
                <h3 className="font-bold text-lg mb-4 text-green-700 dark:text-green-400">{a.topic}</h3>
                <ul className="space-y-4">
                  {a.supporting_claims.map((claim: string, idx: number) => (
                    <li key={idx} className="flex flex-col gap-2">
                      <span className="font-medium">"{claim}"</span>
                      {a.supporting_sources?.[idx] && <CitationChip source={a.supporting_sources[idx]} />}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {filteredReport?.cognitive_synthesis && (
        <section className="bg-card p-8 rounded-2xl border shadow-sm space-y-6 hover:shadow-xl transition-shadow duration-300">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="w-6 h-6 text-blue-500" />
            Cognitive Synthesis
          </h2>
          <div className="grid md:grid-cols-2 gap-8">
            {filteredReport.cognitive_synthesis.intents && filteredReport.cognitive_synthesis.intents.length > 0 && (
              <div>
                <h3 className="font-bold mb-4 text-muted-foreground uppercase tracking-wider text-sm">Identified Intents</h3>
                <ul className="space-y-2">
                  {filteredReport.cognitive_synthesis.intents.map((item: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {filteredReport.cognitive_synthesis.reasoning_patterns && filteredReport.cognitive_synthesis.reasoning_patterns.length > 0 && (
              <div>
                <h3 className="font-bold mb-4 text-muted-foreground uppercase tracking-wider text-sm">Reasoning Patterns</h3>
                <ul className="space-y-2">
                  {filteredReport.cognitive_synthesis.reasoning_patterns.map((item: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
};
