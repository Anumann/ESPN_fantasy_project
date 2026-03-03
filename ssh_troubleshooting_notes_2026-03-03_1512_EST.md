# SSH Troubleshooting Notes - 2026-03-03 15:12 EST

## Issue

The `git push` command was repeatedly failing with a `Permission denied (publickey)` error, even though SSH access had been previously configured. My initial diagnostic checks also failed, leading me to incorrectly believe no key was present.

## Root Cause

The repository was configured to use a specific, non-default SSH key located at `~/.ssh/espn_fantasy_deploy_key`. My automated checks and initial attempts only looked for the default key (`~/.ssh/id_rsa`). My failure to locate the correct, existing key led me to mistakenly generate a new, unnecessary one, causing significant confusion.

## Resolution

The issue was resolved by specifying the correct SSH key for the `git` command to use. The `GIT_SSH_COMMAND` environment variable was used to override the default behavior and point to the correct key file.

### Successful Command

The following command successfully pushed the local commits to the remote repository:

```bash
GIT_SSH_COMMAND="ssh -i ~/.ssh/espn_fantasy_deploy_key" git push
```

This command should be used for future `git` operations from this environment if the default key is not working.
