# DevOps: Infrastructure Guidance

{% set tool = dev_environment.tools.get('terraform') %}
{% if tool %}

## Infrastructure as Code (IaC) with Terraform

**Detected Tool:** {{ tool.display_name }} (Confidence: {{ tool.confidence|capitalize }})
{% if tool.score is not none %}_Detection score: {{ '%.1f'|format(tool.score) }}_{% endif %}

Your project appears to use Terraform for managing infrastructure as code. This
helps ensure infrastructure is reproducible, versionable, and scalable.

**Key Files Detected:**

```text
{% for file in tool.files %}
- {{ file }}
{% endfor %}
{% if tool.files|length == 0 %}
(no representative files captured yet)
{% endif %}
```

{% if tool.recommendations %}
**Actionable Recommendations:**

{% for rec in tool.recommendations %}- {{ rec }}
{% endfor %}

{% else %}
**Actionable Recommendations:**

- Standardise modules to enforce consistency across stacks.
- Store state in a secure remote backend (Terraform Cloud, S3 + DynamoDB, etc.).
- Enforce `terraform fmt`/`terraform validate` and plan scans (`tfsec`, `checkov`) in CI.

{% endif %}

{% endif %}
