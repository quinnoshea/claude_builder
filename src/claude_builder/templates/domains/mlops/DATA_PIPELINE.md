# MLOps: Data Pipeline Guidance

{% if dev_environment.tools.airflow %}

## Airflow for Data Pipelines

**Detected Tool:** Airflow (Confidence:
{{ dev_environment.tools.airflow.confidence }})

Airflow is a platform for authoring, scheduling, and monitoring workflows.

**Key Files Detected:**

```text
{% for file in dev_environment.tools.airflow.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1. **TaskFlow API:** Prefer TaskFlow for Python‑native DAGs.
2. **Atomic Tasks:** Design tasks to be atomic and idempotent.
3. **Version Control:** Store DAGs in Git to track changes.

{% endif %}

{% if dev_environment.tools.prefect %}

## Prefect for Data Pipelines

**Detected Tool:** Prefect (Confidence:
{{ dev_environment.tools.prefect.confidence }})

Prefect is a modern workflow automation platform.

**Next Steps & Best Practices:**

1. **Backend:** Use Prefect Cloud or a self‑hosted server.
2. **Caching:** Enable caching to avoid repeated work.
3. **Projects:** Group related flows into projects.

{% endif %}

{% if dev_environment.tools.dagster %}

## Dagster for Data Pipelines

**Detected Tool:** Dagster (Confidence:
{{ dev_environment.tools.dagster.confidence }})

Dagster orchestrates ML, analytics, and ETL assets.

**Next Steps & Best Practices:**

1. **Software‑Defined Assets:** Define assets in code as the source of truth.
2. **I/O Managers:** Abstract storage/loading with I/O managers.
3. **Dagit:** Use Dagit for visualization and debugging.

{% endif %}

{% if dev_environment.tools.dvc %}

## DVC for Data Versioning

**Detected Tool:** DVC (Confidence:
{{ dev_environment.tools.dvc.confidence }})

DVC versions data and models.

**Key Files Detected:**

```text
{% for file in dev_environment.tools.dvc.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1. **Remote Storage:** Configure a remote (S3, GCS, etc.) for sharing.
2. **Pipelines:** Define processing and modeling pipelines in DVC.
3. **Track Metrics:** Track and compare experiment metrics.

{% endif %}
