# MetaBank API - Admin related features
  
<i>This documentation will be updated after each update of the platform.</i>  

## Table of contents
[Admin Login](#login-2fa)  
[Refresh Login](#login-refresh)  
[Admin Logout](#logout)  
[Create Admin Account](#create-admin-account)  
[Update Admin Account](#update-admin-account)  
[Ask Reset Password Token](#create-reset-password-token)  
[Reset Password](#reset-password)  
[Get Admin Accounts](#get-admin-accounts)  
[Deactivate Admin Account](#deactivate-admin-account)  
[Reactivate Admin Account](#reactivate-admin-account)  

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
    "message": "success_login",
    "refresh_token": "eyJhbGci...",
    "status": true
}
```

### Login refresh
_Authorized user: All_  
Refresh login with JWT refresh token  

URI
```
GET /api/v1/login/refresh
```
HEADER
```
X-AUTH-USER: "Refresh_token"
```
RESPONSE
```
{
    "jwt_token": "eyJhb...",
    "message": "success_refresh",
    "status": true
}
```

### Logout
_Authorized user: All_  
Logout from the platform  

URI
```
GET /api/v1/logout
```
HEADER
```
X-AUTH-USER: "Refresh_token"
```
RESPONSE
```
{
    "message": "success_logout",
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
    "message": "success_admin_creation",
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
    "message": "success_account_updated",
    "status": true
}
```

### Create reset password token
_Authorized user: Admin_  
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
_Authorized user: Admin_  
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

### Get admin accounts
_Authorized user: Admin_  
Get all admin accounts.  

URI  
_deactivated_ arg is optional. By default, the endpoint returns activated accounts. Set 'deactivated=true' to get deactivated accounts.  
```
GET /api/v1/admin?deactivated=false
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
RESPONSE
```
{
    "admin_accounts": [
        {
            "admin_uuid": "0d7290a2-3166-478b-beb3-752847b1bc87",
            "created_date": "2024-01-03T08:53:19.178280Z",
            "deactivated": false,
            "deactivated_date": null,
            "email_address": "alice@mail.com",
            "email_validated": false,
            "firstname": "Alice",
            "last_login_date": null,
            "lastname": "M.",
            "updated_date": null
        },
        {
            "admin_uuid": "87780317-546e-4051-a8f1-da4fbbb06ac8",
            "created_date": "2023-12-27T14:00:04.512864Z",
            "deactivated": false,
            "deactivated_date": null,
            "email_address": "john@doe.com",
            "email_validated": false,
            "firstname": "John",
            "last_login_date": "2024-01-03T09:01:26.921499Z",
            "lastname": "Doe",
            "updated_date": "2023-12-29T15:18:37.839803Z"
        }
    ],
    "message": "successful_admin_accounts",
    "status": true
}
```


### Deactivate admin account
_Authorized user: Admin_  
Deactivate an admin account.  

URI
```
POST /api/v1/admin/deactivate
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
JSON
```
{
    "admin_uuid": ""
}
```
RESPONSE
```
{
    "message": "success_admin_deactivated",
    "status": true
}
```

### Reactivate admin account
_Authorized user: Admin_  
Reactivate an admin account.  

URI
```
POST /api/v1/admin/reactivate
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
JSON
```
{
    "admin_uuid": ""
}
```
RESPONSE
```
{
    "message": "success_admin_reactivated",
    "status": true
}
```

### Get user accounts
_Authorized user: Admin_  
Get all user accounts.  

URI
```
GET /api/v1/admin/users
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
RESPONSE
```
{
    "message": "successful_user_accounts",
    "status": true,
    "user_accounts": [
        {
            "birthdate": "1234-12-25",
            "created_date": "2024-01-10T13:24:26.346968Z",
            "deactivated": false,
            "deactivated_date": null,
            "email_address": "john@doe.com",
            "email_validated": false,
            "firstname": "John",
            "last_login_date": "2024-01-10T14:19:52.570413Z",
            "lastname": "Doe",
            "public_address": "Ox...,
            "updated_date": "2024-01-10T14:49:08.082977Z",
            "user_uuid": "ddeba27c-3d95-450d-b971-33db6e9fbbec"
        }
    ]
}
```
