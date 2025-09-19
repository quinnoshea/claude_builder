# MLOps: Lifecycle Guidance

{% set mlflow_tool = dev_environment.tools.get('mlflow') %}
{% if mlflow_tool %}

## {{ mlflow_tool.display_name }} for MLOps

**Detected Tool:** {{ mlflow_tool.display_name }} (Confidence:
{{ mlflow_tool.confidence|capitalize }})
{% if mlflow_tool.score is not none %}_Detection score:
{{ '%.1f'|format(mlflow_tool.score) }}_{% endif %}

MLflow manages the end-to-end machine learning lifecycle.

**Key Files Detected:**

```text
{% for file in mlflow_tool.files %}
- {{ file }}
{% endfor %}
{% if mlflow_tool.files|length == 0 %}
(no representative files captured yet)
{% endif %}
```

{% if mlflow_tool.recommendations %}
**Actionable Recommendations:**

{% for rec in mlflow_tool.recommendations %}- {{ rec }}
{% endfor %}

{% endif %}

{% endif %}

{% set kubeflow_tool = dev_environment.tools.get('kubeflow') %}
{% if kubeflow_tool %}

## {{ kubeflow_tool.display_name }} for MLOps on Kubernetes

**Detected Tool:** {{ kubeflow_tool.display_name }} (Confidence:
{{ kubeflow_tool.confidence|capitalize }})
{% if kubeflow_tool.score is not none %}_Detection score:
{{ '%.1f'|format(kubeflow_tool.score) }}_{% endif %}

{% if kubeflow_tool.recommendations %}
**Actionable Recommendations:**

{% for rec in kubeflow_tool.recommendations %}- {{ rec }}
{% endfor %}

{% endif %}

{% endif %}
