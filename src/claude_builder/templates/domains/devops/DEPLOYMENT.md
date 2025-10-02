{%- import '_macros.md' as macros -%}
# DevOps: Deployment Guidance

{% set kube = dev_environment.tools.get('kubernetes') %}
{% if kube %}

## Kubernetes Deployments

{{ macros.tool_header(kube) }}

We've detected Kubernetes configuration files, suggesting you are deploying
your application to a Kubernetes cluster.

{% if kube.files and kube.files|length > 0 %}
{{ macros.key_files(kube.files) }}

{% endif %}
{{ macros.recommendations(kube.recommendations, [
  'Use Helm or Kustomize to manage complex deployments consistently.',
  'Define resource requests/limits and liveness/readiness probes for each pod.',
  'Apply strict RBAC roles and Pod Security admission policies to harden clusters.'
]) }}

{% endif %}

{% set helm = dev_environment.tools.get('helm') %}
{% if helm %}

## Helm Chart for Kubernetes

{{ macros.tool_header(helm) }}

We've detected a Helm chart, which is a great way to package and deploy your
application on Kubernetes.

{% if helm.files and helm.files|length > 0 %}
{{ macros.key_files(helm.files) }}

{% endif %}
{{ macros.recommendations(helm.recommendations, [
  'Run `helm lint` and chart unit tests before publishing new releases.',
  'Parameterise values per environment and store in source control.',
  'Integrate secret management (e.g. SOPS, External Secrets) instead of plaintext.'
]) }}

{% endif %}
