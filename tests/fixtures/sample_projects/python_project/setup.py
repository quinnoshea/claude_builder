from setuptools import setup, find_packages

setup(
    name="test-project",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "click>=8.0.0",
    ],
    author="Test Author",
    author_email="test@example.com",
    description="A test project for claude_builder testing",
)