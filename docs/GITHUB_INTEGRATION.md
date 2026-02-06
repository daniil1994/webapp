# GitHub Integration

## Overview

Repa supports cloning and syncing git repositories from GitHub, GitLab, Bitbucket, and other git hosting platforms.

## Features

✅ **Implemented:**
- Clone repositories via HTTPS URLs
- Clone repositories via SSH URLs (git@github.com:...)
- Automatic branch detection (main/master fallback)
- Repository sync (git pull)
- Repository cleanup on project deletion
- Validation of git URLs

❌ **Not Implemented (Future):**
- GitHub OAuth authentication
- Webhooks for auto-sync
- Pull request analysis
- Commit history analysis
- Issues integration

## Usage

### 1. Create Project from Git URL

**API Request:**
```bash
POST /api/v1/projects
```

```json
{
  "name": "My GitHub Project",
  "repo_url": "https://github.com/username/repository.git",
  "branch": "main",
  "description": "Optional description"
}
```

**What happens:**
1. Validates git URL format
2. Creates project with status "cloning"
3. Clones repository to `/tmp/repa_repos/{project_id}/`
4. Updates project with cloned path and status "created"
5. Returns project details

**Response:**
```json
{
  "id": "uuid",
  "name": "My GitHub Project",
  "repo_path": "/tmp/repa_repos/{uuid}/",
  "repo_url": "https://github.com/username/repository.git",
  "status": "created",
  ...
}
```

### 2. Sync Repository (Pull Updates)

**API Request:**
```bash
POST /api/v1/projects/{project_id}/sync
```

**What happens:**
1. Runs `git pull` in project directory
2. Returns current branch and commit hash
3. Suggests re-indexing to update embeddings

**Response:**
```json
{
  "success": true,
  "message": "Repository synced successfully",
  "branch": "main",
  "commit": "abc123...",
  "note": "Please re-index the project to update code embeddings"
}
```

### 3. After Sync - Re-index

```bash
POST /api/v1/projects/{project_id}/index
```

This will update code embeddings with the latest code changes.

## Supported URL Formats

### HTTPS URLs
```
https://github.com/user/repo.git
https://github.com/user/repo
https://gitlab.com/user/repo.git
https://bitbucket.org/user/repo.git
```

### SSH URLs
```
git@github.com:user/repo.git
git@gitlab.com:user/repo.git
```

## Branch Handling

By default, clones the `main` branch. If `main` doesn't exist, tries:
1. `main`
2. `master`
3. Specified branch from request

You can specify a custom branch:
```json
{
  "repo_url": "https://github.com/user/repo.git",
  "branch": "develop"
}
```

## Storage

Cloned repositories are stored in:
```
/tmp/repa_repos/{project_id}/
```

**Note:** `/tmp` directory may be cleaned on system restart. For production, consider:
- Using persistent storage (e.g., `/var/lib/repa/repos/`)
- Backup strategy for cloned repositories
- Monitoring disk space usage

## Error Handling

### Invalid URL
```json
{
  "detail": "Invalid git URL: URL must start with https://, http://, or git@"
}
```

### Clone Failure
```json
{
  "detail": "Failed to clone repository: Authentication failed"
}
```

### Not a Git Repository
```json
{
  "detail": "Project is not a git repository (no repo_url)"
}
```

## Frontend Integration

### Create Project Form

Add git URL field to project creation form:

```tsx
<Input
  label="Git Repository URL (optional)"
  placeholder="https://github.com/username/repo.git"
  value={repoUrl}
  onChange={(e) => setRepoUrl(e.target.value)}
/>

<Select
  label="Branch"
  value={branch}
  onChange={(e) => setBranch(e.target.value)}
>
  <option value="main">main</option>
  <option value="master">master</option>
  <option value="develop">develop</option>
</Select>
```

### Sync Button

Add sync button to project details:

```tsx
<Button
  onClick={async () => {
    await projectsAPI.sync(projectId);
    // Show success message
    // Suggest re-indexing
  }}
  disabled={!project.repo_url}
>
  <RefreshCw className="w-4 h-4" />
  Sync Repository
</Button>
```

## Private Repositories

### HTTPS with Token (Recommended)
```bash
https://TOKEN@github.com/user/private-repo.git
```

### SSH with Keys
1. Generate SSH key: `ssh-keygen -t ed25519`
2. Add public key to GitHub: Settings → SSH Keys
3. Use SSH URL: `git@github.com:user/private-repo.git`

**Note:** For production, store tokens securely:
- Environment variables
- Secrets manager (AWS Secrets, HashiCorp Vault)
- Never commit tokens to git

## Performance

### Clone Speed
- Shallow clone (depth=1): ~5-30 seconds for typical repo
- Full clone: Can take minutes for large repos

### Timeout
- Clone timeout: 5 minutes
- Pull timeout: 2 minutes

### Disk Space
- Average repo: 10-100 MB
- Large repos: 500 MB - 2 GB
- Monitor with: `du -sh /tmp/repa_repos/`

## Security

### URL Validation
- Checks for valid protocol (https, http, git@)
- Validates URL format
- Allows common git platforms by default

### Subprocess Safety
- Uses `subprocess.run` with timeout
- Captures output to prevent command injection
- No shell execution (`shell=False`)

### Access Control
- Only org members can create projects
- Only project owner can sync
- JWT authentication required

## Monitoring

### Check Repository Status

```python
from src.services.git_service import GitService

git_service = GitService()
branch = git_service.get_current_branch(repo_path)
commit = git_service.get_latest_commit(repo_path)
```

### Cleanup Old Repositories

```python
# Remove repository when project is deleted
git_service.cleanup_repository(project_id)
```

## Troubleshooting

### Clone Fails with "Authentication failed"

**Solution:** Use personal access token:
```
https://TOKEN@github.com/user/repo.git
```

### "Repository path does not exist"

**Solution:** Re-clone the repository:
```bash
POST /api/v1/projects/{id}
# Then re-index
POST /api/v1/projects/{id}/index
```

### Disk Space Issues

**Solution:** Clean up old repositories:
```bash
rm -rf /tmp/repa_repos/*
```

## API Reference

### POST /api/v1/projects
Create project (with optional git clone)

**Body:**
```typescript
{
  name: string;
  repo_url?: string;
  branch?: string;  // default: "main"
  description?: string;
}
```

### POST /api/v1/projects/{id}/sync
Sync repository with remote

**Response:**
```typescript
{
  success: boolean;
  message: string;
  branch?: string;
  commit?: string;
}
```

## Configuration

### Change Storage Directory

Edit `backend/src/services/git_service.py`:

```python
class GitService:
    REPOS_DIR = Path("/var/lib/repa/repos")  # Change this
```

### Change Timeouts

```python
# Clone timeout (default: 300s)
timeout=300

# Pull timeout (default: 120s)
timeout=120
```

## Future Enhancements

1. **GitHub OAuth**
   - Login with GitHub
   - Access private repos automatically
   - No need for tokens

2. **Webhooks**
   - Auto-sync on push
   - Auto-index after sync
   - Real-time updates

3. **Pull Request Analysis**
   - Analyze PR diffs
   - Suggest improvements
   - Auto-comment on PRs

4. **Commit History**
   - Track changes over time
   - Blame information
   - Code evolution analytics

## Related Documentation

- [Week 2-3 Roadmap](phase1-roadmap-detailed.md#week-2-3)
- [Projects API](../backend/src/api/v1/projects.py)
- [Git Service](../backend/src/services/git_service.py)
