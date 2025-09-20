# DevOps: Observability Guidance

{% set prom = dev_environment.tools.get('prometheus') %}
{% if prom %}

## Prometheus Monitoring

**Detected Tool:** {{ prom.display_name }} (Confidence:
{{ prom.confidence|capitalize }})
{% if prom.score is not none %}_Detection score:
{{ '%.1f'|format(prom.score) }}_{% endif %}

Prometheus configuration files were found, indicating you are using it for
monitoring.

**Key Files Detected:**

```text
{% for file in prom.files %}
- {{ file }}
{% endfor %}
{% if prom.files|length == 0 %}
(no representative files captured yet)
{% endif %}
```

{% if prom.recommendations %}
**Actionable Recommendations:**

{% for rec in prom.recommendations %}- {{ rec }}
{% endfor %}

{% endif %}

{% endif %}

{% set grafana = dev_environment.tools.get('grafana') %}
{% if grafana %}

## Grafana Dashboards

**Detected Tool:** {{ grafana.display_name }} (Confidence:
{{ grafana.confidence|capitalize }})
{% if grafana.score is not none %}_Detection score:
{{ '%.1f'|format(grafana.score) }}_{% endif %}

We detected Grafana configurations. Visualizing metrics helps you understand
system behavior.

**Key Files Detected:**

```text
{% for file in grafana.files %}
- {{ file }}
{% endfor %}
{% if grafana.files|length == 0 %}
(no representative files captured yet)
{% endif %}
```

{% if grafana.recommendations %}
**Actionable Recommendations:**

{% for rec in grafana.recommendations %}- {{ rec }}
{% endfor %}

{% endif %}

{% endif %}

{% set otel = dev_environment.tools.get('opentelemetry') %}
{% if otel %}

## OpenTelemetry Tracing

**Detected Tool:** {{ otel.display_name }} (Confidence:
{{ otel.confidence|capitalize }})
{% if otel.score is not none %}_Detection score:
{{ '%.1f'|format(otel.score) }}_{% endif %}

Distributed tracing helps debug and understand performance across services.

{% if otel.recommendations %}
**Actionable Recommendations:**

{% for rec in otel.recommendations %}- {{ rec }}
{% endfor %}

{% endif %}

{% endif %}
