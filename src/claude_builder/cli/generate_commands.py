"""Generation CLI commands for Claude Builder."""

import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel

from claude_builder.core.analyzer import ProjectAnalyzer
from claude_builder.core.generator import DocumentGenerator
from claude_builder.core.models import ProjectAnalysis
from claude_builder.utils.exceptions import ClaudeBuilderError

console = Console()


@click.group()
def generate():
    """Generate documentation and configurations."""


@generate.command()
@click.argument("project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--from-analysis", type=click.Path(exists=True, file_okay=True),
              help="Use existing analysis file")
@click.option("--template", help="Override template selection")
@click.option("--partial", help="Generate only specific sections (comma-separated)")
@click.option("--output-dir", type=click.Path(), help="Output directory (default: PROJECT_PATH)")
@click.option("--format", "output_format", type=click.Choice(["files", "zip", "tar"]),
              default="files", help="Output format")
@click.option("--backup-existing", is_flag=True, help="Backup existing files before overwriting")
@click.option("--dry-run", is_flag=True, help="Show what would be generated without creating files")
@click.option("--verbose", "-v", count=True, help="Verbose output")
def docs(project_path: str, from_analysis: Optional[str], template: Optional[str],
         partial: Optional[str], output_dir: Optional[str], output_format: str,
         backup_existing: bool, dry_run: bool, verbose: int):
    """Generate documentation from project analysis."""
    try:
        path = Path(project_path).resolve()

        if verbose > 0:
            console.print(f"[cyan]Generating documentation for: {path}[/cyan]")

        # Get project analysis
        if from_analysis:
            analysis = _load_analysis_from_file(Path(from_analysis))
            if verbose > 0:
                console.print(f"[green]Loaded analysis from: {from_analysis}[/green]")
        else:
            if verbose > 0:
                console.print("[cyan]Analyzing project...[/cyan]")
            analyzer = ProjectAnalyzer()
            analysis = analyzer.analyze(path)

        # Configure generator
        config = {}
        if template:
            config["preferred_template"] = template
        config["output_format"] = output_format

        # Apply partial generation filter
        sections_filter = None
        if partial:
            sections_filter = [s.strip() for s in partial.split(",")]
            if verbose > 0:
                console.print(f"[yellow]Generating only sections: {sections_filter}[/yellow]")

        # Generate content
        generator = DocumentGenerator(config)
        generated_content = generator.generate(analysis, path)

        # Apply sections filter
        if sections_filter:
            filtered_files = {}
            for section in sections_filter:
                # Map section names to files
                if section.lower() == "claude":
                    filtered_files.update({k: v for k, v in generated_content.files.items()
                                         if "claude" in k.lower()})
                elif section.lower() == "agents":
                    filtered_files.update({k: v for k, v in generated_content.files.items()
                                         if "agent" in k.lower()})
                elif section.lower() == "docs":
                    filtered_files.update({k: v for k, v in generated_content.files.items()
                                         if k.endswith(".md") and "agent" not in k.lower()})
                else:
                    # Try to match by filename
                    filtered_files.update({k: v for k, v in generated_content.files.items()
                                         if section.lower() in k.lower()})

            generated_content.files = filtered_files

        # Display what would be generated
        if dry_run or verbose > 0:
            _display_generation_preview(generated_content, analysis)

        if dry_run:
            console.print("[yellow]Dry run complete - no files were created[/yellow]")
            return

        # Write files
        output_path = Path(output_dir) if output_dir else path
        _write_generated_files(generated_content, output_path, backup_existing, verbose)

        console.print("[green]✓ Documentation generated successfully[/green]")
        console.print(f"Output location: {output_path}")

    except Exception as e:
        console.print(f"[red]Error generating documentation: {e}[/red]")
        raise click.ClickException(f"Failed to generate documentation: {e}")


@generate.command()
@click.argument("project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--from-analysis", type=click.Path(exists=True, file_okay=True),
              help="Use existing analysis file")
@click.option("--agents-dir", type=click.Path(), help="Custom agents directory")
@click.option("--output-file", type=click.Path(), help="Output file (default: AGENTS.md)")
@click.option("--dry-run", is_flag=True, help="Show what would be generated without creating files")
@click.option("--verbose", "-v", count=True, help="Verbose output")
def agents(project_path: str, from_analysis: Optional[str], agents_dir: Optional[str],
           output_file: Optional[str], dry_run: bool, verbose: int):
    """Generate agent configurations."""
    try:
        path = Path(project_path).resolve()

        if verbose > 0:
            console.print(f"[cyan]Generating agent configuration for: {path}[/cyan]")

        # Get project analysis
        if from_analysis:
            analysis = _load_analysis_from_file(Path(from_analysis))
            if verbose > 0:
                console.print(f"[green]Loaded analysis from: {from_analysis}[/green]")
        else:
            if verbose > 0:
                console.print("[cyan]Analyzing project...[/cyan]")
            analyzer = ProjectAnalyzer()
            analysis = analyzer.analyze(path)

        # Generate agent configuration
        from claude_builder.core.agents import UniversalAgentSystem
        agent_system = UniversalAgentSystem()
        agent_config = agent_system.select_agents(analysis)

        if verbose > 0:
            console.print(f"[green]Selected {len(agent_config.all_agents)} agents[/green]")

        # Generate agent documentation
        generator = DocumentGenerator({"agents_only": True})
        generated_content = generator.generate(analysis, path)

        # Filter to just agent files
        agent_files = {k: v for k, v in generated_content.files.items()
                      if "agent" in k.lower() or k == "AGENTS.md"}

        if dry_run or verbose > 0:
            console.print(Panel(
                f"**Agent Configuration Preview**\\n\\n"
                f"Core agents: {len(agent_config.core_agents)}\\n"
                f"Domain agents: {len(agent_config.domain_agents)}\\n"
                f"Workflow agents: {len(agent_config.workflow_agents)}\\n"
                f"Custom agents: {len(agent_config.custom_agents)}\\n\\n"
                f"Files to generate: {list(agent_files.keys())}",
                title="Agent Generation Preview"
            ))

        if dry_run:
            console.print("[yellow]Dry run complete - no files were created[/yellow]")
            return

        # Write agent files
        output_path = Path(output_file) if output_file else path / "AGENTS.md"

        if len(agent_files) == 1 and "AGENTS.md" in agent_files:
            # Write single file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(agent_files["AGENTS.md"])
            console.print(f"[green]✓ Agent configuration written to: {output_path}[/green]")
        else:
            # Write multiple files
            for filename, content in agent_files.items():
                file_path = output_path.parent / filename if output_path.is_file() else output_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            console.print(f"[green]✓ Agent files written to: {output_path.parent if output_path.is_file() else output_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error generating agents: {e}[/red]")
        raise click.ClickException(f"Failed to generate agents: {e}")


def _load_analysis_from_file(analysis_file: Path) -> ProjectAnalysis:
    """Load project analysis from file."""
    try:
        with open(analysis_file, encoding="utf-8") as f:
            if analysis_file.suffix.lower() in [".yaml", ".yml"]:
                import yaml
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        # Reconstruct ProjectAnalysis object from dictionary
        # This is a simplified version - in production this would be more robust
        analysis = ProjectAnalysis(project_path=Path(data["project_path"]))

        # Populate basic fields
        analysis.analysis_confidence = data.get("analysis_confidence", 0.0)
        analysis.analysis_timestamp = data.get("analysis_timestamp")
        analysis.analyzer_version = data.get("analyzer_version")

        # Language info
        lang_data = data.get("language_info", {})
        analysis.language_info.primary = lang_data.get("primary")
        analysis.language_info.secondary = lang_data.get("secondary", [])
        analysis.language_info.confidence = lang_data.get("confidence", 0.0)
        analysis.language_info.file_counts = lang_data.get("file_counts", {})
        analysis.language_info.total_lines = lang_data.get("total_lines", {})

        # Framework info
        fw_data = data.get("framework_info", {})
        analysis.framework_info.primary = fw_data.get("primary")
        analysis.framework_info.secondary = fw_data.get("secondary", [])
        analysis.framework_info.confidence = fw_data.get("confidence", 0.0)
        analysis.framework_info.version = fw_data.get("version")
        analysis.framework_info.config_files = fw_data.get("config_files", [])

        # Domain info
        domain_data = data.get("domain_info", {})
        analysis.domain_info.domain = domain_data.get("domain")
        analysis.domain_info.confidence = domain_data.get("confidence", 0.0)
        analysis.domain_info.indicators = domain_data.get("indicators", [])
        analysis.domain_info.specialized_patterns = domain_data.get("specialized_patterns", [])

        # Enum fields
        from claude_builder.core.models import (
            ArchitecturePattern,
            ComplexityLevel,
            ProjectType,
        )
        try:
            analysis.project_type = ProjectType(data.get("project_type", "unknown"))
        except ValueError:
            analysis.project_type = ProjectType.UNKNOWN

        try:
            analysis.complexity_level = ComplexityLevel(data.get("complexity_level", "simple"))
        except ValueError:
            analysis.complexity_level = ComplexityLevel.SIMPLE

        try:
            analysis.architecture_pattern = ArchitecturePattern(data.get("architecture_pattern", "unknown"))
        except ValueError:
            analysis.architecture_pattern = ArchitecturePattern.UNKNOWN

        # Development environment
        dev_data = data.get("development_environment", {})
        analysis.dev_environment.package_managers = dev_data.get("package_managers", [])
        analysis.dev_environment.testing_frameworks = dev_data.get("testing_frameworks", [])
        analysis.dev_environment.linting_tools = dev_data.get("linting_tools", [])
        analysis.dev_environment.ci_cd_systems = dev_data.get("ci_cd_systems", [])
        analysis.dev_environment.containerization = dev_data.get("containerization", [])
        analysis.dev_environment.databases = dev_data.get("databases", [])
        analysis.dev_environment.documentation_tools = dev_data.get("documentation_tools", [])

        # Filesystem info
        fs_data = data.get("filesystem_info", {})
        analysis.filesystem_info.total_files = fs_data.get("total_files", 0)
        analysis.filesystem_info.total_directories = fs_data.get("total_directories", 0)
        analysis.filesystem_info.source_files = fs_data.get("source_files", 0)
        analysis.filesystem_info.test_files = fs_data.get("test_files", 0)
        analysis.filesystem_info.config_files = fs_data.get("config_files", 0)
        analysis.filesystem_info.documentation_files = fs_data.get("documentation_files", 0)
        analysis.filesystem_info.asset_files = fs_data.get("asset_files", 0)
        analysis.filesystem_info.ignore_patterns = fs_data.get("ignore_patterns", [])
        analysis.filesystem_info.root_files = fs_data.get("root_files", [])

        # Warnings and suggestions
        analysis.warnings = data.get("warnings", [])
        analysis.suggestions = data.get("suggestions", [])

        return analysis

    except Exception as e:
        raise ClaudeBuilderError(f"Failed to load analysis from {analysis_file}: {e}")


def _display_generation_preview(generated_content, analysis):
    """Display preview of what will be generated."""
    files_info = []
    total_size = 0

    for filename, content in generated_content.files.items():
        size = len(content.encode("utf-8"))
        total_size += size
        files_info.append(f"  • {filename} ({size:,} bytes)")

    preview_text = f"**Files to generate ({len(generated_content.files)} total):**\\n\\n"
    preview_text += "\\n".join(files_info)
    preview_text += f"\\n\\n**Total size:** {total_size:,} bytes"
    preview_text += f"\\n**Template info:** {len(generated_content.template_info)} templates used"

    console.print(Panel(preview_text, title="Generation Preview"))


def _write_generated_files(generated_content, output_path: Path, backup_existing: bool, verbose: int):
    """Write generated files to disk."""
    files_written = 0

    for filename, content in generated_content.files.items():
        file_path = output_path / filename

        # Create directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Backup existing file if requested
        if backup_existing and file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            file_path.rename(backup_path)
            if verbose > 0:
                console.print(f"[yellow]Backed up existing file: {backup_path}[/yellow]")

        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        files_written += 1

        if verbose > 1:
            console.print(f"[green]✓ {filename}[/green]")

    if verbose > 0:
        console.print(f"[green]Wrote {files_written} files[/green]")


@generate.command()
@click.argument("project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--from-analysis", type=click.Path(exists=True, file_okay=True),
              help="Use existing analysis file")
@click.option("--template", help="Override template selection")
@click.option("--output-file", type=click.Path(), help="Output file (default: CLAUDE.md)")
@click.option("--dry-run", is_flag=True, help="Show what would be generated without creating files")
@click.option("--verbose", "-v", count=True, help="Verbose output")
def claude_md(project_path: str, from_analysis: Optional[str], template: Optional[str],
             output_file: Optional[str], dry_run: bool, verbose: int):
    """Generate CLAUDE.md file."""
    try:
        path = Path(project_path).resolve()

        if verbose > 0:
            console.print(f"[cyan]Generating CLAUDE.md for: {path}[/cyan]")

        # Get project analysis
        if from_analysis:
            analysis = _load_analysis_from_file(Path(from_analysis))
            if verbose > 0:
                console.print(f"[green]Loaded analysis from: {from_analysis}[/green]")
        else:
            if verbose > 0:
                console.print("[cyan]Analyzing project...[/cyan]")
            analyzer = ProjectAnalyzer()
            analysis = analyzer.analyze(path)

        # Configure generator
        config = {}
        if template:
            config["preferred_template"] = template

        # Generate CLAUDE.md content
        generator = DocumentGenerator(config)
        generated_content = generator.generate(analysis, path)

        # Extract only CLAUDE.md content
        claude_content = generated_content.files.get("CLAUDE.md")
        if not claude_content:
            console.print("[red]Failed to generate CLAUDE.md content[/red]")
            return

        if dry_run or verbose > 0:
            console.print(Panel(
                f"**CLAUDE.md Preview** ({len(claude_content)} characters)\\n\\n"
                f"First 200 characters:\\n{claude_content[:200]}...",
                title="CLAUDE.md Generation Preview"
            ))

        if dry_run:
            console.print("[yellow]Dry run complete - no files were created[/yellow]")
            return

        # Write CLAUDE.md file
        output_path = Path(output_file) if output_file else path / "CLAUDE.md"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(claude_content)

        console.print("[green]✓ CLAUDE.md generated successfully[/green]")
        console.print(f"Output location: {output_path}")

    except Exception as e:
        console.print(f"[red]Error generating CLAUDE.md: {e}[/red]")
        raise click.ClickException(f"Failed to generate CLAUDE.md: {e}")


@generate.command()
@click.argument("project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--from-analysis", type=click.Path(exists=True, file_okay=True),
              help="Use existing analysis file")
@click.option("--agents-dir", type=click.Path(), help="Custom agents directory")
@click.option("--output-file", type=click.Path(), help="Output file (default: AGENTS.md)")
@click.option("--dry-run", is_flag=True, help="Show what would be generated without creating files")
@click.option("--verbose", "-v", count=True, help="Verbose output")
def agents_md(project_path: str, from_analysis: Optional[str], agents_dir: Optional[str],
             output_file: Optional[str], dry_run: bool, verbose: int):
    """Generate AGENTS.md file."""
    try:
        path = Path(project_path).resolve()

        if verbose > 0:
            console.print(f"[cyan]Generating AGENTS.md for: {path}[/cyan]")

        # Get project analysis
        if from_analysis:
            analysis = _load_analysis_from_file(Path(from_analysis))
            if verbose > 0:
                console.print(f"[green]Loaded analysis from: {from_analysis}[/green]")
        else:
            if verbose > 0:
                console.print("[cyan]Analyzing project...[/cyan]")
            analyzer = ProjectAnalyzer()
            analysis = analyzer.analyze(path)

        # Generate agent configuration
        from claude_builder.core.agents import UniversalAgentSystem
        agent_system = UniversalAgentSystem()
        agent_config = agent_system.select_agents(analysis)

        if verbose > 0:
            console.print(f"[green]Selected {len(agent_config.all_agents)} agents[/green]")

        # Generate AGENTS.md content
        generator = DocumentGenerator({"agents_only": True})
        generated_content = generator.generate(analysis, path)

        # Extract only AGENTS.md content
        agents_content = generated_content.files.get("AGENTS.md")
        if not agents_content:
            console.print("[red]Failed to generate AGENTS.md content[/red]")
            return

        if dry_run or verbose > 0:
            console.print(Panel(
                f"**AGENTS.md Preview**\\n\\n"
                f"Core agents: {len(agent_config.core_agents)}\\n"
                f"Domain agents: {len(agent_config.domain_agents)}\\n"
                f"Workflow agents: {len(agent_config.workflow_agents)}\\n"
                f"Custom agents: {len(agent_config.custom_agents)}\\n\\n"
                f"Content size: {len(agents_content)} characters",
                title="AGENTS.md Generation Preview"
            ))

        if dry_run:
            console.print("[yellow]Dry run complete - no files were created[/yellow]")
            return

        # Write AGENTS.md file
        output_path = Path(output_file) if output_file else path / "AGENTS.md"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(agents_content)

        console.print("[green]✓ AGENTS.md generated successfully[/green]")
        console.print(f"Output location: {output_path}")

    except Exception as e:
        console.print(f"[red]Error generating AGENTS.md: {e}[/red]")
        raise click.ClickException(f"Failed to generate AGENTS.md: {e}")
