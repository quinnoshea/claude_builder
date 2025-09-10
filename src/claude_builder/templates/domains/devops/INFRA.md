{% if dev_environment.tools.terraform %}
### Infrastructure as Code (IaC) with Terraform

**Detected Tool:** Terraform (Confidence: {{ dev_environment.tools.terraform.confidence }})

Your project appears to use Terraform for managing infrastructure as code. This is a great practice for ensuring your infrastructure is reproducible, versionable, and scalable.

**Key Files Detected:**
```
{% for file in dev_environment.tools.terraform.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1.  **Standardize Your Modules:** If you have multiple Terraform configurations, consider creating reusable modules to enforce consistency and reduce code duplication.
2.  **State Management:** Ensure your Terraform state is stored in a secure, remote backend like AWS S3, Azure Blob Storage, or HashiCorp Consul, rather than in the local filesystem. This is critical for team collaboration.
3.  **Linting and Formatting:** Use `terraform fmt -recursive` to ensure consistent formatting and `tflint` to catch common errors and enforce best practices.
4.  **Security:** Use a tool like `tfsec` or `checkov` to scan your Terraform plans for potential security vulnerabilities before applying them.

**Example Command:**
```bash
# Run a security scan on your Terraform code
tfsec .
```
{% endif %}

