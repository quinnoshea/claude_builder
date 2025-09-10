# MLOps: Lifecycle Guidance

{% if dev_environment.tools.mlflow %}

## MLflow for MLOps

**Detected Tool:** MLflow (Confidence:
{{ dev_environment.tools.mlflow.confidence }})

MLflow manages the end‑to‑end machine learning lifecycle.

**Key Files Detected:**

```text
{% for file in dev_environment.tools.mlflow.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1. **Use a Tracking Server:** For collaboration, set up a central Tracking
   Server to log and compare experiments.
2. **Log Artifacts:** Log models, data, and images in addition to metrics and
   parameters to ensure reproducibility.
3. **Model Registry:** Manage lifecycle from staging to production with the
   Model Registry.

{% endif %}

{% if dev_environment.tools.kubeflow %}

## Kubeflow for MLOps on Kubernetes

**Detected Tool:** Kubeflow (Confidence:
{{ dev_environment.tools.kubeflow.confidence }})

Kubeflow helps deploy and manage ML workflows on Kubernetes.

**Next Steps & Best Practices:**

1. **Pipelines:** Define ML workflows as pipelines to make them reproducible
   and scalable.
2. **Components:** Create reusable components to share workflow building
   blocks.
3. **Katib:** Use Katib for automated hyperparameter tuning.

{% endif %}
