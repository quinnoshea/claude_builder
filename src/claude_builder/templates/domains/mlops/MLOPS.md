{% if dev_environment.tools.mlflow %}
### MLflow for MLOps

**Detected Tool:** MLflow (Confidence: {{ dev_environment.tools.mlflow.confidence }})

MLflow usage has been detected. MLflow is a great open-source platform for managing the end-to-end machine learning lifecycle.

**Key Files Detected:**
```
{% for file in dev_environment.tools.mlflow.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1.  **Use a Tracking Server:** For collaborative projects, set up a central MLflow Tracking Server to log and compare experiments.
2.  **Log Artifacts:** In addition to metrics and parameters, log artifacts such as models, data files, and images to ensure reproducibility.
3.  **Model Registry:** Use the MLflow Model Registry to manage your model's lifecycle from staging to production.

{% endif %}

{% if dev_environment.tools.kubeflow %}
### Kubeflow for MLOps on Kubernetes

**Detected Tool:** Kubeflow (Confidence: {{ dev_environment.tools.kubeflow.confidence }})

We've detected Kubeflow configuration files. Kubeflow is a powerful platform for deploying and managing machine learning workflows on Kubernetes.

**Next Steps & Best Practices:**

1.  **Use Pipelines:** Define your ML workflows as pipelines to make them reproducible, scalable, and easy to manage.
2.  **Leverage Components:** Create reusable components to share and reuse parts of your ML workflows.
3.  **Katib for Hyperparameter Tuning:** Use Katib to automate hyperparameter tuning and find the best model for your problem.

{% endif %}

