{%- import '../_macros.md' as macros -%}
# MLOps: Lifecycle Guidance

{% set mlflow_tool = dev_environment.tools.get('mlflow') %}
{% if mlflow_tool %}

## {{ mlflow_tool.display_name }} for MLOps

{{ macros.tool_header(mlflow_tool) }}

MLflow manages the end-to-end machine learning lifecycle.

{% if mlflow_tool.files and mlflow_tool.files|length > 0 %}
{{ macros.key_files(mlflow_tool.files) }}

{% endif %}
{% if mlflow_tool.recommendations %}
{{ macros.recommendations(mlflow_tool.recommendations) }}

{% endif %}

{% endif %}

{% set kubeflow_tool = dev_environment.tools.get('kubeflow') %}
{% if kubeflow_tool %}

## {{ kubeflow_tool.display_name }} for MLOps on Kubernetes

{{ macros.tool_header(kubeflow_tool) }}

{% if kubeflow_tool.recommendations %}
{{ macros.recommendations(kubeflow_tool.recommendations) }}

{% endif %}

{% endif %}
