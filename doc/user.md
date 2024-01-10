# MetaBank API - User related features
  
<i>This documentation will be updated after each update of the platform.</i>  

## Table of contents
[Register User](#register)  
[Validate Account](#validate-account)  
[Login](#login)  

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
    "message": "success_login",
    "status": true
}
```
