# Metabank API - Admin features
  
<i>This documentation will be updated after each update of the platform.</i>  

## Table of contents
[Create Admin Account](#create-admin-account)  

## Endpoints description
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
