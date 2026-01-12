# MediShield Life Explorer

![Preview](preview.png)

Semantic search interface for Singapore's MediShield Life policy document. Ask natural language questions and get relevant sections highlighted directly in the PDF.

**[Try it live →](https://elango5292.github.io/sg-medishield-semantic-search/)**

## How it works

1. PDF content is extracted and chunked with coordinate metadata
2. Chunks are embedded using Google's Gemini embedding model
3. Embeddings are indexed in Pinecone for vector similarity search
4. User queries are embedded and matched against the index
5. Results are displayed with the relevant section highlighted in the PDF viewer

## Tech Stack

- **Frontend**: React + Vite + Cloudscape Design System
- **Embeddings**: Google Gemini
- **Vector DB**: Pinecone
- **Backend**: AWS Lambda + API Gateway (Terraform)
- **PDF Processing**: Custom Python pipeline

## Project Structure

```
├── frontend/          # React app with PDF viewer and search UI
├── api/               # Terraform infrastructure for Lambda API
├── pdf_pipeline/      # Python scripts for PDF extraction & embedding
└── data/              # Source PDF document
```

## Local Development

```bash
cd frontend
npm install
npm run dev
```

## Deployment

```bash
cd frontend
npm run deploy
```

This builds and pushes to the `gh-pages` branch.
