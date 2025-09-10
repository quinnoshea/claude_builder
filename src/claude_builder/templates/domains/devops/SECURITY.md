{% if dev_environment.tools.vault %}
### HashiCorp Vault for Secrets Management

**Detected Tool:** Vault (Confidence: {{ dev_environment.tools.vault.confidence }})

We've detected usage of HashiCorp Vault, which is an excellent choice for managing secrets and protecting sensitive data.

**Next Steps & Best Practices:**

1.  **Use Dynamic Secrets:** Whenever possible, use Vault's dynamic secrets to generate credentials on-demand. This reduces the risk of leaked static secrets.
2.  **Audit Trails:** Ensure that you have enabled audit devices to maintain a detailed log of all requests and responses to Vault.
3.  **Fine-Grained Policies:** Implement fine-grained access control policies to ensure that applications and users only have access to the secrets they need.

{% endif %}

{% if dev_environment.tools.tfsec %}
### tfsec for Terraform Security

**Detected Tool:** tfsec (Confidence: {{ dev_environment.tools.tfsec.confidence }})

tfsec is being used to scan your Terraform code for security vulnerabilities. This is a great way to shift security left and catch issues early.

**Next Steps & Best Practices:**

1.  **Integrate into CI/CD:** Run `tfsec` as a step in your CI/CD pipeline to automatically scan every pull request.
2.  **Customize Policies:** If needed, you can customize the checks that `tfsec` performs by using a custom configuration file.
3.  **Regularly Update:** Keep `tfsec` updated to the latest version to benefit from new checks and security vulnerability disclosures.

{% endif %}

{% if dev_environment.tools.trivy %}
### Trivy for Vulnerability Scanning

**Detected Tool:** Trivy (Confidence: {{ dev_environment.tools.trivy.confidence }})

Trivy is being used for vulnerability scanning. This is a crucial step in securing your container images and other artifacts.

**Next Steps & Best Practices:**

1.  **Scan in CI/CD:** Integrate Trivy into your CI/CD pipeline to scan your container images before they are pushed to a registry.
2.  **Scan Filesystems and Git Repositories:** In addition to container images, you can use Trivy to scan your application's filesystem and Git repository for vulnerabilities in your dependencies.
3.  **Filter Vulnerabilities:** Use a `.trivyignore` file to filter out vulnerabilities that are not relevant to your project.

{% endif %}

