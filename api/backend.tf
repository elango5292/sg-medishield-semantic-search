# Terraform backend configuration
# Uncomment and configure for remote state

terraform {
  backend "s3" {
    bucket         = "tform-storage"
    key            = "medishield-api/terraform.tfstate"
    region         = "us-east-1"
  }
}
