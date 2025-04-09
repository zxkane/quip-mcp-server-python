# GitHub Tools Usage Guide

## 1. Project Information

- **Project GitHub Repository**: https://github.com/zxkane/quip-mcp-server
- **Project Description**: This is a Model Context Protocol (MCP) server for interacting with Quip spreadsheets. The server provides tools to read spreadsheet data from Quip documents and return the content in CSV format.

## 2. GitHub MCP Tools Usage

The GitHub MCP server provides a rich set of tools that help us efficiently manage code, create and review PRs, track issues, and more. Below are the main tools with their usage methods and examples.

### 2.1 Repository Operations

#### search_repositories

Search for GitHub repositories.

**Parameters**:
- `query`: Search query string
- `sort` (optional): Sort method, possible values are `stars`, `forks`, `updated`
- `order` (optional): Sort order, possible values are `asc`, `desc`
- `per_page` (optional): Number of results per page, default is 30
- `page` (optional): Page number, default is 1

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>search_repositories</tool_name>
<arguments>
{
  "query": "quip-mcp-server",
  "sort": "updated",
  "order": "desc"
}
</arguments>
</use_mcp_tool>
```

#### get_file_contents

Get the contents of a file in a GitHub repository.

**Parameters**:
- `owner`: Repository owner
- `repo`: Repository name
- `path`: File path
- `ref` (optional): Branch, tag, or commit SHA

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>get_file_contents</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "path": "README.md"
}
</arguments>
</use_mcp_tool>
```

#### search_code

Search for code in GitHub repositories.

**Parameters**:
- `query`: Search query string
- `per_page` (optional): Number of results per page, default is 30
- `page` (optional): Page number, default is 1

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>search_code</tool_name>
<arguments>
{
  "query": "repo:zxkane/quip-mcp-server language:python"
}
</arguments>
</use_mcp_tool>
```

### 2.2 PR Creation and Management

#### create_pull_request

Create a new Pull Request.

**Parameters**:
- `owner`: Repository owner
- `repo`: Repository name
- `title`: PR title
- `body`: PR description
- `head`: Branch containing the changes
- `base`: Target branch to merge into

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>create_pull_request</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "title": "Add new feature: multi-sheet export",
  "body": "This PR adds functionality to export multiple sheets simultaneously, improving data processing efficiency.",
  "head": "feature/multi-sheet-export",
  "base": "main"
}
</arguments>
</use_mcp_tool>
```

#### update_pull_request_branch

Update a PR branch, typically used to resolve merge conflicts.

**Parameters**:
- `owner`: Repository owner
- `repo`: Repository name
- `pull_number`: PR number

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>update_pull_request_branch</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "pull_number": 42
}
</arguments>
</use_mcp_tool>
```

#### get_pull_request

Get detailed information about a PR.

**Parameters**:
- `owner`: Repository owner
- `repo`: Repository name
- `pull_number`: PR number

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>get_pull_request</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "pull_number": 42
}
</arguments>
</use_mcp_tool>
```

#### get_pull_request_status

Get the status of a PR, including CI check status.

**Parameters**:
- `owner`: Repository owner
- `repo`: Repository name
- `pull_number`: PR number

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>get_pull_request_status</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "pull_number": 42
}
</arguments>
</use_mcp_tool>
```

#### get_pull_request_files

Get a list of files modified in a PR.

**Parameters**:
- `owner`: Repository owner
- `repo`: Repository name
- `pull_number`: PR number

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>get_pull_request_files</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "pull_number": 42
}
</arguments>
</use_mcp_tool>
```

### 2.3 PR Review and Merge

#### create_pull_request_review

Create a PR review.

**Parameters**:
- `owner`: Repository owner
- `repo`: Repository name
- `pull_number`: PR number
- `event`: Review event, possible values are `APPROVE`, `REQUEST_CHANGES`, `COMMENT`
- `body`: Review comment

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>create_pull_request_review</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "pull_number": 42,
  "event": "APPROVE",
  "body": "Code looks good, tests pass, ready to merge."
}
</arguments>
</use_mcp_tool>
```

#### get_pull_request_reviews

Get all reviews for a PR.

**Parameters**:
- `owner`: Repository owner
- `repo`: Repository name
- `pull_number`: PR number

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>get_pull_request_reviews</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "pull_number": 42
}
</arguments>
</use_mcp_tool>
```

#### get_pull_request_comments

Get all comments on a PR.

**Parameters**:
- `owner`: Repository owner
- `repo`: Repository name
- `pull_number`: PR number

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>get_pull_request_comments</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "pull_number": 42
}
</arguments>
</use_mcp_tool>
```

#### merge_pull_request

Merge a PR.

**Parameters**:
- `owner`: Repository owner
- `repo`: Repository name
- `pull_number`: PR number
- `merge_method` (optional): Merge method, possible values are `merge`, `squash`, `rebase`, default is `merge`

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>merge_pull_request</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "pull_number": 42,
  "merge_method": "squash"
}
</arguments>
</use_mcp_tool>
```

### 2.4 Issue Tracking

#### create_issue

Create a new Issue.

**Parameters**:
- `owner`: Repository owner
- `repo`: Repository name
- `title`: Issue title
- `body`: Issue description
- `labels` (optional): Array of labels

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>create_issue</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "title": "Add support for multi-sheet export",
  "body": "Currently only single sheet export is supported. We need to add functionality to export multiple sheets simultaneously.",
  "labels": ["enhancement", "good first issue"]
}
</arguments>
</use_mcp_tool>
```

#### update_issue

Update an existing Issue.

**Parameters**:
- `owner`: Repository owner
- `repo`: Repository name
- `issue_number`: Issue number
- `title` (optional): New title
- `body` (optional): New description
- `state` (optional): Status, possible values are `open`, `closed`
- `labels` (optional): Array of labels

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>update_issue</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "issue_number": 123,
  "state": "closed"
}
</arguments>
</use_mcp_tool>
```

#### add_issue_comment

Add a comment to an Issue.

**Parameters**:
- `owner`: Repository owner
- `repo`: Repository name
- `issue_number`: Issue number
- `body`: Comment content

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>add_issue_comment</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "issue_number": 123,
  "body": "I'm working on this issue and expect to complete it next week."
}
</arguments>
</use_mcp_tool>
```

#### get_issue

Get detailed information about an Issue.

**Parameters**:
- `owner`: Repository owner
- `repo`: Repository name
- `issue_number`: Issue number

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>get_issue</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "issue_number": 123
}
</arguments>
</use_mcp_tool>
```

#### search_issues

Search for Issues.

**Parameters**:
- `query`: Search query string
- `per_page` (optional): Number of results per page, default is 30
- `page` (optional): Page number, default is 1

**Example**:
```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>search_issues</tool_name>
<arguments>
{
  "query": "repo:zxkane/quip-mcp-server is:issue is:open label:bug"
}
</arguments>
</use_mcp_tool>
```

## 3. CI Checks and Fixes

### 3.1 Methods to Check CI Status

#### Using GitHub MCP Tools

You can use the `get_pull_request_status` tool to check the CI status of a PR:

```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>get_pull_request_status</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "pull_number": 42
}
</arguments>
</use_mcp_tool>
```

The returned result will include the status of all checks, including whether they passed, failed, or are in progress.

#### Viewing through GitHub Interface

You can also check CI status directly on the GitHub interface:
1. Open the PR page
2. Scroll to the "Checks" section at the bottom
3. View the status and detailed logs for each check

### 3.2 Common Failure Causes Analysis

#### Test Failures

- **Unit Test Failures**: Code changes broke existing functionality
- **Integration Test Failures**: Issues with interactions between components
- **End-to-End Test Failures**: Problems in the complete workflow from a user perspective

Review the test logs to identify which specific test case failed and why.

#### Code Style Issues

- **Linting Errors**: Code doesn't comply with the project's style guide
- **Formatting Issues**: Problems with indentation, spacing, line breaks, etc.
- **Type Checking Errors**: If the project uses type checking (like mypy), there might be type-related errors

These issues can usually be fixed by running the appropriate formatting tools or linters.

#### Dependency Issues

- **Missing Dependencies**: Code references dependencies that aren't installed
- **Version Conflicts**: Conflicting version requirements between different dependencies
- **Installation Failures**: Some dependencies fail to install in the CI environment

Check the `pyproject.toml` and `uv.lock` files to ensure dependency configurations are correct.

#### Environment Configuration Issues

- **Missing Environment Variables**: Required environment variables are missing in the CI environment
- **Permission Issues**: Insufficient permissions in the CI environment
- **Resource Limitations**: Insufficient resources (like memory, CPU) in the CI environment

Check the CI configuration file (`.github/workflows/ci.yml`) to ensure the environment is properly configured.

### 3.3 Fix Strategies and Verification

#### Analyze CI Logs

1. Review CI logs to find specific error messages
2. Understand the root cause of the error
3. Determine the fix direction

#### Reproduce Issues Locally

1. Set up the same conditions as the CI environment locally
2. Run the same commands to try to reproduce the error
3. Confirm if the issue can be reproduced locally

#### Fix the Code

1. Modify the code based on error messages and local testing
2. Ensure the fix doesn't introduce new issues
3. Add or update tests to ensure the issue doesn't occur again

#### Submit Fixes and Verify

1. Commit the fixed code
2. Push to the PR branch
3. Wait for CI to run again and verify it passes
4. If it still fails, repeat the above steps

## 4. Real-World Usage Examples

### 4.1 Complete PR Workflow Example

Here's an example of a complete PR workflow using GitHub MCP tools:

#### Step 1: Create a Branch (Using Git Command)

```bash
git checkout -b feature/add-multi-sheet-export
```

#### Step 2: Modify Code (Local Editing)

Modify relevant files to implement new features or fix bugs.

#### Step 3: Create PR

```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>create_pull_request</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "title": "Add multi-sheet export functionality",
  "body": "This PR implements functionality to export multiple sheets simultaneously, improving data processing efficiency.\n\n- Added `export_multiple_sheets` function\n- Updated related tests\n- Updated documentation",
  "head": "feature/add-multi-sheet-export",
  "base": "main"
}
</arguments>
</use_mcp_tool>
```

#### Step 4: Check CI Status

```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>get_pull_request_status</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "pull_number": 42
}
</arguments>
</use_mcp_tool>
```

#### Step 5: Review PR

```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>get_pull_request_reviews</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "pull_number": 42
}
</arguments>
</use_mcp_tool>
```

#### Step 6: Handle Feedback

If you receive review feedback, modify the code and push updates.

```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>get_pull_request_comments</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "pull_number": 42
}
</arguments>
</use_mcp_tool>
```

#### Step 7: Merge PR

```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>merge_pull_request</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "pull_number": 42,
  "merge_method": "squash"
}
</arguments>
</use_mcp_tool>
```

### 4.2 CI Failure Fix Example

Here's an example of handling CI failures:

#### Step 1: Identify CI Failure Reason

```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>get_pull_request_status</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "pull_number": 42
}
</arguments>
</use_mcp_tool>
```

Let's say we discover that tests failed, with the error message indicating that the `test_export_multiple_sheets` test case failed.

#### Step 2: Local Fix

1. Reproduce the issue locally:
```bash
pytest tests/test_server.py::test_export_multiple_sheets -v
```

2. Fix the code to make the test pass.

#### Step 3: Submit Fix

```bash
git add .
git commit -m "Fix test failure in multi-sheet export functionality"
git push origin feature/add-multi-sheet-export
```

#### Step 4: Verify CI Passes

```
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>get_pull_request_status</tool_name>
<arguments>
{
  "owner": "zxkane",
  "repo": "quip-mcp-server",
  "pull_number": 42
}
</arguments>
</use_mcp_tool>
```

After confirming that all CI checks pass, you can request a review and eventually merge the PR.