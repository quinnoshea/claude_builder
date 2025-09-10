# DevOps: Observability Guidance

{% if dev_environment.tools.prometheus %}

### Prometheus Monitoring

**Detected Tool:** Prometheus (Confidence:
{{ dev_environment.tools.prometheus.confidence }})

Prometheus configuration files were found, indicating you are using it for
monitoring.

**Key Files Detected:**

```text
{% for file in dev_environment.tools.prometheus.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1. **Instrument Your Application:** Expose custom metrics for Prometheus to
   scrape to gain insight into performance and behavior.
2. **Alerting Rules:** Define alerting rules to be notified of important
   events.
3. **Dashboards:** Visualize metrics in Grafana for faster analysis.

{% endif %}

{% if dev_environment.tools.grafana %}

### Grafana Dashboards

**Detected Tool:** Grafana (Confidence:
{{ dev_environment.tools.grafana.confidence }})

We detected Grafana configurations. Visualizing metrics helps you understand
system behavior.

**Key Files Detected:**

```text
{% for file in dev_environment.tools.grafana.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1. **Version Dashboards:** Store dashboard JSON in version control to track
   changes.
2. **Use Variables:** Make dashboards reusable and interactive with variables.
3. **Organize:** Group related dashboards into folders to keep things tidy.

{% endif %}

{% if dev_environment.tools.opentelemetry %}

### OpenTelemetry Tracing

**Detected Tool:** OpenTelemetry (Confidence:
{{ dev_environment.tools.opentelemetry.confidence }})

Distributed tracing helps debug and understand performance across services.

**Next Steps & Best Practices:**

1. **Sampling:** Configure sampling to balance visibility and overhead.
2. **Context Propagation:** Ensure trace context is propagated across all
   services.
3. **Custom Attributes:** Enrich spans with attributes for better debugging.

{% endif %}
