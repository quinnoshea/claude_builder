# DevOps: Infrastructure Guidance
<!-- markdownlint-disable MD025 -->

## Infrastructure as Code (IaC) with Terraform

**Detected Tool:** Terraform (Confidence: High)
_Detection score: 12.0_
Your project appears to use Terraform for managing infrastructure as code. This
helps ensure infrastructure is reproducible, versionable, and scalable.

**Key Files Detected:**

```text
- terraform/config.yaml
```

**Actionable Recommendations:**

- Introduce workspaces per environment.
- Enable remote state locking.

# DevOps: Deployment Guidance

## Kubernetes Deployments

**Detected Tool:** Kubernetes (Confidence: High)
_Detection score: 12.0_
We've detected Kubernetes configuration files, suggesting you are deploying
your application to a Kubernetes cluster.

**Key Files Detected:**

```text
- k8s/deployment.yaml
```

**Actionable Recommendations:**

- Enable best practices for kubernetes.

## Helm Chart for Kubernetes

**Detected Tool:** Helm (Confidence: High)
_Detection score: 12.0_
We've detected a Helm chart, which is a great way to package and deploy your
application on Kubernetes.

**Key Files Detected:**

```text
- charts/app/Chart.yaml
```

**Actionable Recommendations:**

- Enable best practices for helm.

# DevOps: Observability Guidance

## Prometheus Monitoring

**Detected Tool:** Prometheus (Confidence: High)
_Detection score: 12.0_
Prometheus configuration files were found, indicating you are using it for
monitoring.

**Key Files Detected:**

```text
- observability/prometheus.yml
```

**Actionable Recommendations:**

- Enable best practices for prometheus.

## Grafana Dashboards

**Detected Tool:** Grafana (Confidence: High)
_Detection score: 12.0_
We detected Grafana configurations. Visualizing metrics helps you understand
system behavior.

**Key Files Detected:**

```text
- grafana/dashboards/app.json
```

**Actionable Recommendations:**

- Enable best practices for grafana.

# DevOps: Security Guidance

## HashiCorp Vault for Secrets Management

**Detected Tool:** HashiCorp Vault (Confidence: High)
_Detection score: 12.0_
Vault helps manage secrets and protect sensitive data.

**Actionable Recommendations:**

- Enable best practices for vault.

**Actionable Recommendations:**

- Scan container images before pushing to registries and block failing
  builds.
- Use `.trivyignore` to suppress noisy findings while tracking rationale in
  code review.
- Schedule regular filesystem and dependency scans to catch CVEs early.
