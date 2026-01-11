terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "lambda_layer" {
  source = "./modules/lambda_layer"

  layer_name = "${var.function_name}-deps"
}

module "lambda" {
  source = "./modules/lambda"

  function_name = var.function_name
  layer_arn     = module.lambda_layer.layer_arn
  runtime       = "python3.12"
  handler       = "handler.lambda_handler"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  environment_variables = {
    PINECONE_API_KEY    = var.pinecone_api_key
    PINECONE_INDEX_NAME = var.pinecone_index_name
    GOOGLE_API_KEY      = var.google_api_key
  }
}

module "api_gateway" {
  source = "./modules/api_gateway"

  api_name             = var.api_name
  lambda_invoke_arn    = module.lambda.invoke_arn
  lambda_function_name = module.lambda.function_name
}
