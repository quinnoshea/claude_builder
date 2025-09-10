# DevOps: Deployment Guidance

{% if dev_environment.tools.kubernetes %}

## Kubernetes Deployments

**Detected Tool:** Kubernetes (Confidence:
{{ dev_environment.tools.kubernetes.confidence }})

We've detected Kubernetes configuration files, suggesting you are deploying
your application to a Kubernetes cluster.

**Key Files Detected:**

```text
{% for file in dev_environment.tools.kubernetes.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1. **Use a Package Manager:** For complex applications, consider using a
   package manager like Helm to manage your Kubernetes resources.
2. **Resource Management:** Define resource requests and limits for your
   containers to ensure stable performance and prevent resource contention.
3. **Health Probes:** Implement readiness and liveness probes so Kubernetes
   can manage your application's lifecycle effectively.
4. **Security Context:** Configure a security context for pods and containers
   to restrict permissions and enhance security.

{% endif %}

{% if dev_environment.tools.helm %}

## Helm Chart for Kubernetes

**Detected Tool:** Helm (Confidence:
{{ dev_environment.tools.helm.confidence }})

We've detected a Helm chart, which is a great way to package and deploy your
application on Kubernetes.

**Key Files Detected:**

```text
{% for file in dev_environment.tools.helm.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1. **Lint Your Chart:** Always run `helm lint` to catch syntax issues and
   ensure your chart follows best practices.
2. **Use Dependencies:** Manage complex applications with subcharts and
   dependencies in `Chart.yaml`.
3. **Secure Your Secrets:** Avoid plain-text secrets in templates. Prefer a
   secrets management tool like Vault or Kubernetes Secrets.

**Example Command:**

```bash
# Lint your Helm chart
helm lint ./path/to/your/chart
```

{% endif %}
