{%- import '_macros.md' as macros -%}
# DevOps: Security Guidance

{% set vault_tool = dev_environment.tools.get('vault') %}
{% if vault_tool %}

## {{ vault_tool.display_name }} for Secrets Management

{{ macros.tool_header(vault_tool) }}

Vault helps manage secrets and protect sensitive data.

{% if vault_tool.recommendations %}
{{ macros.recommendations(vault_tool.recommendations) }}

{% endif %}

{% endif %}

{% set tfsec_tool = dev_environment.tools.get('tfsec') %}
{% if tfsec_tool %}

## {{ tfsec_tool.display_name }} for Terraform Security

{{ macros.tool_header(tfsec_tool) }}

{{ macros.recommendations(tfsec_tool.recommendations, [
  'Run `tfsec` in CI to scan every pull request.',
  'Tune policies via configuration files to reduce false positives.',
  'Keep `tfsec` updated to benefit from new rules.'
]) }}

{% endif %}

{% set trivy_tool = dev_environment.tools.get('trivy') %}
{% if trivy_tool %}

## {{ trivy_tool.display_name }} for Vulnerability Scanning

{{ macros.tool_header(trivy_tool) }}

{{ macros.recommendations(trivy_tool.recommendations, [
  'Scan container images before pushing to registries; block failures.',
  'Use `.trivyignore` to suppress noise; track rationale in code review.',
  'Schedule regular filesystem and dependency scans to catch CVEs early.'
]) }}

{% endif %}
