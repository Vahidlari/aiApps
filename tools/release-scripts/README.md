# Release Helper Scripts

This directory contains helper scripts used by the GitHub Actions release workflow to manage version metadata and documentation for the database server releases.

## Scripts

### `create-version-metadata.sh`

Creates version metadata files for database server releases.

**Usage:**
```bash
create-version-metadata.sh <version> <git_commit> <git_branch> <repository>
```

**Example:**
```bash
bash create-version-metadata.sh 1.0.0 abc123def main Vahidlari/aiApps
```

**Creates:**
- `tools/database_server/config/VERSION` - Simple version file
- `tools/database_server/config/release-info.json` - Complete release metadata

**Output Files:**

`VERSION`:
```
1.0.0
```

`release-info.json`:
```json
{
  "version": "1.0.0",
  "release_date": "2024-01-15T10:30:00Z",
  "git_tag": "v1.0.0",
  "git_commit": "abc123def",
  "git_branch": "main",
  "release_url": "https://github.com/Vahidlari/aiApps/releases/tag/v1.0.0",
  "repository": "Vahidlari/aiApps"
}
```

---

### `update-readme-version.sh`

Updates the database server README with version information.

**Usage:**
```bash
update-readme-version.sh <version> <repository>
```

**Example:**
```bash
bash update-readme-version.sh 1.0.0 Vahidlari/aiApps
```

**Actions:**
1. Updates the README header to include version: `# Ragora Database Server - v1.0.0`
2. Adds a "Release Information" section at the end with:
   - Link to VERSION file
   - Link to release-info.json
   - Link to documentation

**Before:**
```markdown
# Database Server Manager
...
```

**After:**
```markdown
# Ragora Database Server - v1.0.0

# Database Server Manager
...

## Release Information

**Version:** See config/VERSION or run ./database-manager.sh --version
**Release Date:** See config/release-info.json for full metadata
**Documentation:** [Ragora Documentation](https://github.com/Vahidlari/aiApps)
```

---

## Testing Locally

You can test these scripts locally before a release:

```bash
# From the repository root
cd /workspaces/aiApps

# Test metadata creation
bash tools/release-scripts/create-version-metadata.sh \
  "1.0.0-test" \
  "abc123" \
  "test-branch" \
  "Vahidlari/aiApps"

# Test README update
bash tools/release-scripts/update-readme-version.sh \
  "1.0.0-test" \
  "Vahidlari/aiApps"

# Check the results
cat tools/database_server/config/VERSION
cat tools/database_server/config/release-info.json
head -5 tools/database_server/README.md
tail -10 tools/database_server/README.md

# Clean up test files
rm tools/database_server/config/VERSION
rm tools/database_server/config/release-info.json
git restore tools/database_server/README.md
```

---

## Integration with GitHub Actions

These scripts are called by the `.github/workflows/milestone-release.yml` workflow during the database server archive creation step:

```yaml
- name: Create database server archive
  run: |
    VERSION="${{ steps.semantic_release.outputs.new_release_version }}"
    
    # Create version metadata
    bash tools/release-scripts/create-version-metadata.sh \
      "$VERSION" \
      "${{ github.sha }}" \
      "${{ github.ref_name }}" \
      "${{ github.repository }}"
    
    # Update README
    bash tools/release-scripts/update-readme-version.sh \
      "$VERSION" \
      "${{ github.repository }}"
```

---

## Benefits of This Approach

1. **Maintainability**: Scripts are easier to test and debug than inline YAML code
2. **Reusability**: Scripts can be used locally or in other workflows
3. **Readability**: Workflow file is cleaner and more understandable
4. **Testability**: Scripts can be tested independently before deployment
5. **Version Control**: Changes to scripts are easier to review and track

---

## Troubleshooting

### Script not executable

If you get a "Permission denied" error:
```bash
chmod +x tools/release-scripts/*.sh
```

### Script can't find database_server directory

Ensure you're running from the repository root:
```bash
cd /path/to/aiApps
bash tools/release-scripts/create-version-metadata.sh ...
```

### JSON syntax errors

The scripts use here-documents with proper EOF delimiters. If you modify them, ensure:
- The opening `<<EOF` has no spaces before EOF
- The closing `EOF` is on its own line with no spaces or tabs
- No extra indentation before the closing EOF

