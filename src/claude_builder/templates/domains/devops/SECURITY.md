# DevOps: Security Guidance

{% set vault_tool = dev_environment.tools.get('vault') %}
{% if vault_tool %}

## {{ vault_tool.display_name }} for Secrets Management

**Detected Tool:** {{ vault_tool.display_name }} (Confidence: {{ vault_tool.confidence|capitalize }})
{% if vault_tool.score is not none %}_Detection score: {{ '%.1f'|format(vault_tool.score) }}_{% endif %}

Vault helps manage secrets and protect sensitive data.

{% if vault_tool.recommendations %}
**Actionable Recommendations:**

{% for rec in vault_tool.recommendations %}- {{ rec }}
{% endfor %}

{% endif %}

{% endif %}

{% set tfsec_tool = dev_environment.tools.get('tfsec') %}
{% if tfsec_tool %}

## {{ tfsec_tool.display_name }} for Terraform Security

**Detected Tool:** {{ tfsec_tool.display_name }} (Confidence: {{ tfsec_tool.confidence|capitalize }})
{% if tfsec_tool.score is not none %}_Detection score: {{ '%.1f'|format(tfsec_tool.score) }}_{% endif %}

{% if tfsec_tool.recommendations %}
**Actionable Recommendations:**

{% for rec in tfsec_tool.recommendations %}- {{ rec }}
{% endfor %}

{% else %}
**Actionable Recommendations:**

- Run `tfsec` in CI to scan every pull request.
- Tune policies via configuration files to reduce false positives.
- Keep `tfsec` updated to benefit from new rules.

{% endif %}

{% endif %}

{% set trivy_tool = dev_environment.tools.get('trivy') %}
{% if trivy_tool %}

## {{ trivy_tool.display_name }} for Vulnerability Scanning

**Detected Tool:** {{ trivy_tool.display_name }} (Confidence: {{ trivy_tool.confidence|capitalize }})
{% if trivy_tool.score is not none %}_Detection score: {{ '%.1f'|format(trivy_tool.score) }}_{% endif %}

{% if trivy_tool.recommendations %}
**Actionable Recommendations:**

{% for rec in trivy_tool.recommendations %}- {{ rec }}
{% endfor %}

{% else %}
**Actionable Recommendations:**

- Scan container images before pushing to registries and block failing builds.
- Use `.trivyignore` to suppress noisy findings while tracking rationale in code review.
- Schedule regular filesystem and dependency scans to catch CVEs early.

{% endif %}

{% endif %}
