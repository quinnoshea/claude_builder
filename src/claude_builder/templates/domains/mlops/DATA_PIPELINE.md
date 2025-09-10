{% if dev_environment.tools.airflow %}
### Airflow for Data Pipelines

**Detected Tool:** Airflow (Confidence: {{ dev_environment.tools.airflow.confidence }})

Airflow DAGs have been detected. Airflow is a robust platform for programmatically authoring, scheduling, and monitoring workflows.

**Key Files Detected:**
```
{% for file in dev_environment.tools.airflow.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1.  **Use TaskFlow API:** For new DAGs, consider using the TaskFlow API to write your pipelines in a more Python-native way.
2.  **Keep Tasks Atomic:** Design your tasks to be atomic and idempotent to make your DAGs more resilient and easier to debug.
3.  **Use a Version Control System:** Store your DAGs in a version control system like Git to track changes and collaborate with your team.

{% endif %}

{% if dev_environment.tools.prefect %}
### Prefect for Data Pipelines

**Detected Tool:** Prefect (Confidence: {{ dev_environment.tools.prefect.confidence }})

Prefect flows have been detected. Prefect is a modern data workflow automation platform.

**Next Steps & Best Practices:**

1.  **Use a Backend:** Configure a backend (Prefect Cloud or a self-hosted server) to orchestrate and monitor your flows.
2.  **Use Caching:** Use Prefect's caching mechanism to avoid re-running tasks that have already completed successfully.
3.  **Organize with Projects:** Group related flows into projects to keep your work organized.

{% endif %}

{% if dev_environment.tools.dagster %}
### Dagster for Data Pipelines

**Detected Tool:** Dagster (Confidence: {{ dev_environment.tools.dagster.confidence }})

Dagster assets have been detected. Dagster is a data orchestrator for machine learning, analytics, and ETL.

**Next Steps & Best Practices:**

1.  **Use Software-Defined Assets:** Define your data assets in code to provide a single source of truth for your data platform.
2.  **Use I/O Managers:** Use I/O managers to abstract away the storage and loading of your assets.
3.  **Use Dagit:** Use the Dagit UI to visualize your assets, monitor runs, and debug your pipelines.

{% endif %}

{% if dev_environment.tools.dvc %}
### DVC for Data Versioning

**Detected Tool:** DVC (Confidence: {{ dev_environment.tools.dvc.confidence }})

DVC files have been detected. DVC is a great tool for versioning your data and models.

**Key Files Detected:**
```
{% for file in dev_environment.tools.dvc.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1.  **Use a Remote Storage:** Configure a remote storage (like S3, GCS, or a shared network drive) to share your data and models with your team.
2.  **Use Pipelines:** Use DVC pipelines to define your data processing and modeling workflows.
3.  **Track Metrics:** Use DVC to track metrics and compare the performance of different experiments.

{% endif %}

