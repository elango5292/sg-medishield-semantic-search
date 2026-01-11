import { useState } from 'react';
import AppLayout from '@cloudscape-design/components/app-layout';
import ContentLayout from '@cloudscape-design/components/content-layout';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Grid from '@cloudscape-design/components/grid';
import Container from '@cloudscape-design/components/container';
import Input from '@cloudscape-design/components/input';
import Button from '@cloudscape-design/components/button';
import Cards from '@cloudscape-design/components/cards';
import Box from '@cloudscape-design/components/box';
import Badge from '@cloudscape-design/components/badge';
import Link from '@cloudscape-design/components/link';
import Alert from '@cloudscape-design/components/alert';
import Spinner from '@cloudscape-design/components/spinner';
import { PDFViewer } from './components/PDFViewer';
import { searchDocuments } from './api';
import type { SearchResult } from './types';

const PDF_URL = import.meta.env.VITE_PDF_URL || './medishield.pdf';

const EXAMPLE_QUERIES = [
  'What is MediShield Life?',
  'How much can I claim for surgery?',
  'Pre-existing conditions coverage',
  'Premium rates by age',
  'What is the deductible?',
  'How to make a claim?',
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
    <AppLayout
      navigationHide
      toolsHide
      content={
        <ContentLayout
          header={
            <Header
              variant="h1"
              description="Search MediShield Life policy documents using natural language"
              actions={
                <Link
                  href="https://www.moh.gov.sg/medishield-life"
                  external
                  variant="primary"
                >
                  Official MOH Website
                </Link>
              }
            >
              MediShield Life Document Search
            </Header>
          }
        >
          <SpaceBetween size="l">
            <Container>
              <SpaceBetween size="m">
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
                  >
                    Search
                  </Button>
                </div>

                <SpaceBetween size="xs" direction="horizontal">
                  <Box variant="span" color="text-body-secondary">
                    Try:
                  </Box>
                  {EXAMPLE_QUERIES.map((example) => (
                    <Button
                      key={example}
                      variant="link"
                      onClick={() => handleSearch(example)}
                    >
                      {example}
                    </Button>
                  ))}
                </SpaceBetween>
              </SpaceBetween>
            </Container>

            {error && (
              <Alert type="error" dismissible onDismiss={() => setError(null)}>
                {error}
              </Alert>
            )}

            <Grid gridDefinition={[{ colspan: 4 }, { colspan: 8 }]}>
              <Container
                header={
                  <Header
                    variant="h2"
                    counter={hasSearched ? `(${results.length})` : undefined}
                  >
                    Results
                  </Header>
                }
              >
                {isLoading ? (
                  <Box textAlign="center" padding="l">
                    <Spinner size="large" />
                  </Box>
                ) : !hasSearched ? (
                  <Box textAlign="center" padding="l" color="text-body-secondary">
                    Enter a query or click an example to search
                  </Box>
                ) : results.length === 0 ? (
                  <Box textAlign="center" padding="l" color="text-body-secondary">
                    No results found. Try a different query.
                  </Box>
                ) : (
                  <Cards
                    items={results}
                    cardDefinition={{
                      header: (item) => (
                        <SpaceBetween size="xs" direction="horizontal">
                          <Badge color="blue">Page {item.page}</Badge>
                          <Badge
                            color={
                              item.score >= 0.7
                                ? 'green'
                                : item.score >= 0.5
                                ? 'grey'
                                : 'red'
                            }
                          >
                            {Math.round(item.score * 100)}% match
                          </Badge>
                        </SpaceBetween>
                      ),
                      sections: [
                        {
                          id: 'text',
                          content: (item) => (
                            <Box
                              variant="p"
                              color={
                                selectedResult?.id === item.id
                                  ? 'text-body-secondary'
                                  : 'text-body-secondary'
                              }
                            >
                              {item.text.length > 200
                                ? item.text.substring(0, 200) + '...'
                                : item.text}
                            </Box>
                          ),
                        },
                      ],
                    }}
                    selectionType="single"
                    selectedItems={selectedResult ? [selectedResult] : []}
                    onSelectionChange={({ detail }) =>
                      setSelectedResult(detail.selectedItems[0] || null)
                    }
                    trackBy="id"
                    empty={
                      <Box textAlign="center" color="inherit">
                        No results
                      </Box>
                    }
                  />
                )}
              </Container>

              <Container
                header={<Header variant="h2">Document Viewer</Header>}
                fitHeight
              >
                <div style={{ height: '600px' }}>
                  <PDFViewer pdfUrl={PDF_URL} selectedResult={selectedResult} />
                </div>
              </Container>
            </Grid>

            <Box textAlign="center" color="text-body-secondary" fontSize="body-s">
              This is a demonstration tool. For official information, visit the{' '}
              <Link href="https://www.moh.gov.sg/medishield-life" external>
                Ministry of Health website
              </Link>
              .
            </Box>
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}

export default App;
