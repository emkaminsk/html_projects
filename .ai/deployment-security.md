# Deployment Security Guide

## Problem
By default, nginx (and most web servers) will serve ALL files in the document root, including hidden files and directories starting with `.`. This means:
- `.ai/tech-stack.md` - Internal documentation
- `.cursor/` - Development configuration
- `.github/` - CI/CD workflows
- `.git/` - Version control (if present)

These can be accessed via URLs like:
- `https://yourdomain.com/.ai/tech-stack.md`
- `https://yourdomain.com/.cursor/rules/`

## Solution: Nginx Configuration

### Option 1: Block All Hidden Files/Directories (Recommended)

Add this to your nginx server block:

```nginx
# Block all hidden files and directories
location ~ /\. {
    deny all;
    access_log off;
    log_not_found off;
}
```

### Option 2: Specific Directory Blocking

If you want more granular control:

```nginx
# Block specific directories
location ~ ^/(\.ai|\.cursor|\.github|\.git) {
    deny all;
    access_log off;
    log_not_found off;
}
```

### Complete Nginx Configuration

See `nginx.conf.example` in the project root for a complete configuration.

## Implementation Steps

1. **SSH into your VPS**
2. **Locate your nginx config** (usually `/etc/nginx/sites-available/your-site` or `/etc/nginx/nginx.conf`)
3. **Add the blocking rules** to your server block
4. **Test configuration**: `sudo nginx -t`
5. **Reload nginx**: `sudo systemctl reload nginx`

## Verification

After implementing, test that directories are blocked:

```bash
# Should return 403 Forbidden
curl -I https://yourdomain.com/.ai/tech-stack.md
curl -I https://yourdomain.com/.cursor/

# Should still work normally
curl -I https://yourdomain.com/index.html
```

## Alternative: Exclude from Git (Not Recommended)

If you don't want to version control these folders, add to `.gitignore`:

```
.ai/
.cursor/
```

However, this means:
- ❌ You lose version control for these files
- ❌ Team members won't have access to development rules
- ❌ CI/CD workflows won't be tracked

**Better approach**: Keep them in git, block them in nginx.

## Additional Security Recommendations

1. **Block `.git` directory** (if accidentally deployed)
2. **Block `.env` files** (if you add any)
3. **Add security headers** (see nginx.conf.example)
4. **Use HTTPS** (Let's Encrypt)
5. **Regular security audits** of your nginx config

