# MLOps: Data Pipeline Guidance

{% set airflow_tool = dev_environment.tools.get('airflow') %}
{% if airflow_tool %}

## {{ airflow_tool.display_name }} for Data Pipelines

**Detected Tool:** {{ airflow_tool.display_name }} (Confidence:
{{ airflow_tool.confidence|capitalize }})
{% if airflow_tool.score is not none %}_Detection score:
{{ '%.1f'|format(airflow_tool.score) }}_{% endif %}

Airflow is a platform for authoring, scheduling, and monitoring workflows.

**Key Files Detected:**
```text
{% for file in airflow_tool.files %}
- {{ file }}
{% endfor %}
{% if airflow_tool.files|length == 0 %}
(no representative files captured yet)
{% endif %}
```

{% if airflow_tool.recommendations %}
**Actionable Recommendations:**

{% for rec in airflow_tool.recommendations %}- {{ rec }}
{% endfor %}

{% endif %}

{% endif %}

{% set prefect_tool = dev_environment.tools.get('prefect') %}
{% if prefect_tool %}

## {{ prefect_tool.display_name }} for Data Pipelines

**Detected Tool:** {{ prefect_tool.display_name }} (Confidence:
{{ prefect_tool.confidence|capitalize }})
{% if prefect_tool.score is not none %}_Detection score:
{{ '%.1f'|format(prefect_tool.score) }}_{% endif %}

{% if prefect_tool.recommendations %}
**Actionable Recommendations:**

{% for rec in prefect_tool.recommendations %}- {{ rec }}
{% endfor %}

{% endif %}

{% endif %}

{% set dagster_tool = dev_environment.tools.get('dagster') %}
{% if dagster_tool %}

## {{ dagster_tool.display_name }} for Data Pipelines

**Detected Tool:** {{ dagster_tool.display_name }} (Confidence:
{{ dagster_tool.confidence|capitalize }})
{% if dagster_tool.score is not none %}_Detection score:
{{ '%.1f'|format(dagster_tool.score) }}_{% endif %}

{% if dagster_tool.recommendations %}
**Actionable Recommendations:**

{% for rec in dagster_tool.recommendations %}- {{ rec }}
{% endfor %}

{% endif %}

{% endif %}

{% set dvc_tool = dev_environment.tools.get('dvc') %}
{% if dvc_tool %}

## {{ dvc_tool.display_name }} for Data Versioning

**Detected Tool:** {{ dvc_tool.display_name }} (Confidence:
{{ dvc_tool.confidence|capitalize }})
{% if dvc_tool.score is not none %}_Detection score:
{{ '%.1f'|format(dvc_tool.score) }}_{% endif %}

**Key Files Detected:**
```text
{% for file in dvc_tool.files %}
- {{ file }}
{% endfor %}
{% if dvc_tool.files|length == 0 %}
(no representative files captured yet)
{% endif %}
```

{% if dvc_tool.recommendations %}
**Actionable Recommendations:**

{% for rec in dvc_tool.recommendations %}- {{ rec }}
{% endfor %}

{% endif %}

{% endif %}
