"""Structured recommendations for health check failures.

This module provides platform-specific installation and configuration guidance
for tools and dependencies detected during health checks.
"""

from __future__ import annotations

import platform


class RecommendationProvider:
    """Provides actionable, platform-specific recommendations for health check issues."""

    def __init__(self) -> None:
        self.platform = platform.system().lower()

    def get_tool_recommendation(self, tool_name: str) -> dict[str, str]:
        """Get installation recommendation for a specific tool.

        Args:
            tool_name: Name of the tool (e.g., 'git', 'docker', 'terraform')

        Returns:
            Dictionary with 'message' and 'command' keys providing guidance
        """
        recommendations = {
            "git": self._get_git_recommendation(),
            "terraform": self._get_terraform_recommendation(),
            "kubectl": self._get_kubectl_recommendation(),
            "docker": self._get_docker_recommendation(),
            "helm": self._get_helm_recommendation(),
            "ansible": self._get_ansible_recommendation(),
            "aws": self._get_aws_cli_recommendation(),
            "gcloud": self._get_gcloud_cli_recommendation(),
            "az": self._get_azure_cli_recommendation(),
        }

        return recommendations.get(
            tool_name,
            {
                "message": f"Install {tool_name} and ensure it's in your PATH",
            },
        )

    def get_multiple_tools_summary(self, missing_tools: list[str]) -> str:
        """Generate a summary message for multiple missing tools.

        Args:
            missing_tools: List of tool names that are missing

        Returns:
            Human-readable summary message
        """
        if not missing_tools:
            return "All tools are available"

        if len(missing_tools) == 1:
            return f"Missing tool: {missing_tools[0]}"

        return f"Missing {len(missing_tools)} tools: {', '.join(missing_tools)}"

    def _get_git_recommendation(self) -> dict[str, str]:
        """Git installation recommendation."""
        if self.platform == "linux":
            return {
                "message": "Install Git using your package manager",
                "command": "sudo apt-get install git  # Debian/Ubuntu\nsudo yum install git      # RHEL/CentOS",
            }
        if self.platform == "darwin":
            return {
                "message": "Install Git using Homebrew or Xcode Command Line Tools",
                "command": "brew install git  # or: xcode-select --install",
            }
        if self.platform == "windows":
            return {
                "message": "Download Git from git-scm.com",
                "command": "winget install Git.Git",
            }
        return {"message": "Install Git: https://git-scm.com/downloads"}

    def _get_terraform_recommendation(self) -> dict[str, str]:
        """Terraform installation recommendation."""
        if self.platform == "linux":
            return {
                "message": "Install Terraform from HashiCorp's official repository",
                "command": "wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg\n"
                'echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list\n'
                "sudo apt-get update && sudo apt-get install terraform",
            }
        if self.platform == "darwin":
            return {
                "message": "Install Terraform using Homebrew",
                "command": "brew tap hashicorp/tap && brew install hashicorp/tap/terraform",
            }
        if self.platform == "windows":
            return {
                "message": "Install Terraform using Chocolatey or download binary",
                "command": "choco install terraform",
            }
        return {"message": "Install Terraform: https://www.terraform.io/downloads"}

    def _get_kubectl_recommendation(self) -> dict[str, str]:
        """kubectl installation recommendation."""
        if self.platform == "linux":
            return {
                "message": "Install kubectl using the Kubernetes package repository",
                "command": "curl -LO https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl\n"
                "sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl",
            }
        if self.platform == "darwin":
            return {
                "message": "Install kubectl using Homebrew",
                "command": "brew install kubectl",
            }
        if self.platform == "windows":
            return {
                "message": "Install kubectl using Chocolatey or download binary",
                "command": "choco install kubernetes-cli",
            }
        return {"message": "Install kubectl: https://kubernetes.io/docs/tasks/tools/"}

    def _get_docker_recommendation(self) -> dict[str, str]:
        """Docker installation recommendation."""
        if self.platform == "linux":
            return {
                "message": "Install Docker Engine and ensure the Docker daemon is running",
                "command": "curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh\n"
                "sudo systemctl start docker && sudo systemctl enable docker\n"
                "sudo usermod -aG docker $USER  # Add current user to docker group",
            }
        if self.platform == "darwin":
            return {
                "message": "Install Docker Desktop for Mac",
                "command": "brew install --cask docker",
            }
        if self.platform == "windows":
            return {
                "message": "Install Docker Desktop for Windows",
                "command": "winget install Docker.DockerDesktop",
            }
        return {"message": "Install Docker: https://docs.docker.com/get-docker/"}

    def _get_helm_recommendation(self) -> dict[str, str]:
        """Helm installation recommendation."""
        if self.platform == "linux":
            return {
                "message": "Install Helm using the official install script",
                "command": "curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash",
            }
        if self.platform == "darwin":
            return {
                "message": "Install Helm using Homebrew",
                "command": "brew install helm",
            }
        if self.platform == "windows":
            return {
                "message": "Install Helm using Chocolatey or Scoop",
                "command": "choco install kubernetes-helm",
            }
        return {"message": "Install Helm: https://helm.sh/docs/intro/install/"}

    def _get_ansible_recommendation(self) -> dict[str, str]:
        """Ansible installation recommendation."""
        return {
            "message": "Install Ansible using pip (cross-platform)",
            "command": "pip install ansible",
        }

    def _get_aws_cli_recommendation(self) -> dict[str, str]:
        """AWS CLI installation recommendation."""
        if self.platform == "linux":
            return {
                "message": "Install AWS CLI v2 for Linux",
                "command": "curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'\n"
                "unzip awscliv2.zip && sudo ./aws/install",
            }
        if self.platform == "darwin":
            return {
                "message": "Install AWS CLI using Homebrew or the official installer",
                "command": "brew install awscli",
            }
        if self.platform == "windows":
            return {
                "message": "Install AWS CLI using the MSI installer",
                "command": "winget install Amazon.AWSCLI",
            }
        return {"message": "Install AWS CLI: https://aws.amazon.com/cli/"}

    def _get_gcloud_cli_recommendation(self) -> dict[str, str]:
        """Google Cloud CLI installation recommendation."""
        if self.platform == "linux":
            return {
                "message": "Install Google Cloud CLI using the official installer",
                "command": "curl https://sdk.cloud.google.com | bash\n"
                "exec -l $SHELL  # Restart shell\n"
                "gcloud init",
            }
        if self.platform == "darwin":
            return {
                "message": "Install Google Cloud CLI using Homebrew or the official installer",
                "command": "brew install --cask google-cloud-sdk",
            }
        if self.platform == "windows":
            return {
                "message": "Install Google Cloud CLI using the Windows installer",
                "command": "Download from: https://cloud.google.com/sdk/docs/install",
            }
        return {
            "message": "Install Google Cloud CLI: https://cloud.google.com/sdk/docs/install"
        }

    def _get_azure_cli_recommendation(self) -> dict[str, str]:
        """Azure CLI installation recommendation."""
        if self.platform == "linux":
            return {
                "message": "Install Azure CLI using the official script",
                "command": "curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash",
            }
        if self.platform == "darwin":
            return {
                "message": "Install Azure CLI using Homebrew",
                "command": "brew update && brew install azure-cli",
            }
        if self.platform == "windows":
            return {
                "message": "Install Azure CLI using the MSI installer",
                "command": "winget install Microsoft.AzureCLI",
            }
        return {
            "message": "Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        }


def get_recommendation_for_tool(tool_name: str) -> dict[str, str]:
    """Get installation recommendation for a tool (convenience function).

    Args:
        tool_name: Name of the tool

    Returns:
        Dictionary with 'message' and 'command' keys
    """
    provider = RecommendationProvider()
    return provider.get_tool_recommendation(tool_name)


def format_recommendation(
    tool_name: str, recommendation: dict[str, str] | None = None
) -> str:
    """Format a recommendation as a user-friendly string.

    Args:
        tool_name: Name of the tool
        recommendation: Optional recommendation dict (will be fetched if not provided)

    Returns:
        Formatted recommendation string
    """
    if recommendation is None:
        recommendation = get_recommendation_for_tool(tool_name)

    message = recommendation.get("message", "")
    command = recommendation.get("command")

    if command:
        return f"{message}\n  Command: {command}"
    return message
