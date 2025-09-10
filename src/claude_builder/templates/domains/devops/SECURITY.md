# DevOps: Security Guidance

{% if dev_environment.tools.vault %}

### HashiCorp Vault for Secrets Management

**Detected Tool:** Vault (Confidence:
{{ dev_environment.tools.vault.confidence }})

Vault helps manage secrets and protect sensitive data.

**Next Steps & Best Practices:**

1. **Use Dynamic Secrets:** Prefer dynamic credentials to reduce the risk of
   leaked static secrets.
2. **Audit Trails:** Enable audit devices to maintain detailed logs of all
   requests and responses to Vault.
3. **Fine-Grained Policies:** Implement policies to ensure apps and users only
   access what they need.

{% endif %}

{% if dev_environment.tools.tfsec %}

### tfsec for Terraform Security

**Detected Tool:** tfsec (Confidence:
{{ dev_environment.tools.tfsec.confidence }})

tfsec scans Terraform code for security issues.

**Next Steps & Best Practices:**

1. **CI/CD Integration:** Run `tfsec` in CI to scan every pull request.
2. **Customize Policies:** Adjust checks via a configuration file when needed.
3. **Stay Updated:** Keep `tfsec` current to benefit from new rules.

{% endif %}

{% if dev_environment.tools.trivy %}

### Trivy for Vulnerability Scanning

**Detected Tool:** Trivy (Confidence:
{{ dev_environment.tools.trivy.confidence }})

Trivy scans container images and filesystems for vulnerabilities.

**Next Steps & Best Practices:**

1. **Scan in CI/CD:** Scan images before pushing to a registry.
2. **Scan Filesystems and Repos:** Use Trivy on app files and dependencies.
3. **Filter Noise:** Use `.trivyignore` for irrelevant findings.

{% endif %}
