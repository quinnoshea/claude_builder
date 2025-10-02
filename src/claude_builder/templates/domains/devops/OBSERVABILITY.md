{%- import '_macros.md' as macros -%}
# DevOps: Observability Guidance

{% set prom = dev_environment.tools.get('prometheus') %}
{% if prom %}

## Prometheus Monitoring

{{ macros.tool_header(prom) }}
Prometheus configuration files were found, indicating you are using it for
monitoring.

{% if prom.files and prom.files|length > 0 %}
{{ macros.key_files(prom.files) }}

{% endif %}
{% if prom.recommendations %}
{{ macros.recommendations(prom.recommendations) }}

{% endif %}

{% endif %}

{% set grafana = dev_environment.tools.get('grafana') %}
{% if grafana %}

## Grafana Dashboards

{{ macros.tool_header(grafana) }}
We detected Grafana configurations. Visualizing metrics helps you understand
system behavior.

{% if grafana.files and grafana.files|length > 0 %}
{{ macros.key_files(grafana.files) }}

{% endif %}
{% if grafana.recommendations %}
{{ macros.recommendations(grafana.recommendations) }}

{% endif %}

{% endif %}

{% set otel = dev_environment.tools.get('opentelemetry') %}
{% if otel %}

## OpenTelemetry Tracing

{{ macros.tool_header(otel) }}
Distributed tracing helps debug and understand performance across services.

{% if otel.recommendations %}
{{ macros.recommendations(otel.recommendations) }}

{% endif %}

{% endif %}
