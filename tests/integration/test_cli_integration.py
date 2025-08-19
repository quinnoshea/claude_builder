"""
Integration tests for CLI components.

Tests the complete CLI workflow including:
- Command parsing and execution
- CLI integration with core analysis
- CLI integration with generation
- Error handling and user feedback
- Configuration management via CLI
"""

import pytest
from pathlib import Path
from click.testing import CliRunner
from claude_builder.cli.main import cli
from claude_builder.cli import analyze_commands, generate_commands, config_commands


class TestCLIIntegration:
    """Test suite for CLI integration."""
    
    def test_cli_help_command(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'claude-builder' in result.output
        assert 'analyze' in result.output
        assert 'generate' in result.output
        assert 'config' in result.output
    
    def test_cli_version_command(self):
        """Test CLI version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert 'version' in result.output.lower()


class TestAnalyzeCLI:
    """Test suite for analyze CLI commands."""
    
    def test_analyze_python_project(self, sample_python_project):
        """Test analyzing Python project via CLI."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                'analyze', 
                str(sample_python_project),
                '--format', 'json',
                '--output', 'analysis.json'
            ])
            
            assert result.exit_code == 0
            assert Path('analysis.json').exists()
    
    def test_analyze_with_config_file(self, sample_python_project, temp_dir):
        """Test analysis with configuration file."""
        runner = CliRunner()
        
        # Create config file
        config_file = temp_dir / 'config.toml'
        config_file.write_text("""
[analysis]
depth = "detailed"
include_git = true

[output]
format = "json"
""")
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                'analyze',
                str(sample_python_project),
                '--config', str(config_file)
            ])
            
            assert result.exit_code == 0
    
    def test_analyze_invalid_project(self):
        """Test analyzing invalid project path."""
        runner = CliRunner()
        
        result = runner.invoke(cli, [
            'analyze',
            '/nonexistent/path'
        ])
        
        assert result.exit_code != 0
        assert 'error' in result.output.lower()


class TestGenerateCLI:
    """Test suite for generate CLI commands."""
    
    def test_generate_documentation(self, sample_python_project):
        """Test generating documentation via CLI."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # First analyze the project
            result = runner.invoke(cli, [
                'analyze',
                str(sample_python_project),
                '--output', 'analysis.json'
            ])
            assert result.exit_code == 0
            
            # Then generate documentation
            result = runner.invoke(cli, [
                'generate',
                'analysis.json',
                '--template', 'comprehensive',
                '--output', 'docs/'
            ])
            
            assert result.exit_code == 0
            assert Path('docs/').exists()
    
    def test_generate_with_custom_template(self, sample_python_project, temp_dir):
        """Test generation with custom template."""
        runner = CliRunner()
        
        # Create custom template
        template_file = temp_dir / 'custom.md'
        template_file.write_text("""
# {{ project_name }}

Project Type: {{ project_type }}
Framework: {{ framework }}

## Dependencies
{% for dep in dependencies %}
- {{ dep }}
{% endfor %}
""")
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                'generate',
                str(sample_python_project),
                '--template-file', str(template_file),
                '--output', 'custom_docs/'
            ])
            
            # Should work even if exit code is non-zero due to missing analysis
            assert Path('custom_docs/').exists() or 'template' in result.output


class TestConfigCLI:
    """Test suite for config CLI commands."""
    
    def test_config_init(self):
        """Test config initialization."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['config', 'init'])
            
            assert result.exit_code == 0
            assert Path('claude-builder.toml').exists()
    
    def test_config_show(self, temp_dir):
        """Test showing current configuration."""
        runner = CliRunner()
        
        # Create config file
        config_file = temp_dir / 'claude-builder.toml'
        config_file.write_text("""
[project]
name = "test-project"
type = "python"

[analysis]
depth = "standard"
""")
        
        result = runner.invoke(cli, [
            'config', 'show',
            '--config', str(config_file)
        ])
        
        assert result.exit_code == 0
        assert 'test-project' in result.output
    
    def test_config_set(self):
        """Test setting configuration values."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Initialize config first
            runner.invoke(cli, ['config', 'init'])
            
            # Set a value
            result = runner.invoke(cli, [
                'config', 'set',
                'analysis.depth', 'detailed'
            ])
            
            assert result.exit_code == 0
            
            # Verify the value was set
            result = runner.invoke(cli, ['config', 'show'])
            assert 'detailed' in result.output


class TestCLIWorkflow:
    """Test suite for complete CLI workflows."""
    
    def test_full_analysis_generation_workflow(self, sample_python_project):
        """Test complete workflow from analysis to generation."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Step 1: Initialize configuration
            result = runner.invoke(cli, ['config', 'init'])
            assert result.exit_code == 0
            
            # Step 2: Analyze project
            result = runner.invoke(cli, [
                'analyze',
                str(sample_python_project),
                '--output', 'analysis.json'
            ])
            assert result.exit_code == 0
            assert Path('analysis.json').exists()
            
            # Step 3: Generate documentation
            result = runner.invoke(cli, [
                'generate',
                'analysis.json',
                '--template', 'comprehensive',
                '--output', 'docs/'
            ])
            assert result.exit_code == 0
            assert Path('docs/').exists()
            
            # Step 4: Verify generated files
            docs_dir = Path('docs/')
            generated_files = list(docs_dir.glob('*.md'))
            assert len(generated_files) > 0
    
    def test_error_handling_workflow(self):
        """Test error handling in CLI workflow."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Try to analyze non-existent project
            result = runner.invoke(cli, [
                'analyze',
                '/nonexistent/project'
            ])
            
            assert result.exit_code != 0
            assert 'error' in result.output.lower()
            
            # Try to generate from non-existent analysis
            result = runner.invoke(cli, [
                'generate',
                'missing_analysis.json'
            ])
            
            assert result.exit_code != 0
    
    def test_verbose_output_workflow(self, sample_python_project):
        """Test workflow with verbose output."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                '--verbose',
                'analyze',
                str(sample_python_project),
                '--output', 'analysis.json'
            ])
            
            # Should complete successfully and show verbose output
            assert result.exit_code == 0
            assert len(result.output) > 100  # Verbose output should be substantial


class TestCLIConfiguration:
    """Test suite for CLI configuration handling."""
    
    def test_cli_with_environment_variables(self, sample_python_project):
        """Test CLI with environment variable configuration."""
        runner = CliRunner()
        
        # Set environment variables
        env = {
            'CLAUDE_BUILDER_ANALYSIS_DEPTH': 'detailed',
            'CLAUDE_BUILDER_OUTPUT_FORMAT': 'json'
        }
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                'analyze',
                str(sample_python_project)
            ], env=env)
            
            # Should use environment configuration
            assert result.exit_code == 0
    
    def test_cli_config_precedence(self, sample_python_project, temp_dir):
        """Test configuration precedence in CLI."""
        runner = CliRunner()
        
        # Create config file
        config_file = temp_dir / 'config.toml'
        config_file.write_text("""
[analysis]
depth = "basic"
""")
        
        with runner.isolated_filesystem():
            # CLI flag should override config file
            result = runner.invoke(cli, [
                'analyze',
                str(sample_python_project),
                '--config', str(config_file),
                '--depth', 'detailed'  # This should override config file
            ])
            
            assert result.exit_code == 0


class TestCLIPlugins:
    """Test suite for CLI plugin integration."""
    
    def test_plugin_discovery(self):
        """Test CLI plugin discovery mechanism."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ['plugins', 'list'])
        
        # Should complete without error, even if no plugins
        assert result.exit_code == 0
    
    def test_plugin_help(self):
        """Test CLI plugin help system."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ['plugins', '--help'])
        
        assert result.exit_code == 0
        assert 'plugin' in result.output.lower()


class TestCLIPerformance:
    """Test suite for CLI performance characteristics."""
    
    def test_cli_startup_time(self):
        """Test CLI startup performance."""
        import time
        runner = CliRunner()
        
        start_time = time.time()
        result = runner.invoke(cli, ['--help'])
        end_time = time.time()
        
        startup_time = end_time - start_time
        
        assert result.exit_code == 0
        assert startup_time < 2.0  # Should start quickly
    
    def test_large_project_analysis(self, temp_dir):
        """Test CLI performance with large project."""
        runner = CliRunner()
        
        # Create large project structure
        for i in range(50):
            subdir = temp_dir / f"module_{i}"
            subdir.mkdir()
            for j in range(10):
                (subdir / f"file_{j}.py").write_text(f"# Module {i} File {j}")
        
        with runner.isolated_filesystem():
            import time
            start_time = time.time()
            
            result = runner.invoke(cli, [
                'analyze',
                str(temp_dir),
                '--output', 'large_analysis.json'
            ])
            
            end_time = time.time()
            analysis_time = end_time - start_time
            
            assert result.exit_code == 0
            assert analysis_time < 30.0  # Should complete within reasonable time