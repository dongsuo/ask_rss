'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listFeedSources, addFeedSource, ProcessRSSResult } from '@/lib/api';
import { PlusCircleIcon, TrashIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';
import Link from 'next/link';

export default function SettingsPage() {
  const [url, setUrl] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: sources = [], isLoading, error: fetchError } = useQuery({
    queryKey: ['feedSources'],
    queryFn: listFeedSources,
  });

  const mutation = useMutation<ProcessRSSResult, Error, string>({
    mutationFn: async (url) => {
      return await addFeedSource(url, 100);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['feedSources'] });
      setUrl('');
      setSuccess(`Successfully processed ${data.articles_processed} articles from ${data.source_url}`);
      setError(null);
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
    mutation.mutate(url);
  };

  // TODO: Implement delete functionality
  const handleDelete = async (sourceUrl: string) => {
    // Implement delete functionality
    console.log('Delete:', sourceUrl);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center mb-8">
        <Link href="/" className="mr-4">
          <ArrowLeftIcon className="h-6 w-6 text-gray-600 hover:text-gray-900" />
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">RSS Feed Settings</h1>
      </div>

      <div className="bg-white shadow rounded-lg p-6 mb-8">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Add New RSS Feed</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex gap-2">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter RSS feed URL"
              className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              required
              disabled={mutation.isPending}
            />
            <button
              type="submit"
              disabled={mutation.isPending || !url.trim()}
              className="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <PlusCircleIcon className="h-5 w-5 mr-1" />
              {mutation.isPending ? 'Adding...' : 'Add Feed'}
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-4 p-4 bg-red-50 rounded-md">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {success && (
          <div className="mt-4 p-4 bg-green-50 rounded-md">
            <p className="text-sm text-green-700">{success}</p>
          </div>
        )}
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Your RSS Feeds</h2>
        
        {isLoading ? (
          <p className="text-gray-500">Loading feeds...</p>
        ) : fetchError ? (
          <p className="text-red-500">Error loading feeds. Please try again.</p>
        ) : sources.length === 0 ? (
          <p className="text-gray-500">No RSS feeds added yet. Add one above to get started.</p>
        ) : (
          <ul className="divide-y divide-gray-200">
            {sources.map((source) => (
              <li key={source.url} className="py-4 flex justify-between items-center">
                <div>
                  <p className="text-sm font-medium text-gray-900">{source.url}</p>
                  <p className="text-sm text-gray-500">
                    {source.article_count} articles • Last updated: {source.last_processed || 'Never'}
                  </p>
                </div>
                <button
                  onClick={() => handleDelete(source.url)}
                  className="text-red-600 hover:text-red-900"
                  title="Delete feed"
                >
                  <TrashIcon className="h-5 w-5" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
