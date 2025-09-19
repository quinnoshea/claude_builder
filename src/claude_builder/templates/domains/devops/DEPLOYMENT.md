# DevOps: Deployment Guidance

{% set kube = dev_environment.tools.get('kubernetes') %}
{% if kube %}

## Kubernetes Deployments

**Detected Tool:** {{ kube.display_name }} (Confidence: {{ kube.confidence|capitalize }})
{% if kube.score is not none %}_Detection score: {{ '%.1f'|format(kube.score) }}_{% endif %}

We've detected Kubernetes configuration files, suggesting you are deploying
your application to a Kubernetes cluster.

**Key Files Detected:**

```text
{% for file in kube.files %}
- {{ file }}
{% endfor %}
{% if kube.files|length == 0 %}
(no representative files captured yet)
{% endif %}
```

{% if kube.recommendations %}
**Actionable Recommendations:**

{% for rec in kube.recommendations %}- {{ rec }}
{% endfor %}

{% else %}
**Actionable Recommendations:**

- Use Helm or Kustomize to manage complex deployments consistently.
- Define resource requests/limits and liveness/readiness probes for each pod.
- Apply strict RBAC roles and Pod Security admission policies to harden clusters.

{% endif %}

{% endif %}

{% set helm = dev_environment.tools.get('helm') %}
{% if helm %}

## Helm Chart for Kubernetes

**Detected Tool:** {{ helm.display_name }} (Confidence: {{ helm.confidence|capitalize }})
{% if helm.score is not none %}_Detection score: {{ '%.1f'|format(helm.score) }}_{% endif %}

We've detected a Helm chart, which is a great way to package and deploy your
application on Kubernetes.

**Key Files Detected:**

```text
{% for file in helm.files %}
- {{ file }}
{% endfor %}
{% if helm.files|length == 0 %}
(no representative files captured yet)
{% endif %}
```

{% if helm.recommendations %}
**Actionable Recommendations:**

{% for rec in helm.recommendations %}- {{ rec }}
{% endfor %}

{% else %}
**Actionable Recommendations:**

- Run `helm lint` and chart unit tests before publishing new releases.
- Parameterise values per environment and store them in source control.
- Integrate secret management (e.g. SOPS, External Secrets) instead of plaintext values.

{% endif %}

{% endif %}
