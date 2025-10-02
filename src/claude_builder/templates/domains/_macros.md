{# Reusable Jinja2 macros for domain templates #}

{# Display tool detection header with confidence and score #}
{% macro tool_header(tool) -%}
**Detected Tool:** {{ tool.display_name }}
**Confidence:** {{ tool.confidence|capitalize }}
{%- if tool.score is not none %}
**Detection Score:** {{ '%.1f'|format(tool.score) }}
{%- endif %}
{%- endmacro %}

{# Display tool detection header (compact inline format) #}
{% macro tool_header_inline(tool) -%}
**Detected:** {{ tool.display_name }} ({{ tool.confidence|capitalize }})
{%- if tool.score is not none %} | Score: {{ '%.1f'|format(tool.score) }}{%- endif %}
{%- endmacro %}

{# Display list of key files detected #}
{% macro key_files(files) -%}
**Key Files Detected:**

```text
{% for file in files -%}
- {{ file }}
{% endfor -%}
{% if files|length == 0 -%}
(no representative files captured yet)
{% endif -%}
```
{%- endmacro %}

{# Display recommendations section #}
{% macro recommendations(recs, default_recs=none) -%}
**Actionable Recommendations:**

{% if recs -%}
{% for rec in recs -%}
- {{ rec }}
{% endfor -%}
{% elif default_recs -%}
{% for rec in default_recs -%}
- {{ rec }}
{% endfor -%}
{% endif -%}
{%- endmacro %}

{# Complete tool section with all common elements #}
{% macro tool_section(tool, title, description, default_recs=none) -%}
## {{ title }}

{{ self.tool_header(tool) }}

{{ description }}

{% if tool.files and tool.files|length > 0 -%}
{{ self.key_files(tool.files) }}

{% endif -%}
{{ self.recommendations(tool.recommendations, default_recs) }}
{%- endmacro %}
