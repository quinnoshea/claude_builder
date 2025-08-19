"""
Unit tests for the template system components.

Tests the template management and processing including:
- Template loading and validation
- Template rendering and variable substitution
- Template inheritance and composition
- Dynamic template selection
- Template caching and performance
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from claude_builder.core.template_manager import (
    TemplateManager, Template, TemplateLoader, 
    TemplateRenderer, TemplateError, TemplateContext
)


class TestTemplate:
    """Test suite for Template model."""
    
    def test_template_creation(self):
        """Test basic template creation."""
        template = Template(
            name="test-template",
            content="# {{ title }}\n{{ content }}",
            template_type="markdown",
            variables=["title", "content"]
        )
        
        assert template.name == "test-template"
        assert "{{ title }}" in template.content
        assert template.template_type == "markdown"
        assert "title" in template.variables
        assert "content" in template.variables
    
    def test_template_validation_valid(self):
        """Test template validation with valid template."""
        template = Template(
            name="valid-template",
            content="# {{ project_name }}\nType: {{ project_type }}",
            template_type="markdown"
        )
        
        # Should not raise any exceptions
        template.validate()
    
    def test_template_validation_invalid_syntax(self):
        """Test template validation with invalid Jinja2 syntax."""
        template = Template(
            name="invalid-template",
            content="# {{ project_name }\nMissing closing brace",
            template_type="markdown"
        )
        
        with pytest.raises(TemplateError):
            template.validate()
    
    def test_template_variable_extraction(self):
        """Test automatic variable extraction from template content."""
        template = Template(
            name="auto-vars",
            content="""
# {{ project_name }}
Type: {{ project_type }}
Framework: {{ framework }}
{% if has_tests %}
Testing: {{ test_framework }}
{% endif %}
""",
            template_type="markdown"
        )
        
        variables = template.extract_variables()
        
        assert "project_name" in variables
        assert "project_type" in variables
        assert "framework" in variables
        assert "has_tests" in variables
        assert "test_framework" in variables
    
    def test_template_metadata(self):
        """Test template metadata handling."""
        template = Template(
            name="meta-template",
            content="# {{ title }}",
            template_type="markdown",
            metadata={
                "author": "Claude Builder",
                "version": "1.0",
                "description": "Test template with metadata"
            }
        )
        
        assert template.metadata["author"] == "Claude Builder"
        assert template.metadata["version"] == "1.0"
        assert template.metadata["description"] == "Test template with metadata"
    
    def test_template_inheritance_info(self):
        """Test template inheritance information."""
        child_template = Template(
            name="child-template",
            content="{% extends 'base-template' %}\n{% block content %}Child content{% endblock %}",
            template_type="markdown",
            parent_template="base-template"
        )
        
        assert child_template.parent_template == "base-template"
        assert child_template.is_child_template() is True
    
    def test_template_serialization(self):
        """Test template serialization to dictionary."""
        template = Template(
            name="serialize-test",
            content="# {{ title }}",
            template_type="markdown",
            variables=["title"],
            metadata={"version": "1.0"}
        )
        
        data = template.dict()
        
        assert data["name"] == "serialize-test"
        assert data["content"] == "# {{ title }}"
        assert data["template_type"] == "markdown"
        assert "title" in data["variables"]
        assert data["metadata"]["version"] == "1.0"


class TestTemplateContext:
    """Test suite for TemplateContext class."""
    
    def test_context_creation(self):
        """Test template context creation."""
        context = TemplateContext(
            project_name="test-project",
            project_type="python",
            framework="fastapi"
        )
        
        assert context.get("project_name") == "test-project"
        assert context.get("project_type") == "python"
        assert context.get("framework") == "fastapi"
    
    def test_context_nested_data(self):
        """Test template context with nested data structures."""
        context = TemplateContext(
            project={
                "name": "nested-test",
                "type": "rust",
                "metadata": {
                    "version": "0.1.0",
                    "authors": ["Claude Builder"]
                }
            },
            dependencies=["tokio", "serde", "clap"]
        )
        
        assert context.get("project.name") == "nested-test"
        assert context.get("project.type") == "rust"
        assert context.get("project.metadata.version") == "0.1.0"
        assert "tokio" in context.get("dependencies")
    
    def test_context_dynamic_values(self):
        """Test template context with dynamic value generation."""
        def get_current_date():
            return "2024-01-01"
        
        context = TemplateContext(
            project_name="dynamic-test",
            current_date=get_current_date,
            computed_value=lambda: "computed_result"
        )
        
        assert context.get("project_name") == "dynamic-test"
        assert context.get("current_date") == "2024-01-01"
        assert context.get("computed_value") == "computed_result"
    
    def test_context_merging(self):
        """Test merging multiple template contexts."""
        base_context = TemplateContext(
            project_name="base",
            project_type="python"
        )
        
        override_context = TemplateContext(
            project_type="rust",
            framework="axum"
        )
        
        merged = base_context.merge(override_context)
        
        assert merged.get("project_name") == "base"  # From base
        assert merged.get("project_type") == "rust"  # Overridden
        assert merged.get("framework") == "axum"  # From override
    
    def test_context_conditional_values(self):
        """Test template context with conditional value logic."""
        context = TemplateContext(
            project_type="python",
            framework="fastapi"
        )
        
        # Add conditional values
        context.add_conditional("is_python", lambda: context.get("project_type") == "python")
        context.add_conditional("is_web_framework", lambda: context.get("framework") in ["fastapi", "django", "flask"])
        
        assert context.get("is_python") is True
        assert context.get("is_web_framework") is True


class TestTemplateLoader:
    """Test suite for TemplateLoader class."""
    
    def test_loader_initialization(self, temp_dir):
        """Test template loader initialization."""
        loader = TemplateLoader(template_directory=temp_dir)
        
        assert loader.template_directory == temp_dir
        assert len(loader.loaded_templates) == 0
    
    def test_load_template_from_file(self, temp_dir):
        """Test loading template from file."""
        template_file = temp_dir / "test_template.md"
        template_content = """---
name: test-template
type: markdown
variables: [title, content]
---
# {{ title }}

{{ content }}
"""
        template_file.write_text(template_content)
        
        loader = TemplateLoader(template_directory=temp_dir)
        template = loader.load_template("test_template.md")
        
        assert template.name == "test-template"
        assert template.template_type == "markdown"
        assert "title" in template.variables
        assert "{{ title }}" in template.content
    
    def test_load_template_without_frontmatter(self, temp_dir):
        """Test loading template without YAML frontmatter."""
        template_file = temp_dir / "simple_template.md"
        template_content = "# {{ project_name }}\nSimple template content"
        template_file.write_text(template_content)
        
        loader = TemplateLoader(template_directory=temp_dir)
        template = loader.load_template("simple_template.md")
        
        assert template.name == "simple_template.md"
        assert "{{ project_name }}" in template.content
    
    def test_load_all_templates(self, temp_dir):
        """Test loading all templates from directory."""
        # Create multiple template files
        templates = [
            ("template1.md", "# {{ title1 }}"),
            ("template2.md", "# {{ title2 }}"),
            ("template3.md", "# {{ title3 }}")
        ]
        
        for filename, content in templates:
            (temp_dir / filename).write_text(content)
        
        loader = TemplateLoader(template_directory=temp_dir)
        loaded_templates = loader.load_all_templates()
        
        assert len(loaded_templates) == 3
        template_names = [t.name for t in loaded_templates]
        assert "template1.md" in template_names
        assert "template2.md" in template_names
        assert "template3.md" in template_names
    
    def test_load_template_with_inheritance(self, temp_dir):
        """Test loading template with inheritance."""
        # Create base template
        base_template = temp_dir / "base.md"
        base_content = """---
name: base-template
type: markdown
---
# {{ project_name }}
{% block content %}Default content{% endblock %}
"""
        base_template.write_text(base_content)
        
        # Create child template
        child_template = temp_dir / "child.md"
        child_content = """---
name: child-template
type: markdown
extends: base-template
---
{% extends 'base.md' %}
{% block content %}Child-specific content{% endblock %}
"""
        child_template.write_text(child_content)
        
        loader = TemplateLoader(template_directory=temp_dir)
        child = loader.load_template("child.md")
        
        assert child.parent_template == "base-template"
        assert "{% extends 'base.md' %}" in child.content
    
    def test_load_nonexistent_template(self, temp_dir):
        """Test loading nonexistent template."""
        loader = TemplateLoader(template_directory=temp_dir)
        
        with pytest.raises(TemplateError):
            loader.load_template("nonexistent.md")
    
    def test_template_caching(self, temp_dir):
        """Test template caching mechanism."""
        template_file = temp_dir / "cached_template.md"
        template_file.write_text("# {{ title }}")
        
        loader = TemplateLoader(template_directory=temp_dir)
        
        # Load template twice
        template1 = loader.load_template("cached_template.md")
        template2 = loader.load_template("cached_template.md")
        
        # Should be the same object (cached)
        assert template1 is template2
        assert len(loader.loaded_templates) == 1


class TestTemplateRenderer:
    """Test suite for TemplateRenderer class."""
    
    def test_renderer_initialization(self):
        """Test template renderer initialization."""
        renderer = TemplateRenderer()
        
        assert renderer.jinja_env is not None
        assert renderer.render_cache is not None
    
    def test_render_simple_template(self):
        """Test rendering simple template."""
        template = Template(
            name="simple",
            content="# {{ title }}\n{{ content }}",
            template_type="markdown"
        )
        
        context = TemplateContext(
            title="Test Title",
            content="Test content here"
        )
        
        renderer = TemplateRenderer()
        result = renderer.render(template, context)
        
        assert "# Test Title" in result
        assert "Test content here" in result
    
    def test_render_template_with_loops(self):
        """Test rendering template with loops."""
        template = Template(
            name="loop-test",
            content="""# Dependencies
{% for dep in dependencies %}
- {{ dep.name }}: {{ dep.version }}
{% endfor %}""",
            template_type="markdown"
        )
        
        context = TemplateContext(
            dependencies=[
                {"name": "fastapi", "version": "0.100.0"},
                {"name": "uvicorn", "version": "0.23.0"}
            ]
        )
        
        renderer = TemplateRenderer()
        result = renderer.render(template, context)
        
        assert "- fastapi: 0.100.0" in result
        assert "- uvicorn: 0.23.0" in result
    
    def test_render_template_with_conditionals(self):
        """Test rendering template with conditional logic."""
        template = Template(
            name="conditional-test",
            content="""# {{ project_name }}
{% if has_tests %}
## Testing
Test framework: {{ test_framework }}
{% endif %}
{% if not has_docker %}
Note: Docker configuration not detected
{% endif %}""",
            template_type="markdown"
        )
        
        context = TemplateContext(
            project_name="Conditional Test",
            has_tests=True,
            test_framework="pytest",
            has_docker=False
        )
        
        renderer = TemplateRenderer()
        result = renderer.render(template, context)
        
        assert "# Conditional Test" in result
        assert "Test framework: pytest" in result
        assert "Docker configuration not detected" in result
    
    def test_render_template_with_filters(self):
        """Test rendering template with Jinja2 filters."""
        template = Template(
            name="filter-test",
            content="""# {{ title | title }}
Project: {{ project_name | upper }}
Created: {{ date | strftime('%Y-%m-%d') }}
Dependencies: {{ dependencies | length }} total""",
            template_type="markdown"
        )
        
        from datetime import datetime
        
        context = TemplateContext(
            title="test project",
            project_name="filter-test",
            date=datetime(2024, 1, 1),
            dependencies=["dep1", "dep2", "dep3"]
        )
        
        renderer = TemplateRenderer()
        result = renderer.render(template, context)
        
        assert "# Test Project" in result  # title filter
        assert "Project: FILTER-TEST" in result  # upper filter
        assert "Dependencies: 3 total" in result  # length filter
    
    def test_render_template_with_inheritance(self, temp_dir):
        """Test rendering template with inheritance."""
        # This would require setting up Jinja2 template inheritance
        # which is more complex and might be better tested in integration tests
        pass
    
    def test_render_template_error_handling(self):
        """Test template rendering error handling."""
        template = Template(
            name="error-test",
            content="# {{ undefined_variable }}",
            template_type="markdown"
        )
        
        context = TemplateContext(defined_variable="value")
        
        renderer = TemplateRenderer()
        
        with pytest.raises(TemplateError):
            renderer.render(template, context)
    
    def test_render_caching(self):
        """Test template render result caching."""
        template = Template(
            name="cache-test",
            content="# {{ title }}\nGenerated at: {{ timestamp }}",
            template_type="markdown"
        )
        
        context = TemplateContext(
            title="Cache Test",
            timestamp="2024-01-01 12:00:00"
        )
        
        renderer = TemplateRenderer(enable_cache=True)
        
        # Render twice with same context
        result1 = renderer.render(template, context)
        result2 = renderer.render(template, context)
        
        # Results should be identical (cached)
        assert result1 == result2
        assert renderer.cache_hits > 0


class TestTemplateManager:
    """Test suite for TemplateManager class."""
    
    def test_manager_initialization(self, temp_dir):
        """Test template manager initialization."""
        manager = TemplateManager(template_directory=temp_dir)
        
        assert manager.loader is not None
        assert manager.renderer is not None
        assert len(manager.templates) == 0
    
    def test_get_template_by_name(self, temp_dir):
        """Test getting template by name."""
        template_file = temp_dir / "test.md"
        template_file.write_text("# {{ title }}")
        
        manager = TemplateManager(template_directory=temp_dir)
        template = manager.get_template("test.md")
        
        assert template is not None
        assert template.name == "test.md"
    
    def test_get_templates_by_type(self, temp_dir):
        """Test getting templates by type."""
        # Create templates of different types
        (temp_dir / "doc1.md").write_text("---\ntype: documentation\n---\n# {{ title }}")
        (temp_dir / "guide1.md").write_text("---\ntype: guide\n---\n# {{ title }}")
        (temp_dir / "doc2.md").write_text("---\ntype: documentation\n---\n# {{ title }}")
        
        manager = TemplateManager(template_directory=temp_dir)
        
        doc_templates = manager.get_templates_by_type("documentation")
        guide_templates = manager.get_templates_by_type("guide")
        
        assert len(doc_templates) == 2
        assert len(guide_templates) == 1
    
    def test_render_template_by_name(self, temp_dir):
        """Test rendering template by name."""
        template_file = temp_dir / "render_test.md"
        template_file.write_text("# {{ project_name }}\nType: {{ project_type }}")
        
        manager = TemplateManager(template_directory=temp_dir)
        
        context = TemplateContext(
            project_name="Render Test",
            project_type="python"
        )
        
        result = manager.render_template("render_test.md", context)
        
        assert "# Render Test" in result
        assert "Type: python" in result
    
    def test_template_selection_by_project_type(self, temp_dir):
        """Test automatic template selection by project type."""
        # Create project-specific templates
        (temp_dir / "python_claude.md").write_text("---\nproject_types: [python]\n---\nPython project: {{ name }}")
        (temp_dir / "rust_claude.md").write_text("---\nproject_types: [rust]\n---\nRust project: {{ name }}")
        (temp_dir / "generic_claude.md").write_text("---\nproject_types: []\n---\nGeneric project: {{ name }}")
        
        manager = TemplateManager(template_directory=temp_dir)
        
        python_template = manager.select_template_for_project("claude", "python")
        rust_template = manager.select_template_for_project("claude", "rust")
        unknown_template = manager.select_template_for_project("claude", "unknown")
        
        assert "python_claude.md" in python_template.name
        assert "rust_claude.md" in rust_template.name
        assert "generic_claude.md" in unknown_template.name
    
    def test_batch_rendering(self, temp_dir):
        """Test batch rendering of multiple templates."""
        # Create multiple templates
        templates = {
            "claude.md": "# {{ project_name }} - Claude Instructions",
            "readme.md": "# {{ project_name }}\n{{ description }}",
            "guide.md": "# Development Guide for {{ project_name }}"
        }
        
        for filename, content in templates.items():
            (temp_dir / filename).write_text(content)
        
        manager = TemplateManager(template_directory=temp_dir)
        
        context = TemplateContext(
            project_name="Batch Test",
            description="Test batch rendering"
        )
        
        results = manager.render_all_templates(context)
        
        assert len(results) == 3
        assert "claude.md" in results
        assert "readme.md" in results
        assert "guide.md" in results
        assert "# Batch Test - Claude Instructions" in results["claude.md"]
        assert "Test batch rendering" in results["readme.md"]


class TestTemplateError:
    """Test suite for TemplateError exception."""
    
    def test_template_error_creation(self):
        """Test TemplateError exception creation."""
        error = TemplateError("Template rendering failed")
        assert str(error) == "Template rendering failed"
    
    def test_template_error_with_template_info(self):
        """Test TemplateError with template information."""
        error = TemplateError(
            "Variable 'undefined_var' not found",
            template_name="test-template",
            line_number=5
        )
        
        assert "undefined_var" in str(error)
        assert error.template_name == "test-template"
        assert error.line_number == 5