# MetaBank API - Admin features
  
<i>This documentation will be updated after each update of the platform.</i>  

## Table of contents
[Admin Login](#login-2fa)  
[Admin Logout](#logout)  
[Create Admin Account](#create-admin-account)  
[Update Admin Account](#update-admin-account)  
[Ask Reset Password Token](#create-reset-password-token)  
[Reset Password](#reset-password)  

## Endpoints description
### Login 2FA
_Authorized user: Admin_  
Login to the platform  

URI
```
POST /api/v1/admin/login
```
JSON
```
{
    "login": "john@doe.com",
    "password": "password",
    "2fa_token": "098765"       # optional, only to send the 2FA token (2nd call)
}
```
RESPONSE
```
{
    "account": {
        "admin_uuid": "87780317-546e-4051-a8f1-da4fbbb06ac8",
        "created_date": "2023-12-27T14:00:04.512864Z",
        "email_address": "john@doe.com",
        "firstname": "John",
        "lastname": "D.",
        "updated_date": "2023-12-27T18:00:40.916883Z"
    },
    "jwt_token": "eyJhbG...",
    "message": "Login successful",
    "refresh_token": "eyJhbGci...",
    "status": true
}
```

### Login refresh
_Authorized user: Admin_  
Refresh login with JWT refresh token  

URI
```
GET /api/v1/admin/login/refresh
```
RESPONSE
```
{
    "jwt_token": "eyJhb...",
    "message": "Refresh successful",
    "status": true
}
```

### Logout
_Authorized user: Admin_  
Logout from the platform  

URI
```
GET /api/v1/admin/logout
```
HEADER
```
X-AUTH-USER: "Refresh_token"
```
RESPONSE
```
{
    "message": "Logout successful",
    "status": true
}
```

### Create admin account
_Authorized user: Admin_  
Create a new admin account on the platform  

URI
```
POST /api/v1/admin/create
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
JSON
```
{
    "email_address": "john@doe.com",
    "firstname": "John",
    "lastname": "Doe"
}
```
RESPONSE
```
{
    "message": "Admin account successfully created",
    "status": true,
    "user_uuid": "87780317-546e-4051-a8f1-da4fbbb06ac8"
}
```

### Update admin account
_Authorized user: Admin_  
Update personal information of own admin account.  
Only fields to be updated must be given.  
To update password, it is mandatory to give 'old_password' and 'new_password'.  

URI
```
POST /api/v1/admin/account
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
JSON
```
{
    "email_address": "john@doe.com",
    "firstname": "John",
    "lastname": "Doe",
    "old_password": "old",
    "new_password": "new"
}
```
RESPONSE
```
{
    "message": "Admin account successfully updated",
    "status": true
}
```

### Create reset password token
_Authorized user: All_  
Create an otp token to reset the password and send it by email.  

URI
```
POST /api/v1/admin/password/reset/token
```
JSON
```
{
    "email_address": "john@doe.com"
}
```
RESPONSE
```
{
    "message": "Email sent",
    "status": true
}
```

### Reset password
_Authorized user: All_  
Reset the password with otp token sent by email.  

URI
```
POST /api/v1/admin/password/reset
```
JSON
```
{
    "email_address": "john@doe.com",
    "password": "password",
    "reset_token": "a8a526bc"
}
```
RESPONSE
```
{
    "message": "Password updated",
    "status": true
}
```
