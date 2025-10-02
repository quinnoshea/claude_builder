{%- import '../_macros.md' as macros -%}
# MLOps: Data Pipeline Guidance

{% set airflow_tool = dev_environment.tools.get('airflow') %}
{% if airflow_tool %}

## {{ airflow_tool.display_name }} for Data Pipelines

{{ macros.tool_header(airflow_tool) }}

Airflow is a platform for authoring, scheduling, and monitoring workflows.

{% if airflow_tool.files and airflow_tool.files|length > 0 %}
{{ macros.key_files(airflow_tool.files) }}

{% endif %}
{% if airflow_tool.recommendations %}
{{ macros.recommendations(airflow_tool.recommendations) }}

{% endif %}

{% endif %}

{% set prefect_tool = dev_environment.tools.get('prefect') %}
{% if prefect_tool %}

## {{ prefect_tool.display_name }} for Data Pipelines

{{ macros.tool_header(prefect_tool) }}

{% if prefect_tool.recommendations %}
{{ macros.recommendations(prefect_tool.recommendations) }}

{% endif %}

{% endif %}

{% set dagster_tool = dev_environment.tools.get('dagster') %}
{% if dagster_tool %}

## {{ dagster_tool.display_name }} for Data Pipelines

{{ macros.tool_header(dagster_tool) }}

{% if dagster_tool.recommendations %}
{{ macros.recommendations(dagster_tool.recommendations) }}

{% endif %}

{% endif %}

{% set dvc_tool = dev_environment.tools.get('dvc') %}
{% if dvc_tool %}

## {{ dvc_tool.display_name }} for Data Versioning

{{ macros.tool_header(dvc_tool) }}

{% if dvc_tool.files and dvc_tool.files|length > 0 %}
{{ macros.key_files(dvc_tool.files) }}

{% endif %}
{% if dvc_tool.recommendations %}
{{ macros.recommendations(dvc_tool.recommendations) }}

{% endif %}

{% endif %}
