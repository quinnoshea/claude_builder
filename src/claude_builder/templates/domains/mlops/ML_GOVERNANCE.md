{% if dev_environment.tools.dbt %}
### dbt for Data Transformation

**Detected Tool:** dbt (Confidence: {{ dev_environment.tools.dbt.confidence }})

dbt models have been detected. dbt is a great tool for transforming data in your warehouse.

**Key Files Detected:**
```
{% for file in dev_environment.tools.dbt.files %}
- {{ file }}
{% endfor %}
```

**Next Steps & Best Practices:**

1.  **Test Your Models:** Write tests for your dbt models to ensure data quality and prevent regressions.
2.  **Document Your Models:** Document your models to help your team understand your data warehouse.
3.  **Use Packages:** Leverage dbt packages to reuse code and speed up your development.

{% endif %}

{% if dev_environment.tools.great_expectations %}
### Great Expectations for Data Quality

**Detected Tool:** Great Expectations (Confidence: {{ dev_environment.tools.great_expectations.confidence }})

Great Expectations checkpoints have been detected. Great Expectations is a powerful tool for data testing, documentation, and profiling.

**Next Steps & Best Practices:**

1.  **Integrate into Pipelines:** Run your checkpoints as part of your data pipelines to automatically validate your data.
2.  **Use Data Docs:** Host and share your Data Docs to provide a single source of truth for your data quality.
3.  **Customize Expectations:** Write custom Expectations to meet your specific data quality needs.

{% endif %}

{% if dev_environment.tools.feast %}
### Feast for Feature Stores

**Detected Tool:** Feast (Confidence: {{ dev_environment.tools.feast.confidence }})

Feast feature definitions have been detected. Feast is an open-source feature store for machine learning.

**Next Steps & Best Practices:**

1.  **Use a Centralized Store:** Use a centralized online and offline store to serve features for both training and inference.
2.  **Monitor Feature Drift:** Monitor your features for drift to ensure that your models are not trained on stale or irrelevant data.
3.  **Share and Reuse Features:** Use Feast to share and reuse features across multiple projects and teams.

{% endif %}

