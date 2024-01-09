# MetaBank API - User related features
  
<i>This documentation will be updated after each update of the platform.</i>  

## Table of contents
[Register User](#register)  

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