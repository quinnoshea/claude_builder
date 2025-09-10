{% if dev_environment.tools.prometheus %}
### Prometheus Monitoring

**Detected Tool:** Prometheus (Confidence: {{ dev_environment.tools.prometheus.confidence }})

Prometheus configuration files were found, indicating that you are using Prometheus for monitoring.

**Key Files Detected:**
```
{% for file in dev_environment.tools.prometheus.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1.  **Instrument Your Application:** Expose custom application metrics for Prometheus to scrape. This will give you deeper insights into your application's performance.
2.  **Alerting Rules:** Define alerting rules in Prometheus to be notified of important events.
3.  **Use a Dashboard:** Visualize your metrics with a tool like Grafana for easier analysis.

{% endif %}

{% if dev_environment.tools.grafana %}
### Grafana Dashboards

**Detected Tool:** Grafana (Confidence: {{ dev_environment.tools.grafana.confidence }})

We've detected Grafana dashboard configurations. Visualizing your metrics is key to understanding your system's behavior.

**Key Files Detected:**
```
{% for file in dev_environment.tools.grafana.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1.  **Version Your Dashboards:** Store your dashboard JSON files in version control to track changes and collaborate with your team.
2.  **Use Variables:** Make your dashboards more interactive and reusable by using template variables.
3.  **Organize with Folders:** Group related dashboards into folders to keep your Grafana instance organized.

{% endif %}

{% if dev_environment.tools.opentelemetry %}
### OpenTelemetry Tracing

**Detected Tool:** OpenTelemetry (Confidence: {{ dev_environment.tools.opentelemetry.confidence }})

OpenTelemetry usage has been detected. Distributed tracing is a powerful tool for debugging and understanding your application's performance in a microservices architecture.

**Next Steps & Best Practices:**

1.  **Ensure Consistent Sampling:** Configure your sampling strategy to capture a representative amount of traces without overwhelming your system.
2.  **Propagate Context:** Make sure trace context is propagated across all your services to get a complete end-to-end view of your requests.
3.  **Add Custom Attributes:** Enrich your spans with custom attributes to provide more context and make debugging easier.

{% endif %}

