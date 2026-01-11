variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "function_name" {
  description = "Lambda function name"
  type        = string
  default     = "medishield-search-api"
}

variable "api_name" {
  description = "API Gateway name"
  type        = string
  default     = "medishield-search-api"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 256
}

variable "pinecone_api_key" {
  description = "Pinecone API key"
  type        = string
  sensitive   = true
}

variable "pinecone_index_name" {
  description = "Pinecone index name"
  type        = string
  default     = "medishield-pdf-pipeline"
}

variable "google_api_key" {
  description = "Google API key for embeddings"
  type        = string
  sensitive   = true
}
