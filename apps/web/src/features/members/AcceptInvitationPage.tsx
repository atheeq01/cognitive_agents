import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAcceptInvite } from './api';
import { useAuth } from '../../app/providers/AuthProvider';
import { motion } from 'framer-motion';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import { toast } from 'sonner';

const AcceptInvitationPage = () => {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const acceptMutation = useAcceptInvite();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (!token) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setStatus('error');
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setErrorMsg('No invitation token provided');
      return;
    }

    if (!user) {
      // They need to be logged in to accept
      // You could redirect them to /login with a return URL, but for simplicity we show an error
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setStatus('error');
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setErrorMsg('You must be logged in to accept an invitation.');
      return;
    }

    const acceptInvite = async () => {
      try {
        await acceptMutation.mutateAsync(token);
        setStatus('success');
        toast.success('Invitation accepted successfully!');
        // Redirect to dashboard after a short delay
        setTimeout(() => {
          navigate('/');
        }, 2000);
      } catch (err) {
        setStatus('error');
        setErrorMsg(err instanceof Error ? err.message : 'Failed to accept invitation. It may have expired.');
      }
    };

    void acceptInvite();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, user]);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full bg-card border shadow-xl rounded-2xl p-8 text-center"
      >
        <div className="mb-6 flex justify-center">
          {status === 'loading' && (
            <div className="w-16 h-16 bg-primary/10 text-primary rounded-full flex items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin" />
            </div>
          )}
          {status === 'success' && (
            <div className="w-16 h-16 bg-green-500/10 text-green-500 rounded-full flex items-center justify-center">
              <CheckCircle className="w-8 h-8" />
            </div>
          )}
          {status === 'error' && (
            <div className="w-16 h-16 bg-destructive/10 text-destructive rounded-full flex items-center justify-center">
              <XCircle className="w-8 h-8" />
            </div>
          )}
        </div>

        <h1 className="text-2xl font-bold mb-2">
          {status === 'loading' && 'Processing Invitation...'}
          {status === 'success' && 'Welcome to the Project!'}
          {status === 'error' && 'Invitation Failed'}
        </h1>
        
        <p className="text-muted-foreground mb-8">
          {status === 'loading' && 'Please wait while we verify your invitation token.'}
          {status === 'success' && 'Your invitation has been accepted. Redirecting you to the dashboard...'}
          {status === 'error' && errorMsg}
        </p>

        {status === 'error' && !user && (
          <button
            onClick={() => navigate('/login')}
            className="w-full h-10 bg-primary text-primary-foreground rounded-md font-medium hover:bg-primary/90 transition-colors"
          >
            Log In Now
          </button>
        )}
        
        {status === 'error' && user && (
          <button
            onClick={() => navigate('/')}
            className="w-full h-10 border bg-background text-foreground rounded-md font-medium hover:bg-accent transition-colors"
          >
            Return to Dashboard
          </button>
        )}
      </motion.div>
    </div>
  );
};

export default AcceptInvitationPage;
