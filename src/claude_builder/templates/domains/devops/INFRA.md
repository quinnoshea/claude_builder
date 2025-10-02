{%- import '_macros.md' as macros -%}
# DevOps: Infrastructure Guidance

{% set tool = dev_environment.tools.get('terraform') %}
{% if tool %}

## Infrastructure as Code (IaC) with Terraform

{{ macros.tool_header(tool) }}
Your project appears to use Terraform for managing infrastructure as code. This
helps ensure infrastructure is reproducible, versionable, and scalable.

{% if tool.files and tool.files|length > 0 %}
{{ macros.key_files(tool.files) }}

{% endif %}
{{ macros.recommendations(tool.recommendations, [
  'Standardise modules to enforce consistency across stacks.',
  'Store state in a secure remote backend (Terraform Cloud, S3, DynamoDB).',
  'Enforce `terraform fmt`/`validate` and scans (`tfsec`, `checkov`) in CI.'
]) }}

{% endif %}
