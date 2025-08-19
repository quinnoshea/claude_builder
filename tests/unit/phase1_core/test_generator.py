"""Tests for Phase 1 core functionality: Document Generator.

Tests cover the document generation capabilities including:
- Template loading and processing
- Variable substitution
- Content generation for different project types
- Output formatting and file organization
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from claude_builder.core.generator import DocumentGenerator, TemplateLoader
from claude_builder.core.models import ProjectType, ComplexityLevel
from tests.conftest import assert_file_exists, assert_directory_structure


@pytest.mark.unit
@pytest.mark.phase1
class TestDocumentGenerator:
    """Test the main DocumentGenerator class."""

    def test_generator_initialization(self, default_config):
        """Test generator initializes with correct defaults."""
        generator = DocumentGenerator()
        assert generator is not None
        assert hasattr(generator, 'template_loader')

    def test_generator_with_config(self):
        """Test generator initializes with custom configuration."""
        config = {
            'template_paths': ['./custom_templates/'],
            'output_format': 'markdown',
            'validate_output': True
        }
        generator = DocumentGenerator(config=config)
        assert generator.config['template_paths'] == ['./custom_templates/']
        assert generator.config['validate_output'] is True

    def test_generate_python_project_docs(self, sample_analysis, temp_dir):
        """Test document generation for Python project."""
        # Update analysis for Python
        sample_analysis.language_info.primary = "python"
        sample_analysis.project_type = ProjectType.CLI_TOOL
        
        generator = DocumentGenerator()
        result = generator.generate(sample_analysis, temp_dir)
        
        assert result is not None
        assert hasattr(result, 'files')
        assert isinstance(result.files, dict)
        
        # Check core files are generated
        expected_files = ["CLAUDE.md", "AGENTS.md"]
        for file_name in expected_files:
            assert file_name in result.files
            assert len(result.files[file_name]) > 0

    def test_generate_rust_project_docs(self, sample_analysis, temp_dir):
        """Test document generation for Rust project."""
        # Update analysis for Rust
        sample_analysis.language_info.primary = "rust"
        sample_analysis.project_type = ProjectType.CLI_TOOL
        sample_analysis.build_system = "cargo"
        
        generator = DocumentGenerator()
        result = generator.generate(sample_analysis, temp_dir)
        
        assert "CLAUDE.md" in result.files
        claude_content = result.files["CLAUDE.md"]
        assert "rust" in claude_content.lower()
        assert "cargo" in claude_content.lower()

    def test_generate_web_api_docs(self, sample_analysis, temp_dir):
        """Test document generation for web API project."""
        # Update analysis for web API
        sample_analysis.project_type = ProjectType.WEB_API
        sample_analysis.framework_info.primary = "fastapi"
        
        generator = DocumentGenerator()
        result = generator.generate(sample_analysis, temp_dir)
        
        claude_content = result.files["CLAUDE.md"]
        assert "api" in claude_content.lower()
        assert "web" in claude_content.lower()
        
        agents_content = result.files["AGENTS.md"]
        assert "backend-architect" in agents_content or "api-designer" in agents_content

    def test_generate_with_custom_templates(self, sample_analysis, temp_dir):
        """Test generation with custom template paths."""
        # Create custom template directory
        custom_templates = temp_dir / "custom_templates"
        custom_templates.mkdir()
        (custom_templates / "custom_claude.md").write_text("# Custom Claude Instructions\n${project_name}")
        
        config = {
            'template_paths': [str(custom_templates)],
            'custom_template_mapping': {
                'CLAUDE.md': 'custom_claude.md'
            }
        }
        generator = DocumentGenerator(config=config)
        result = generator.generate(sample_analysis, temp_dir)
        
        assert "CLAUDE.md" in result.files
        assert "Custom Claude Instructions" in result.files["CLAUDE.md"]

    def test_generate_with_complexity_adaptation(self, sample_analysis, temp_dir):
        """Test that generation adapts to project complexity."""
        # Test simple complexity
        sample_analysis.complexity_level = ComplexityLevel.SIMPLE
        generator = DocumentGenerator()
        simple_result = generator.generate(sample_analysis, temp_dir)
        
        # Test high complexity
        sample_analysis.complexity_level = ComplexityLevel.HIGH
        complex_result = generator.generate(sample_analysis, temp_dir)
        
        # Complex projects should have more comprehensive documentation
        simple_content = simple_result.files["CLAUDE.md"]
        complex_content = complex_result.files["CLAUDE.md"]
        
        assert len(complex_content) >= len(simple_content)

    def test_variable_substitution(self, sample_analysis, temp_dir):
        """Test template variable substitution."""
        generator = DocumentGenerator()
        result = generator.generate(sample_analysis, temp_dir)
        
        claude_content = result.files["CLAUDE.md"]
        
        # Check that variables have been substituted
        assert "${project_name}" not in claude_content
        assert "${language}" not in claude_content
        assert "${framework}" not in claude_content
        
        # Check that actual values are present
        assert str(sample_analysis.project_path.name) in claude_content or "test" in claude_content.lower()

    def test_generate_without_framework(self, sample_analysis, temp_dir):
        """Test generation when no framework is detected."""
        sample_analysis.framework_info.primary = None
        sample_analysis.framework_info.confidence = 0
        
        generator = DocumentGenerator()
        result = generator.generate(sample_analysis, temp_dir)
        
        assert "CLAUDE.md" in result.files
        # Should still generate valid content without framework-specific content
        assert len(result.files["CLAUDE.md"]) > 100

    def test_generate_with_domain_features(self, sample_analysis, temp_dir):
        """Test generation includes domain-specific features."""
        # Add domain features
        sample_analysis.domain_info.domain = "e_commerce"
        sample_analysis.domain_info.features = ["payment_processing", "inventory", "user_auth"]
        
        generator = DocumentGenerator()
        result = generator.generate(sample_analysis, temp_dir)
        
        content = result.files["CLAUDE.md"]
        # Should include domain-specific guidance
        assert any(feature in content.lower() for feature in ["payment", "inventory", "auth"])

    def test_output_validation(self, sample_analysis, temp_dir):
        """Test output validation functionality."""
        config = {'validate_output': True}
        generator = DocumentGenerator(config=config)
        
        result = generator.generate(sample_analysis, temp_dir)
        
        # All generated files should be valid
        for filename, content in result.files.items():
            assert isinstance(content, str)
            assert len(content) > 0
            # Basic markdown validation for .md files
            if filename.endswith('.md'):
                assert content.count('#') >= 1  # Should have at least one header

    def test_incremental_generation(self, sample_analysis, temp_dir):
        """Test incremental generation doesn't overwrite existing files."""
        generator = DocumentGenerator()
        
        # First generation
        result1 = generator.generate(sample_analysis, temp_dir)
        
        # Modify analysis slightly
        sample_analysis.complexity_level = ComplexityLevel.HIGH
        
        # Second generation
        result2 = generator.generate(sample_analysis, temp_dir)
        
        # Should generate new content
        assert result1.files != result2.files


@pytest.mark.unit
@pytest.mark.phase1
class TestTemplateLoader:
    """Test the TemplateLoader component."""

    def test_template_loader_initialization(self):
        """Test template loader initializes correctly."""
        loader = TemplateLoader()
        assert loader is not None
        assert hasattr(loader, 'template_paths')

    def test_load_base_templates(self):
        """Test loading of base templates."""
        loader = TemplateLoader()
        
        # Should be able to load base templates
        claude_template = loader.load_template('claude_instructions.md', 'base')
        assert claude_template is not None
        assert isinstance(claude_template, str)
        assert len(claude_template) > 0

    def test_load_language_specific_templates(self):
        """Test loading of language-specific templates."""
        loader = TemplateLoader()
        
        # Test Python templates
        python_template = loader.load_template('claude_instructions.md', 'languages/python')
        assert python_template is not None
        assert "python" in python_template.lower()

    def test_load_framework_specific_templates(self):
        """Test loading of framework-specific templates."""
        loader = TemplateLoader()
        
        # Test FastAPI templates
        fastapi_template = loader.load_template('claude_instructions.md', 'frameworks/fastapi')
        assert fastapi_template is not None
        assert "fastapi" in fastapi_template.lower()

    def test_template_inheritance(self):
        """Test template inheritance and merging."""
        loader = TemplateLoader()
        
        # Load base and specific templates
        base_template = loader.load_template('claude_instructions.md', 'base')
        python_template = loader.load_template('claude_instructions.md', 'languages/python')
        
        # Both should be different
        assert base_template != python_template
        
        # Python template should be more specific
        assert "python" in python_template.lower()

    def test_custom_template_paths(self, temp_dir):
        """Test loading templates from custom paths."""
        # Create custom template
        custom_path = temp_dir / "custom_templates"
        custom_path.mkdir()
        template_file = custom_path / "test_template.md"
        template_file.write_text("# Custom Template\nContent: ${variable}")
        
        loader = TemplateLoader(template_paths=[str(custom_path)])
        
        # Should be able to load custom template
        template = loader.load_template('test_template.md')
        assert template is not None
        assert "Custom Template" in template

    def test_template_not_found(self):
        """Test handling of missing templates."""
        loader = TemplateLoader()
        
        # Should handle missing templates gracefully
        template = loader.load_template('nonexistent_template.md')
        assert template is None or template == ""

    def test_template_variable_extraction(self):
        """Test extraction of template variables."""
        loader = TemplateLoader()
        
        template_content = "Hello ${name}, your ${project_type} project uses ${language}."
        variables = loader.extract_variables(template_content)
        
        expected_vars = {"name", "project_type", "language"}
        assert variables == expected_vars

    def test_template_substitution(self, sample_analysis):
        """Test template variable substitution."""
        loader = TemplateLoader()
        
        template_content = "Project: ${project_name}\nLanguage: ${language}\nType: ${project_type}"
        
        variables = {
            'project_name': sample_analysis.project_path.name,
            'language': sample_analysis.language_info.primary,
            'project_type': sample_analysis.project_type.value
        }
        
        result = loader.substitute_variables(template_content, variables)
        
        assert "${project_name}" not in result
        assert sample_analysis.project_path.name in result
        assert sample_analysis.language_info.primary in result

    def test_conditional_template_sections(self):
        """Test conditional template sections."""
        loader = TemplateLoader()
        
        template_content = """
# Base Content

{{#if framework}}
## Framework: ${framework}
Framework-specific content here.
{{/if}}

{{#if has_tests}}
## Testing
Testing configuration here.
{{/if}}
"""
        
        # Test with framework
        variables = {'framework': 'fastapi', 'has_tests': True}
        result = loader.substitute_variables(template_content, variables)
        
        assert "Framework: fastapi" in result
        assert "Testing" in result
        
        # Test without framework
        variables = {'has_tests': False}
        result = loader.substitute_variables(template_content, variables)
        
        assert "Framework:" not in result
        assert "Testing configuration" not in result


@pytest.mark.unit
@pytest.mark.phase1
class TestOutputGeneration:
    """Test output generation and file organization."""

    def test_file_organization(self, sample_analysis, temp_dir):
        """Test that generated files are properly organized."""
        generator = DocumentGenerator()
        result = generator.generate(sample_analysis, temp_dir)
        
        # Check core files exist
        core_files = ["CLAUDE.md", "AGENTS.md"]
        for file_name in core_files:
            assert file_name in result.files
        
        # Check file structure is logical
        assert len(result.files) >= 2

    def test_content_quality(self, sample_analysis, temp_dir):
        """Test quality of generated content."""
        generator = DocumentGenerator()
        result = generator.generate(sample_analysis, temp_dir)
        
        for filename, content in result.files.items():
            # Basic quality checks
            assert len(content) > 50  # Not empty or trivial
            assert content.strip() != ""  # Not just whitespace
            
            if filename.endswith('.md'):
                # Markdown-specific checks
                assert content.startswith('#')  # Has header
                assert '\n' in content  # Multi-line content

    def test_project_specific_customization(self, sample_analysis, temp_dir):
        """Test that content is customized for specific project characteristics."""
        generator = DocumentGenerator()
        
        # Test Python CLI project
        sample_analysis.language_info.primary = "python"
        sample_analysis.project_type = ProjectType.CLI_TOOL
        python_result = generator.generate(sample_analysis, temp_dir)
        
        # Test Rust web API project
        sample_analysis.language_info.primary = "rust"
        sample_analysis.project_type = ProjectType.WEB_API
        sample_analysis.framework_info.primary = "axum"
        rust_result = generator.generate(sample_analysis, temp_dir)
        
        # Content should be different and project-specific
        python_content = python_result.files["CLAUDE.md"]
        rust_content = rust_result.files["CLAUDE.md"]
        
        assert python_content != rust_content
        assert "python" in python_content.lower()
        assert "rust" in rust_content.lower()

    def test_metadata_preservation(self, sample_analysis, temp_dir):
        """Test that project metadata is preserved in generated content."""
        generator = DocumentGenerator()
        result = generator.generate(sample_analysis, temp_dir)
        
        # Check that analysis metadata is reflected in output
        metadata = result.metadata if hasattr(result, 'metadata') else {}
        
        # Should preserve key analysis information
        content = result.files["CLAUDE.md"]
        assert sample_analysis.language_info.primary in content.lower()

    def test_error_handling(self, temp_dir):
        """Test error handling in document generation."""
        generator = DocumentGenerator()
        
        # Test with invalid analysis
        invalid_analysis = Mock()
        invalid_analysis.project_path = temp_dir / "nonexistent"
        invalid_analysis.language_info = Mock()
        invalid_analysis.language_info.primary = None
        
        # Should handle gracefully
        try:
            result = generator.generate(invalid_analysis, temp_dir)
            # Should either succeed with default content or raise appropriate error
            assert result is not None
        except Exception as e:
            # If it raises an error, it should be a meaningful one
            assert isinstance(e, (ValueError, TypeError, FileNotFoundError))

    def test_performance_with_large_project(self, temp_dir):
        """Test generation performance with large project analysis."""
        from claude_builder.core.models import ProjectAnalysis, LanguageInfo, FilesystemInfo
        
        # Create analysis for large project
        large_analysis = ProjectAnalysis(
            project_path=temp_dir,
            language_info=LanguageInfo(primary="python", confidence=95.0),
            filesystem_info=FilesystemInfo(
                total_files=1000,
                source_files=800,
                test_files=150,
                config_files=50
            ),
            project_type=ProjectType.WEB_API,
            complexity_level=ComplexityLevel.HIGH,
            analysis_confidence=90.0
        )
        
        generator = DocumentGenerator()
        
        # Should complete in reasonable time
        import time
        start_time = time.time()
        result = generator.generate(large_analysis, temp_dir)
        end_time = time.time()
        
        # Should complete within 5 seconds even for large projects
        assert end_time - start_time < 5.0
        assert result is not None