{%- import '../_macros.md' as macros -%}
# MLOps: Governance Guidance

{% set dbt_tool = dev_environment.tools.get('dbt') %}
{% if dbt_tool %}

## {{ dbt_tool.display_name }} for Data Transformation

{{ macros.tool_header(dbt_tool) }}

{% if dbt_tool.files and dbt_tool.files|length > 0 %}
{{ macros.key_files(dbt_tool.files) }}

{% endif %}
{% if dbt_tool.recommendations %}
{{ macros.recommendations(dbt_tool.recommendations) }}

{% endif %}

{% endif %}

{% set gx_tool = dev_environment.tools.get('great_expectations') %}
{% if gx_tool %}

## {{ gx_tool.display_name }} for Data Quality

{{ macros.tool_header(gx_tool) }}

{% if gx_tool.recommendations %}
{{ macros.recommendations(gx_tool.recommendations) }}

{% endif %}

{% endif %}

{% set feast_tool = dev_environment.tools.get('feast') %}
{% if feast_tool %}

## {{ feast_tool.display_name }} for Feature Stores

{{ macros.tool_header(feast_tool) }}

{% if feast_tool.recommendations %}
{{ macros.recommendations(feast_tool.recommendations) }}

{% endif %}

{% endif %}
