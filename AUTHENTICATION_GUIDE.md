# 🔐 Authentication System Guide

## Overview
The RFID Reception System now includes a secure authentication page that appears before the main application window. This ensures only authorized users can access the system.

## Features

### 🎯 Login Window
- **Modern UI Design**: Clean and professional login interface
- **Password Protection**: Secure SHA-256 password hashing
- **Show/Hide Password**: Toggle password visibility
- **Enter Key Support**: Press Enter to login
- **Exit Confirmation**: Prevents accidental closure

### 🔒 Security
- Passwords are stored as SHA-256 hashes in the configuration file
- No plain text password storage
- Failed login attempts are logged
- Application closes if login window is closed without authentication

## Default Credentials

**Default Password**: `admin123`

💡 **Important**: Change the default password after first use!

## How to Use

### Starting the Application
1. Run `run_app.py` or your application launcher
2. The login window will appear first
3. Enter your password
4. Click "✓ تسجيل الدخول" (Login) or press Enter
5. Upon successful authentication, the main application window opens

### Changing the Password

To change your password, you need to update the `password_hash` in the config file:

#### Method 1: Using Python
1. Open Python terminal
2. Run the following code:
```python
import hashlib
new_password = "your_new_password"
password_hash = hashlib.sha256(new_password.encode()).hexdigest()
print(password_hash)
```
3. Copy the output hash
4. Open `config/config.json`
5. Replace the `password_hash` value with your new hash
6. Save the file

#### Method 2: Using Online SHA-256 Generator
1. Visit a trusted SHA-256 generator (e.g., https://emn178.github.io/online-tools/sha256.html)
2. Enter your new password
3. Copy the generated hash
4. Open `config/config.json`
5. Replace the `password_hash` value with your new hash
6. Save the file

### Configuration File Location
```
rfid-reception-system/
└── config/
    └── config.json
```

### Example config.json
```json
{
    "serial_port": "COM3",
    "baud_rate": 115200,
    "employee_name": "Receptionist",
    "backup_dir": "backups",
    "backup_time": "23:59",
    "report_time": "23:55",
    "db_path": "rfid_reception.db",
    "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",
    "weekly_day_of_week": "mon",
    "weekly_time": "00:10",
    "monthly_day": 1,
    "monthly_time": "00:15"
}
```

## Common Password Hashes (for reference)

| Password | SHA-256 Hash |
|----------|--------------|
| admin123 | 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9 |
| password | 5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8 |
| 123456 | 8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92 |

⚠️ **Security Warning**: Use strong, unique passwords. Avoid common passwords like the examples above.

## Troubleshooting

### Problem: Forgot Password
**Solution**: 
1. Open `config/config.json`
2. Replace the `password_hash` with the default hash for "admin123":
   ```
   "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
   ```
3. Save and restart the application
4. Login with "admin123"
5. Change the password immediately

### Problem: Login Window Doesn't Appear
**Solution**:
1. Check the logs in `logs/rfid_reception.log`
2. Ensure the `login_window.py` file exists in `rfid_reception/gui/`
3. Verify all required imports are available

### Problem: Application Closes After Login
**Solution**:
1. Check the logs for error messages
2. Ensure all services (database, serial, reports) are properly initialized
3. Verify configuration file is valid JSON

## File Structure

```
rfid-reception-system/
├── rfid_reception/
│   ├── gui/
│   │   ├── login_window.py    # ← New authentication window
│   │   └── main_window.py     # Main application window
│   └── app.py                 # Modified to show login first
├── config/
│   └── config.json            # Contains password hash
└── run_app.py                 # Application launcher
```

## Security Best Practices

1. ✅ **Change Default Password**: Always change from "admin123" after first use
2. ✅ **Use Strong Passwords**: Minimum 8 characters, mix of letters, numbers, and symbols
3. ✅ **Regular Updates**: Change password periodically
4. ✅ **Secure Storage**: Keep `config.json` file permissions restricted
5. ✅ **Don't Share**: Never share your password or password hash
6. ✅ **Monitor Logs**: Check logs regularly for unauthorized access attempts

## Technical Details

### Password Hashing
- **Algorithm**: SHA-256 (256-bit hash function)
- **Security**: One-way hash function (cannot be reversed)
- **Implementation**: Python's `hashlib` library

### Login Flow
1. User enters password
2. Password is hashed using SHA-256
3. Hash is compared with stored hash in config
4. If match: Main application opens
5. If no match: Error message shown, password field cleared

### Logging
All authentication events are logged:
- Successful logins
- Failed login attempts
- Application closure from login window

Check logs at: `logs/rfid_reception.log`

---

## Support

If you encounter any issues with the authentication system:
1. Check this guide first
2. Review the logs in `logs/rfid_reception.log`
3. Verify your configuration file is valid
4. Contact system administrator if problems persist

---

**Version**: 1.0
**Last Updated**: November 2025
