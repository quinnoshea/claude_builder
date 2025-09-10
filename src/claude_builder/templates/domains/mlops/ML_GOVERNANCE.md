{% if dev_environment.tools.dbt %}

### dbt for Data Transformation

**Detected Tool:** dbt (Confidence:
{{ dev_environment.tools.dbt.confidence }})

dbt transforms data in your warehouse using SQL and tested models.

**Key Files Detected:**

```text
{% for file in dev_environment.tools.dbt.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1. **Tests:** Write tests to ensure data quality and prevent regressions.
2. **Docs:** Document models to help teams understand your warehouse.
3. **Packages:** Reuse code via dbt packages to speed development.

{% endif %}

{% if dev_environment.tools.great_expectations %}

### Great Expectations for Data Quality

**Detected Tool:** Great Expectations (Confidence:
{{ dev_environment.tools.great_expectations.confidence }})

Great Expectations provides data testing, documentation, and profiling.

**Next Steps & Best Practices:**

1. **Pipelines:** Run checkpoints in pipelines to validate data.
2. **Data Docs:** Host Data Docs as the single source of truth.
3. **Custom Expectations:** Write custom checks for your needs.

{% endif %}

{% if dev_environment.tools.feast %}

### Feast for Feature Stores

**Detected Tool:** Feast (Confidence:
{{ dev_environment.tools.feast.confidence }})

Feast is a feature store for machine learning.

**Next Steps & Best Practices:**

1. **Centralized Store:** Provide combined online/offline stores for training
   and inference.
2. **Monitor Drift:** Watch features for drift to avoid stale inputs.
3. **Share/Reuse:** Share features across projects and teams.

{% endif %}
