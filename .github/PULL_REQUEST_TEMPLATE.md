# Pull Request

## 📋 Summary

<!-- Provide a brief description of the changes in this PR -->

## 🔗 Related Issues

<!-- Link to any related issues, e.g., "Fixes #123" or "Addresses #456" -->

- Fixes #
- Related to #

## 🎯 Changes Made

<!-- Describe the specific changes made -->

### 🔧 Code Changes

- [ ] Core functionality changes
- [ ] CLI interface modifications
- [ ] Template additions/modifications
- [ ] Agent configuration updates
- [ ] Bug fixes
- [ ] Performance improvements

### 📚 Documentation Changes

- [ ] README updates
- [ ] Code documentation (docstrings)
- [ ] Examples or guides
- [ ] Configuration documentation

### 🧪 Testing Changes

- [ ] New tests added
- [ ] Existing tests modified
- [ ] Test coverage improved
- [ ] Performance tests added

## 🔍 Type of Change

<!-- Mark the type of change with an "x" -->

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing
  functionality to not work as expected)
- [ ] 📚 Documentation only changes
- [ ] 🧪 Test only changes
- [ ] 🔧 Refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] 🎨 Style/formatting changes

## 🧪 Testing

<!-- Describe how you tested these changes -->

### Testing Checklist

- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed
- [ ] Edge cases considered and tested
- [ ] Cross-platform testing (if applicable)

### Test Commands Run

```bash
# List the test commands you ran
pytest
pytest --cov=claude_builder
black --check claude_builder tests
ruff check claude_builder tests
mypy claude_builder
```

### Test Results

<!-- Describe the results of your testing -->

## 🏗️ Implementation Details

### Architecture Impact
<!-- Describe any architectural changes or impacts -->

### Dependencies
<!-- List any new dependencies or dependency changes -->

### Configuration Changes
<!-- Describe any configuration file changes -->

### Migration Notes
<!-- If applicable, describe any migration steps needed -->

## 📸 Screenshots/Examples

<!-- If applicable, add screenshots or code examples -->

### Before

```python
# Show code before changes
```

### After

```python
# Show code after changes
```

## 🎨 Code Quality

### Code Quality Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Type hints added where appropriate
- [ ] Error handling implemented
- [ ] Logging added where appropriate

### Security Considerations

- [ ] No sensitive information exposed
- [ ] Input validation implemented
- [ ] Security best practices followed
- [ ] No new security vulnerabilities introduced

## 🚀 Deployment Impact

<!-- Describe any deployment considerations -->

### Breaking Changes
<!-- List any breaking changes and migration steps -->

### Configuration Updates
<!-- List any required configuration updates -->

### Rollback Plan
<!-- Describe how to rollback these changes if needed -->

## 📝 Additional Notes

<!-- Any additional information that reviewers should know -->

### Performance Impact
<!-- Describe any performance implications -->

### Future Enhancements
<!-- List any follow-up work or future enhancements planned -->

### Known Limitations
<!-- List any known limitations of this implementation -->

## ✅ Pre-submission Checklist

<!-- Verify all items before submitting -->

### Code Quality

- [ ] Code has been self-reviewed
- [ ] Code follows the project's style guidelines
- [ ] Comments have been added for complex logic
- [ ] No debug code or console.log statements left in

### Testing

- [ ] All tests pass locally
- [ ] New tests have been added for new functionality
- [ ] Test coverage maintained or improved
- [ ] Manual testing completed

### Documentation

- [ ] Documentation has been updated (if applicable)
- [ ] Docstrings added/updated for new functions
- [ ] README updated (if applicable)
- [ ] Examples updated (if applicable)

### Git

- [ ] Meaningful commit messages used
- [ ] Commits are logically organized
- [ ] No merge commits in feature branch
- [ ] Branch is up to date with main

### Dependency Management

- [ ] No unnecessary dependencies added
- [ ] All new dependencies documented
- [ ] License compatibility verified

## 🤝 Review Guidelines

### For Reviewers

- Focus on code quality, security, and maintainability
- Check for proper error handling and edge cases
- Verify test coverage for new functionality
- Ensure documentation is clear and accurate

### Areas of Focus
<!-- Highlight specific areas where you'd like reviewer attention -->

---

## Thank you for contributing to Claude Builder! 🚀
