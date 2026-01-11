aws_region          = "us-west-1"
function_name       = "medishield-search-api"
api_name            = "medishield-search-api"
lambda_timeout      = 30
lambda_memory_size  = 256
pinecone_index_name = "medishield-pdf-pipeline"


# Set these via environment variables or terraform.tfvars.local (gitignored)
pinecone_api_key = "***REMOVED***"
google_api_key   = "***REMOVED***"
