import { useState } from 'react';
import TopNavigation from '@cloudscape-design/components/top-navigation';
import SplitPanel from '@cloudscape-design/components/split-panel';
import AppLayout from '@cloudscape-design/components/app-layout';
import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import Input from '@cloudscape-design/components/input';
import Button from '@cloudscape-design/components/button';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import Badge from '@cloudscape-design/components/badge';
import Link from '@cloudscape-design/components/link';
import Alert from '@cloudscape-design/components/alert';
import Spinner from '@cloudscape-design/components/spinner';
import ColumnLayout from '@cloudscape-design/components/column-layout';
import { PDFViewer } from './components/PDFViewer';
import { searchDocuments } from './api';
import type { SearchResult } from './types';

const PDF_URL = import.meta.env.VITE_PDF_URL || './medishield.pdf';

const EXAMPLE_QUERIES = [
  { label: 'What is MediShield Life?', icon: '📋' },
  { label: 'Surgery claim limits', icon: '🏥' },
  { label: 'Pre-existing conditions', icon: '📝' },
  { label: 'Premium by age', icon: '💰' },
  { label: 'Deductible amount', icon: '🧾' },
  { label: 'How to claim', icon: '📤' },
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
      setError('Failed to search. Please check your connection and try again.');
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch(query);
    }
  };

  return (
    <>
      <TopNavigation
        identity={{
          href: '#',
          title: 'MediShield Life',
          logo: {
            src: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23fff"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 3c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm7 13H5v-.23c0-.62.28-1.2.76-1.58C7.47 15.82 9.64 15 12 15s4.53.82 6.24 2.19c.48.38.76.97.76 1.58V19z"/></svg>',
            alt: 'MediShield Life',
          },
        }}
        utilities={[
          {
            type: 'button',
            text: 'Official MOH Website',
            href: 'https://www.moh.gov.sg/medishield-life',
            external: true,
            externalIconAriaLabel: 'Opens in a new tab',
          },
        ]}
      />

      <AppLayout
        navigationHide
        toolsHide
        contentType="default"
        splitPanel={
          <SplitPanel
            header="Document Viewer"
            hidePreferencesButton
            closeBehavior="hide"
          >
            <div style={{ height: 'calc(100vh - 280px)', minHeight: '500px' }}>
              <PDFViewer pdfUrl={PDF_URL} selectedResult={selectedResult} />
            </div>
          </SplitPanel>
        }
        splitPanelOpen={true}
        splitPanelPreferences={{ position: 'side' }}
        splitPanelSize={700}
        content={
          <SpaceBetween size="l">
            <Container>
              <SpaceBetween size="m">
                <Header
                  variant="h1"
                  description="Ask questions about coverage, claims, premiums, and more"
                >
                  Document Search
                </Header>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <div style={{ flex: 1 }}>
                    <Input
                      value={query}
                      onChange={({ detail }) => setQuery(detail.value)}
                      onKeyDown={handleKeyDown as never}
                      placeholder="Ask a question about MediShield Life..."
                      type="search"
                    />
                  </div>
                  <Button
                    variant="primary"
                    onClick={() => handleSearch(query)}
                    loading={isLoading}
                    disabled={!query.trim()}
                    iconName="search"
                  >
                    Search
                  </Button>
                </div>

                <ColumnLayout columns={3} variant="text-grid">
                  {EXAMPLE_QUERIES.map((example) => (
                    <div
                      key={example.label}
                      onClick={() => handleSearch(example.label)}
                      style={{
                        padding: '12px',
                        border: '1px solid #e9ebed',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        transition: 'all 0.15s',
                        backgroundColor: '#fff',
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.borderColor = '#0972d3';
                        e.currentTarget.style.backgroundColor = '#f2f8fd';
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.borderColor = '#e9ebed';
                        e.currentTarget.style.backgroundColor = '#fff';
                      }}
                    >
                      <SpaceBetween size="xxs">
                        <span style={{ fontSize: '20px' }}>{example.icon}</span>
                        <Box variant="span" fontSize="body-s">
                          {example.label}
                        </Box>
                      </SpaceBetween>
                    </div>
                  ))}
                </ColumnLayout>
              </SpaceBetween>
            </Container>

            {error && (
              <Alert type="error" dismissible onDismiss={() => setError(null)}>
                {error}
              </Alert>
            )}

            <Container
              header={
                <Header
                  variant="h2"
                  counter={hasSearched ? `(${results.length})` : undefined}
                  description={
                    hasSearched && results.length > 0
                      ? 'Click a result to view it in the document'
                      : undefined
                  }
                >
                  Search Results
                </Header>
              }
            >
              {isLoading ? (
                <Box textAlign="center" padding="l">
                  <SpaceBetween size="s" alignItems="center">
                    <Spinner size="large" />
                    <Box color="text-body-secondary">Searching documents...</Box>
                  </SpaceBetween>
                </Box>
              ) : !hasSearched ? (
                <Box textAlign="center" padding="l" color="text-body-secondary">
                  <SpaceBetween size="s">
                    <Box variant="h3" color="text-body-secondary">
                      👆
                    </Box>
                    <Box>Enter a query or click an example above to get started</Box>
                  </SpaceBetween>
                </Box>
              ) : results.length === 0 ? (
                <Box textAlign="center" padding="l" color="text-body-secondary">
                  No results found. Try a different query.
                </Box>
              ) : (
                <SpaceBetween size="s">
                  {results.map((result, index) => (
                    <div
                      key={result.id}
                      onClick={() => setSelectedResult(result)}
                      style={{
                        padding: '16px',
                        border:
                          selectedResult?.id === result.id
                            ? '2px solid #0972d3'
                            : '1px solid #e9ebed',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        backgroundColor:
                          selectedResult?.id === result.id ? '#f2f8fd' : '#fff',
                        transition: 'all 0.15s',
                      }}
                    >
                      <SpaceBetween size="xs">
                        <SpaceBetween size="xs" direction="horizontal">
                          <Badge color="blue">#{index + 1}</Badge>
                          <Badge color="grey">Page {result.page}</Badge>
                          <Badge
                            color={
                              result.score >= 0.7
                                ? 'green'
                                : result.score >= 0.5
                                ? 'grey'
                                : 'red'
                            }
                          >
                            {Math.round(result.score * 100)}% relevance
                          </Badge>
                        </SpaceBetween>
                        <Box variant="p">{result.text}</Box>
                      </SpaceBetween>
                    </div>
                  ))}
                </SpaceBetween>
              )}
            </Container>

            <Box textAlign="center" color="text-body-secondary" fontSize="body-s">
              This is a demonstration tool. For official information, visit the{' '}
              <Link href="https://www.moh.gov.sg/medishield-life" external>
                Ministry of Health website
              </Link>
              .
            </Box>
          </SpaceBetween>
        }
      />
    </>
  );
}

export default App;
