import { useState } from 'react';
import { SearchBar } from './components/SearchBar';
import { ResultCard } from './components/ResultCard';
import { PDFViewer } from './components/PDFViewer';
import { searchDocuments } from './api';
import type { SearchResult } from './types';

const PDF_URL = import.meta.env.VITE_PDF_URL || './medishield.pdf';

function App() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (query: string) => {
    setIsLoading(true);
    setError(null);
    setHasSearched(true);
    
    try {
      const response = await searchDocuments(query);
      setResults(response.results);
      setSelectedResult(response.results[0] || null);
    } catch {
      setError('Failed to search. Please check your connection and try again.');
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-900">MediShield Life</h1>
              <p className="text-xs text-slate-500">Document Search</p>
            </div>
          </div>
          <a 
            href="https://www.moh.gov.sg/medishield-life" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-sm text-slate-500 hover:text-blue-600 transition-colors"
          >
            Official MOH Website →
          </a>
        </div>
      </header>

      <main className="flex-1 flex flex-col lg:flex-row">
        <aside className="w-full lg:w-96 bg-white border-r border-slate-200 flex flex-col">
          <div className="p-4 border-b border-slate-200">
            <SearchBar onSearch={handleSearch} isLoading={isLoading} />
          </div>
          
          <div className="flex-1 overflow-auto p-4">
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 mb-4">
                {error}
              </div>
            )}
            
            {!hasSearched && (
              <div className="text-center py-8">
                <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <p className="text-sm text-slate-500">
                  Search for information about MediShield Life coverage, claims, premiums, and more.
                </p>
              </div>
            )}

            {hasSearched && results.length === 0 && !isLoading && !error && (
              <div className="text-center py-8">
                <p className="text-sm text-slate-500">No results found. Try a different query.</p>
              </div>
            )}

            <div className="space-y-3">
              {results.map((result) => (
                <ResultCard
                  key={result.id}
                  result={result}
                  isSelected={selectedResult?.id === result.id}
                  onClick={() => setSelectedResult(result)}
                />
              ))}
            </div>
          </div>
        </aside>

        <section className="flex-1 p-4 min-h-[500px] lg:min-h-0">
          <PDFViewer pdfUrl={PDF_URL} selectedResult={selectedResult} />
        </section>
      </main>

      <footer className="bg-white border-t border-slate-200 px-6 py-3">
        <p className="text-xs text-slate-400 text-center">
          This is a demonstration tool. For official information, visit the Ministry of Health website.
        </p>
      </footer>
    </div>
  );
}

export default App;
