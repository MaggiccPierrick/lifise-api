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
