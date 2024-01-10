# MetaBank API - User related features
  
<i>This documentation will be updated after each update of the platform.</i>  

## Table of contents
[Register User](#register)  
[Validate Account](#validate-account)  
[Login](#login)  
[Login](#login-refresh)  
[Login](#logout)  

## Endpoints description
### Register
_Authorized user: User_  
Create user account on the platform.  

URI
```
POST /api/v1/user/register
```
JSON
```
{
    "firstname": "John",
    "lastname": "Doe",
    "email_address": "john@doe.com"
}
```
RESPONSE
```
{
    "message": "success_user_register",
    "status": true
}
```

### Validate account
_Authorized user: User_  
Validate the user account.  

URI
```
POST /api/v1/user/validate
```
JSON
```
{
    "user_uuid": "f601edad-0c82-4e6c-8775-659c07fc9c2e",
    "token": "180745"
}
```
RESPONSE
```
{
    "message": "success_validated",
    "status": true
}
```

### Login
_Authorized user: User_  
Login the user with Magic Link DID token & creates the user if he does not exists in db.  

URI
```
POST /api/v1/user/login
```
JSON
```
{
    "did_token": "xxx",
    "user_uuid"             # optional, used for pre-registered users
}
```
RESPONSE
```
{
    "account": {
        "created_date": "2023-12-27T14:00:04.512864Z",
        "email_address": "john@doe.com",
        "firstname": "John",
        "lastname": "D.",
        "updated_date": "2023-12-27T18:00:40.916883Z",
        "user_uuid": "87780317-546e-4051-a8f1-da4fbbb06ac8"
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

### Update account
_Authorized user: User_  
Update personal information of user account.  
Only fields to be updated must be given.  

URI
```
POST /api/v1/user/account
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
JSON
```
{
    "firstname": "John",
    "lastname": "Doe",
    "birthdate": "1900-01-01"
}
```
RESPONSE
```
{
    "message": "success_account_updated",
    "status": true
}
```

### Get account information
_Authorized user: User_  

URI
```
GET /api/v1/user/account
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
RESPONSE
```
{
    "account": {
        "birthdate": "1900-01-01",
        "firstname": "John",
        "lastname": "Doe"
    },
    "message": "success_account",
    "status": true
}
```
