locals {
  layer_dir = "${path.module}/layer"
}

data "external" "pip_install" {
  program = ["bash", "-c", <<-EOT
    set -e
    rm -rf "${local.layer_dir}"
    mkdir -p "${local.layer_dir}/python"
    pip install -r "${path.module}/requirements.txt" -t "${local.layer_dir}/python" --quiet --upgrade --platform manylinux2014_x86_64 --only-binary=:all: >&2
    echo '{"status":"done"}'
  EOT
  ]
}

data "archive_file" "layer_zip" {
  depends_on  = [data.external.pip_install]
  type        = "zip"
  source_dir  = local.layer_dir
  output_path = "${path.module}/layer.zip"
}

resource "aws_lambda_layer_version" "deps" {
  layer_name          = var.layer_name
  filename            = data.archive_file.layer_zip.output_path
  source_code_hash    = data.archive_file.layer_zip.output_base64sha256
  compatible_runtimes = ["python3.12"]
}
