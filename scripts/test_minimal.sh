#!/bin/bash
set -e

echo "🔧 Quick CI Pipeline Test"
echo "========================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}📦 Installing dependencies...${NC}"
uv pip install -e ".[dev,test]"

echo -e "${BLUE}🔍 Testing tools availability...${NC}"
echo "• black: $(uv run black --version | head -1)"
echo "• ruff: $(uv run ruff --version)"
echo "• mypy: $(uv run mypy --version)"
echo "• pytest: $(uv run pytest --version)"
echo "• bandit: $(uv run bandit --version | head -1)"

echo -e "${BLUE}🧪 Running single test with coverage...${NC}"
uv run pytest tests/unit/cli/test_analyze_commands.py::TestAnalyzeCommands::test_project_command_success \
  --cov=claude_builder \
  --cov-report=xml:coverage.xml \
  --cov-report=term \
  -v

if [[ -f "coverage.xml" ]]; then
    echo -e "${GREEN}✅ Coverage generated${NC}"
    echo -e "${BLUE}🔧 Testing path fixing...${NC}"
    uv run python scripts/fix_coverage_paths.py coverage.xml
    echo -e "${GREEN}✅ Path fixing works${NC}"
else
    echo -e "${YELLOW}⚠️  No coverage file generated${NC}"
fi

echo -e "${GREEN}🎉 Minimal test complete!${NC}"