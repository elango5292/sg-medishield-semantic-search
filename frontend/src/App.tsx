import { useState, useEffect } from 'react';
import TopNavigation from '@cloudscape-design/components/top-navigation';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import Badge from '@cloudscape-design/components/badge';
import Alert from '@cloudscape-design/components/alert';
import Spinner from '@cloudscape-design/components/spinner';
import Input from '@cloudscape-design/components/input';
import Button from '@cloudscape-design/components/button';
import { PDFViewer } from './components/PDFViewer';
import { searchDocuments } from './api';
import type { SearchResult } from './types';

const PDF_URL = import.meta.env.VITE_PDF_URL || './medishield.pdf';

const EXAMPLE_QUERIES = [
  'What is MediShield Life?',
  'Surgery claim limits',
  'Pre-existing conditions',
  'Premium by age',
];

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;

    setQuery(searchQuery);
    setIsLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const response = await searchDocuments(searchQuery);
      setResults(response.results);
      setSelectedResult(response.results[0] || null);
    } catch {
      setError('Search failed. Please try again.');
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Run default query on first load
  useEffect(() => {
    handleSearch('What happens if I can\'t afford my premiums?');
  }, []);

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <TopNavigation
        identity={{
          href: '#',
          title: 'MediShield Life Explorer',
        }}
        utilities={[
          {
            type: 'button',
            text: 'GitHub',
            href: 'https://github.com/elango5292/sg-medishield-semantic-search',
            external: true,
          },
        ]}
      />

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* PDF Viewer - Main Area */}
        <div style={{ flex: 1, backgroundColor: '#232f3e' }}>
          <PDFViewer pdfUrl={PDF_URL} selectedResult={selectedResult} />
        </div>

        {/* Search Sidebar */}
        <div
          style={{
            width: '380px',
            borderLeft: '1px solid #e9ebed',
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: '#fff',
          }}
        >
          {/* Search Input */}
          <div style={{ padding: '16px', borderBottom: '1px solid #e9ebed' }}>
            <SpaceBetween size="s">
              <div style={{ display: 'flex', gap: '8px' }}>
                <div style={{ flex: 1 }}>
                  <Input
                    value={query}
                    onChange={({ detail }) => setQuery(detail.value)}
                    onKeyDown={(e) => {
                      if ((e as unknown as KeyboardEvent).key === 'Enter') handleSearch(query);
                    }}
                    placeholder="Ask a question..."
                    type="search"
                  />
                </div>
                <Button
                  variant="primary"
                  onClick={() => handleSearch(query)}
                  loading={isLoading}
                  disabled={!query.trim()}
                  iconName="search"
                />
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {EXAMPLE_QUERIES.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSearch(q)}
                    style={{
                      padding: '4px 10px',
                      fontSize: '12px',
                      border: '1px solid #e9ebed',
                      borderRadius: '12px',
                      backgroundColor: '#fafafa',
                      cursor: 'pointer',
                      color: '#545b64',
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </SpaceBetween>
          </div>

          {/* Results */}
          <div style={{ flex: 1, overflow: 'auto', padding: '12px' }}>
            {error && (
              <Alert type="error" dismissible onDismiss={() => setError(null)}>
                {error}
              </Alert>
            )}

            {isLoading ? (
              <Box textAlign="center" padding="l">
                <Spinner />
              </Box>
            ) : !hasSearched ? (
              <Box textAlign="center" padding="l" color="text-body-secondary" fontSize="body-s">
                Search to find relevant sections in the document
              </Box>
            ) : results.length === 0 ? (
              <Box textAlign="center" padding="l" color="text-body-secondary">
                No results found
              </Box>
            ) : (
              <SpaceBetween size="xs">
                <Box color="text-body-secondary" fontSize="body-s">
                  {results.length} results found
                </Box>
                {results.map((result, index) => (
                  <div
                    key={result.id}
                    onClick={() => setSelectedResult(result)}
                    style={{
                      padding: '12px',
                      border: selectedResult?.id === result.id
                        ? '2px solid #0972d3'
                        : '1px solid #e9ebed',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      backgroundColor: selectedResult?.id === result.id ? '#f2f8fd' : '#fff',
                    }}
                  >
                    <SpaceBetween size="xxs">
                      <SpaceBetween size="xxs" direction="horizontal">
                        <Badge color="blue">#{index + 1}</Badge>
                        <Badge color="grey">p.{result.page}</Badge>
                        <Badge color={result.score >= 0.7 ? 'green' : 'grey'}>
                          {Math.round(result.score * 100)}%
                        </Badge>
                      </SpaceBetween>
                      <Box fontSize="body-s" color="text-body-secondary">
                        {result.text.length > 150
                          ? result.text.substring(0, 150) + '...'
                          : result.text}
                      </Box>
                    </SpaceBetween>
                  </div>
                ))}
              </SpaceBetween>
            )}
          </div>

          {/* Footer */}
          <div
            style={{
              padding: '12px',
              borderTop: '1px solid #e9ebed',
              backgroundColor: '#fafafa',
            }}
          >
            <Box fontSize="body-s" color="text-body-secondary" textAlign="center">
              Powered by Gemini Embeddings & Pinecone
            </Box>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
