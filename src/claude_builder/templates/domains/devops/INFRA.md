# DevOps: Infrastructure Guidance

{% if dev_environment.tools.terraform %}

### Infrastructure as Code (IaC) with Terraform

**Detected Tool:** Terraform (Confidence:
{{ dev_environment.tools.terraform.confidence }})

Your project appears to use Terraform for managing infrastructure as code. This
helps ensure infrastructure is reproducible, versionable, and scalable.

**Key Files Detected:**

```text
{% for file in dev_environment.tools.terraform.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1. **Standardize Modules:** If you have multiple configurations, create
   reusable modules to enforce consistency and reduce duplication.
2. **State Management:** Store state in a secure, remote backend (for example
   S3, Azure Blob, or Terraform Cloud), not locally. This is critical for team
   collaboration.
3. **Linting and Formatting:** Use `terraform fmt -recursive` for formatting and
   `tflint` to catch common errors and enforce best practices.
4. **Security:** Scan plans with `tfsec` or `checkov` before applying changes.

**Example Command:**

```bash
# Run a security scan on your Terraform code
tfsec .
```

{% endif %}
