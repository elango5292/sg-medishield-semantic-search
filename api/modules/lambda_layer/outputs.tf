output "layer_arn" {
  description = "ARN of the Lambda layer"
  value       = aws_lambda_layer_version.deps.arn
}
