import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { addFeedSource, ProcessRSSResult } from '@/lib/api';
import { PlusCircleIcon, ExclamationCircleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

export default function AddFeedForm() {
  const [url, setUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const mutation = useMutation<ProcessRSSResult, Error, string>({
    mutationFn: async (url) => {
      return await addFeedSource(url, 100);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['feedSources'] });
      setUrl('');
      setSuccess(`Successfully processed ${data.articles_processed} articles from ${data.source_url}`);
      setError(null);
      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(null), 5000);
    },
    onError: (error) => {
      setError(error.message || 'Failed to add feed. Please try again.');
      setSuccess(null);
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) {
      setError('Please enter a valid URL');
      return;
    }
    
    setError(null);
    setSuccess(null);
    setIsSubmitting(true);
    
    try {
      await mutation.mutateAsync(url);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-2">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Enter RSS feed URL"
            className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            required
            disabled={isSubmitting}
          />
          <button
            type="submit"
            disabled={isSubmitting || !url.trim()}
            className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <PlusCircleIcon className="h-5 w-5 mr-1" />
            {isSubmitting ? 'Processing...' : 'Add Feed'}
          </button>
        </div>
      </form>

      {/* Error message */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <ExclamationCircleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Success message */}
      {success && (
        <div className="rounded-md bg-green-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <CheckCircleIcon className="h-5 w-5 text-green-400" aria-hidden="true" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-green-800">{success}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
