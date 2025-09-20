# MLOps: Governance Guidance

{% set dbt_tool = dev_environment.tools.get('dbt') %}
{% if dbt_tool %}

## {{ dbt_tool.display_name }} for Data Transformation

**Detected Tool:** {{ dbt_tool.display_name }} (Confidence:
{{ dbt_tool.confidence|capitalize }})
{% if dbt_tool.score is not none %}_Detection score:
{{ '%.1f'|format(dbt_tool.score) }}_{% endif %}

**Key Files Detected:**

```text
{% for file in dbt_tool.files %}
- {{ file }}
{% endfor %}
{% if dbt_tool.files|length == 0 %}
(no representative files captured yet)
{% endif %}
```

{% if dbt_tool.recommendations %}
**Actionable Recommendations:**

{% for rec in dbt_tool.recommendations %}- {{ rec }}
{% endfor %}

{% endif %}

{% endif %}

{% set gx_tool = dev_environment.tools.get('great_expectations') %}
{% if gx_tool %}

## {{ gx_tool.display_name }} for Data Quality

**Detected Tool:** {{ gx_tool.display_name }} (Confidence:
{{ gx_tool.confidence|capitalize }})
{% if gx_tool.score is not none %}_Detection score:
{{ '%.1f'|format(gx_tool.score) }}_{% endif %}

{% if gx_tool.recommendations %}
**Actionable Recommendations:**

{% for rec in gx_tool.recommendations %}- {{ rec }}
{% endfor %}

{% endif %}

{% endif %}

{% set feast_tool = dev_environment.tools.get('feast') %}
{% if feast_tool %}

## {{ feast_tool.display_name }} for Feature Stores

**Detected Tool:** {{ feast_tool.display_name }} (Confidence:
{{ feast_tool.confidence|capitalize }})
{% if feast_tool.score is not none %}_Detection score:
{{ '%.1f'|format(feast_tool.score) }}_{% endif %}

{% if feast_tool.recommendations %}
**Actionable Recommendations:**

{% for rec in feast_tool.recommendations %}- {{ rec }}
{% endfor %}

{% endif %}

{% endif %}
