#!/bin/bash
set -e

echo "🔍 Testing CI pipeline locally..."
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Clean previous runs
echo -e "${BLUE}🧹 Cleaning previous test runs...${NC}"
rm -rf htmlcov coverage.xml .coverage .pytest_cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Check if we're in a virtual environment
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo -e "${YELLOW}⚠️  Warning: Not in a virtual environment. Consider activating one.${NC}"
fi

# Install dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
if command -v uv &> /dev/null; then
    echo "Using uv for package management..."
    uv pip install -e ".[dev,test]"
elif command -v pipx &> /dev/null; then
    echo "Using pipx for package management..."
    pipx install -e ".[dev,test]"
else
    echo "Using pip as fallback..."
    python3 -m pip install --upgrade pip
    pip install -e ".[dev,test]"
fi

# Check Python path setup
echo -e "${BLUE}🔍 Checking Python path setup...${NC}"
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
echo "PYTHONPATH: $PYTHONPATH"

# Run linting
echo -e "${BLUE}🔍 Running code quality checks...${NC}"

echo "  • Running ruff..."
uv run ruff check src/claude_builder || {
    echo -e "${YELLOW}⚠️  Ruff found issues (non-fatal)${NC}"
}

echo "  • Running black format check..."
uv run black --check src/claude_builder tests || {
    echo -e "${YELLOW}⚠️  Black format issues found (non-fatal)${NC}"
}

echo "  • Running mypy type checking..."
uv run mypy src/claude_builder --ignore-missing-imports || {
    echo -e "${YELLOW}⚠️  MyPy found type issues (non-fatal)${NC}"
}

# Run security checks
echo -e "${BLUE}🔒 Running security checks...${NC}"

echo "  • Running bandit security scan..."
uv run bandit -r src/claude_builder -f json -o bandit-report.json || {
    echo -e "${YELLOW}⚠️  Bandit found potential security issues (non-fatal)${NC}"
}

echo "  • Running safety dependency check..."
uv run safety check --json > safety-report.json || {
    echo -e "${YELLOW}⚠️  Safety found dependency issues (non-fatal)${NC}"
}

# Run tests with coverage
echo -e "${BLUE}🧪 Running tests with coverage...${NC}"
uv run pytest \
  --cov=claude_builder \
  --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov \
  --cov-report=term-missing \
  --junitxml=junit.xml \
  -v

# Check if coverage file was generated
if [[ -f "coverage.xml" ]]; then
    echo -e "${GREEN}✅ Coverage report generated successfully${NC}"

    # Show coverage summary
    echo -e "${BLUE}📊 Coverage Summary:${NC}"
    uv run coverage report

    # Fix coverage paths
    echo -e "${BLUE}🔧 Fixing coverage paths for external tools...${NC}"
    uv run python scripts/fix_coverage_paths.py coverage.xml

    echo -e "${GREEN}✅ Coverage paths fixed for Codacy${NC}"
else
    echo -e "${RED}❌ Coverage report not generated${NC}"
fi

# Test specific phase markers
echo -e "${BLUE}🧪 Testing phase-specific test markers...${NC}"

echo "  • Running Phase 1 tests (core functionality)..."
pytest -m "phase1" --tb=short || {
    echo -e "${YELLOW}⚠️  Some Phase 1 tests failed${NC}"
}

echo "  • Running Phase 2 tests (intelligence layer)..."
pytest -m "phase2" --tb=short || {
    echo -e "${YELLOW}⚠️  Some Phase 2 tests failed${NC}"
}

echo "  • Running Phase 3 tests (advanced features)..."
pytest -m "phase3" --tb=short || {
    echo -e "${YELLOW}⚠️  Some Phase 3 tests failed${NC}"
}

# Check CLI installation
echo -e "${BLUE}🔧 Testing CLI installation...${NC}"
uv pip install . || {
    echo -e "${RED}❌ CLI installation failed${NC}"
    exit 1
}

echo "  • Testing claude-builder --help..."
claude-builder --help > /dev/null || {
    echo -e "${RED}❌ CLI help command failed${NC}"
    exit 1
}

echo "  • Testing claude-builder --version..."
claude-builder --version > /dev/null || {
    echo -e "${RED}❌ CLI version command failed${NC}"
    exit 1
}

# Generate summary report
echo -e "${BLUE}📋 Generating test summary...${NC}"

# Count test results
TOTAL_TESTS=$(uv run pytest --collect-only -q 2>/dev/null | grep -o '[0-9]\+ item' | head -1 | cut -d' ' -f1 || echo "unknown")
FAILED_TESTS=$(grep -c 'failed' junit.xml 2>/dev/null || echo "0")
COVERAGE_PERCENT=$(uv run coverage report --format=total 2>/dev/null || echo "unknown")

echo ""
echo "================================="
echo -e "${GREEN}🎉 Local CI Test Complete!${NC}"
echo "================================="
echo "📊 Test Summary:"
echo "  • Total tests: $TOTAL_TESTS"
echo "  • Failed tests: $FAILED_TESTS"
echo "  • Coverage: ${COVERAGE_PERCENT}%"
echo ""
echo "📁 Generated files:"
echo "  • coverage.xml (fixed for Codacy)"
echo "  • htmlcov/ (HTML coverage report)"
echo "  • junit.xml (test results)"
echo "  • bandit-report.json (security scan)"
echo "  • safety-report.json (dependency scan)"
echo ""

if [[ -f "coverage.xml" ]]; then
    echo -e "${GREEN}✅ Ready for Codacy upload!${NC}"
else
    echo -e "${RED}❌ Coverage file missing - check test configuration${NC}"
fi

echo ""
echo "💡 Next steps:"
echo "  1. Review any warnings or failures above"
echo "  2. Fix failing tests if needed"
echo "  3. Commit changes and push to trigger GitHub Actions"
echo "  4. Monitor Codacy for successful analysis"
