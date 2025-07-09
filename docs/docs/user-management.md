# User Management

Rubberduck provides a simple yet effective user management system for controlling access to your LLM proxy infrastructure. Learn how to manage users, authentication, and access controls.

## Overview

The user management system in Rubberduck allows you to:

- **Control Access**: Manage who can create and manage proxies
- **Track Usage**: Associate proxy activity with specific users
- **Secure Operations**: Protect proxy infrastructure with authentication
- **Audit Activity**: Monitor user actions and proxy usage

Currently, Rubberduck operates with a simple authentication model suitable for small teams and development environments.

## Default User Account

### Initial Setup

When Rubberduck starts for the first time, a default administrator account is automatically created:

**Default Credentials:**
- **Email**: `admin@example.com`
- **Password**: `admin`

:::warning Security Notice
Change the default password immediately after first login, especially in production environments.
:::

### First Login

1. Navigate to `http://localhost:5173` in your browser
2. Click **"Sign In"** if not automatically redirected
3. Enter the default credentials:
   - Email: `admin@example.com`
   - Password: `admin`
4. You'll be redirected to the main dashboard

## User Authentication

### Login Process

**Web Interface Login:**
1. Access the Rubberduck web interface
2. Enter your email and password
3. Click **"Sign In"** to authenticate
4. Upon successful login, you'll see the dashboard

**Session Management:**
- Sessions persist until logout or expiration
- Automatic session renewal for active users
- Secure session cookies with CSRF protection

### Logout

To logout from your session:
1. Click on your user profile in the top navigation
2. Select **"Sign Out"** from the dropdown menu
3. You'll be redirected to the login page

## Account Management

### Profile Settings

Access your profile settings through the user menu:

**Personal Information:**
- View and update email address
- Change display name
- Update contact preferences

**Account Security:**
- Change password
- View active sessions
- Review login history

### Password Management

**Changing Your Password:**
1. Navigate to **Profile Settings**
2. Click **"Change Password"**
3. Enter your current password
4. Provide a new secure password
5. Confirm the password change
6. Save your changes

**Password Requirements:**
- Minimum 8 characters
- Mix of uppercase and lowercase letters
- Include numbers and special characters
- Avoid common passwords and dictionary words

## User Roles and Permissions

### Current Permission Model

In the current version, all authenticated users have equivalent permissions:

**User Capabilities:**
- ✅ Create new proxy instances
- ✅ Start and stop proxies
- ✅ Configure proxy settings
- ✅ View logs and monitoring data
- ✅ Manage failure simulation settings
- ✅ Access all dashboard features

**System Operations:**
- ✅ View system metrics
- ✅ Access user management (own account)
- ✅ Export logs and data
- ✅ Configure global settings

### Future Role-Based Access

Future versions will include expanded role-based access control:

**Planned Roles:**
- **Administrator**: Full system access and user management
- **Operator**: Proxy management and monitoring
- **Viewer**: Read-only access to dashboards and logs
- **Developer**: Proxy creation and testing capabilities

## Multi-User Considerations

### Proxy Ownership

**Current Model:**
- All users can see and manage all proxies
- No individual proxy ownership
- Shared responsibility for proxy management

**Best Practices:**
- Use descriptive proxy names to indicate purpose/owner
- Coordinate proxy usage among team members
- Establish naming conventions for shared environments

### Resource Sharing

**Shared Resources:**
- All proxy instances are visible to all users
- Cache data is shared across proxies
- Logs and monitoring data are accessible to all users

**Coordination Strategies:**
- Establish proxy naming conventions
- Document proxy purposes and ownership
- Communicate changes to shared proxies
- Use tags or descriptions for organization

## Security Best Practices

### Authentication Security

**Strong Passwords:**
- Use unique passwords for Rubberduck accounts
- Enable password managers for secure storage
- Regular password rotation (every 3-6 months)
- Avoid sharing credentials between team members

**Session Security:**
- Logout when leaving workstations unattended
- Use HTTPS for all web interface access
- Monitor active sessions for unusual activity
- Clear browser data on shared computers

### Access Control

**Network Security:**
- Restrict Rubberduck access to authorized networks
- Use VPN for remote access
- Implement firewall rules for port access
- Monitor connection logs for unusual patterns

**Environment Security:**
- Separate development and production instances
- Use different credentials for different environments
- Regular security updates and patches
- Backup user data and configurations

## User Activity Monitoring

### Login Tracking

**Session Logs:**
- Track user login attempts
- Monitor session durations
- Log logout events
- Record failed authentication attempts

**Security Monitoring:**
- Detect unusual login patterns
- Alert on failed login attempts
- Monitor concurrent sessions
- Track login locations (if available)

### Action Auditing

**Proxy Operations:**
- Record proxy creation and deletion
- Track configuration changes
- Log start/stop operations
- Monitor failure simulation modifications

**System Changes:**
- Track user profile updates
- Log password changes
- Monitor export operations
- Record administrative actions

## User Management Tasks

### Profile Maintenance

**Regular Tasks:**
- Review and update contact information
- Change passwords periodically
- Check active sessions
- Review login history

**Security Reviews:**
- Audit account access patterns
- Verify session security
- Update security settings
- Review shared resource access

### Team Coordination

**Communication:**
- Share proxy naming conventions
- Coordinate testing schedules
- Document proxy purposes
- Communicate maintenance windows

**Resource Management:**
- Monitor shared proxy usage
- Coordinate cache management
- Share monitoring insights
- Collaborate on troubleshooting

## Backup and Recovery

### User Data Backup

**Account Information:**
- User profiles and preferences
- Password hashes (encrypted)
- Session data and history
- Activity logs and audit trails

**Recovery Procedures:**
- Password reset functionality
- Account recovery options
- Data restoration from backups
- Emergency access procedures

### Data Protection

**Privacy Measures:**
- Secure password storage (hashed/salted)
- Encrypted session cookies
- Protected personal information
- GDPR compliance considerations

**Backup Strategy:**
- Regular automated backups
- Secure backup storage
- Tested recovery procedures
- Disaster recovery planning

## API Access and Authentication

### API Authentication

**Current API Access:**
- Session-based authentication for web interface
- No separate API key system (yet)
- Use web session cookies for API calls

**Future API Features:**
- Dedicated API keys for programmatic access
- Token-based authentication
- Scoped permissions for API access
- Rate limiting per user/API key

### Programmatic Access

**Current Limitations:**
- API access requires web session
- No dedicated service accounts
- Limited automation capabilities

**Workarounds:**
- Use session cookies in scripts
- Implement web scraping for automation
- Manual export for data access

## Troubleshooting

### Login Issues

**Common Problems:**
- Forgotten passwords
- Session expiration
- Browser compatibility
- Network connectivity

**Resolution Steps:**
1. **Clear browser cache and cookies**
2. **Try incognito/private browsing mode**
3. **Check network connectivity**
4. **Verify correct URL and port**
5. **Contact administrator if issues persist**

### Password Reset

**Current Process:**
- Manual password reset by administrator
- Direct database modification if needed
- Temporary password assignment

**Recovery Steps:**
1. Contact system administrator
2. Verify identity and account ownership
3. Administrator resets password
4. Login with temporary credentials
5. Immediately change to new password

### Session Problems

**Session Timeout:**
- Default session duration varies by configuration
- Automatic renewal for active users
- Manual re-login required after timeout

**Multiple Sessions:**
- Multiple browser sessions supported
- Cross-device access allowed
- Session conflicts are rare

## Compliance and Privacy

### Data Privacy

**Personal Information:**
- Minimal personal data collection
- Secure storage of credentials
- No tracking beyond necessary audit logs
- User control over profile data

**GDPR Compliance:**
- Right to data access
- Right to data deletion
- Data portability options
- Privacy by design principles

### Audit Requirements

**Compliance Logging:**
- User authentication events
- Administrative actions
- Data access patterns
- System modifications

**Retention Policies:**
- User activity logs (90 days)
- Authentication logs (30 days)
- Profile changes (permanent)
- Audit trails (1 year)

## Migration and Scaling

### User Data Migration

**Export Capabilities:**
- User profile data
- Activity history
- Authentication logs
- Configuration settings

**Import Procedures:**
- Bulk user creation
- Profile data restoration
- Permission migration
- Historical data import

### Scaling Considerations

**Multi-Instance Deployment:**
- Shared user database
- Centralized authentication
- Distributed proxy management
- Consistent user experience

**Performance Optimization:**
- Session caching
- Authentication optimization
- Database indexing
- Load balancing support

## Future Enhancements

### Planned Features

**Advanced Authentication:**
- Single Sign-On (SSO) integration
- Multi-factor authentication (MFA)
- OAuth/SAML support
- LDAP/Active Directory integration

**Enhanced User Management:**
- Role-based access control (RBAC)
- User groups and teams
- Granular permissions
- Resource-level access control

**Self-Service Features:**
- Password reset workflows
- Profile self-management
- API key generation
- Usage reporting

### Integration Roadmap

**Enterprise Features:**
- Enterprise SSO providers
- Audit and compliance tools
- Advanced security features
- User provisioning automation

## Next Steps

After setting up user management:

1. **Configure security settings** - Enhance authentication security
2. **[Set up monitoring](/logging)** - Track user activity and system usage
3. **Plan for scale** - Prepare for multi-user environments
4. **Implement backup procedures** - Protect user data and configurations

---

Proper user management ensures secure and organized access to your Rubberduck infrastructure. Follow these guidelines to maintain a secure and well-managed system.