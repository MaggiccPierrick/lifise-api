# MetaBank API - User related features
  
<i>This documentation will be updated after each update of the platform.</i>  

## Table of contents
[Register User](#register)  
[Validate Account](#validate-account)  
[Login](#login)  
[Refresh Login](#login-refresh)  
[Logout](#logout)  
[Update Account](#update-account)  
[Get Account](#get-account-information)  
[Search User](#search-user)  
[Add A Beneficiary](#add-beneficiary)  
[Remove A Beneficiary](#remove-beneficiary)  
[Get Beneficiaries](#get-beneficiaries)  

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
        "birthdate": "2023-12-27",
        "created_date": "2023-12-27T14:00:04.512864Z",
        "email_address": "john@doe.com",
        "firstname": "John",
        "lastname": "D.",
        "public_address": "0x...",
        "selfie": "IMG_DATA",
        "selfie_ext": "png",
        "updated_date": "2023-12-27T18:00:40.916883Z",
        "user_uuid": "87780317-546e-4051-a8f1-da4fbbb06ac8"
    },
    "jwt_token": "eyJhbG...",
    "message": "success_login",
    "refresh_token": "eyJhbGci...",
    "refresh_expiration": "2024-01-16T21:48:54.762722Z",
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
    "birthdate": "1900-01-01",
    "selfie": "IMG_DATA",
    "selfie_ext": "png"                # type of uploaded file. Optional, 'jpg' by default.
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
Return the personal information of the connected user or public profile of the requested user.  

URI
```
GET /api/v1/user/account                # get full profile of the user
GET /api/v1/user/account/<user_uuid>    # get public profile of the other user
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
RESPONSE  
Full personal profile
```
{
    "account": {
        "birthdate": "2023-12-27",
        "created_date": "2023-12-27T14:00:04.512864Z",
        "email_address": "john@doe.com",
        "firstname": "John",
        "lastname": "D.",
        "public_address": "0x...",
        "selfie": "IMG_DATA",
        "selfie_ext": "png",
        "updated_date": "2023-12-27T18:00:40.916883Z",
        "user_uuid": "87780317-546e-4051-a8f1-da4fbbb06ac8"
    },
    "message": "success_account",
    "status": true
}
```
Public profile
```
{
    "account": {
        "email_address": "john@doe.com",
        "firstname": "John",
        "lastname": "D.",
        "public_address": "0x...",
        "selfie": "IMG_DATA",
        "selfie_ext": "png",
        "user_uuid": "87780317-546e-4051-a8f1-da4fbbb06ac8"
    },
    "message": "success_account",
    "status": true
}
```

### Search user
_Authorized user: User_  
Search a registered user with email address.  

URI
```
POST /api/v1/user/search
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
JSON
```
{
    "email_address": "john@mail.com"
}
```
RESPONSE
```
{
    "message": "success_user_found",
    "status": true,
    "user": {
        "email_address": "john@mail.com",
        "firstname": null,
        "lastname": null,
        "public_address": "0x8d...",
        "selfie": null,
        "selfie_ext": null,
        "user_uuid": "19034c2c-d9ef-41e7-8f87-5fa7aa7ff836"
    }
}
```

### Add beneficiary
_Authorized user: User_  
Add a beneficiary with a public address and email (optional), or his user uuid.  

URI
```
POST /api/v1/user/beneficiary
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
JSON  
Add with a public address (Polygon address):  
```
{
    "public_address": "0x1234567",
    "email_address": "address@mail.com",                    # optional
    "2fa_token": ""                                         # only for the second request to validate with 2FA
}
```
Add a registered user, with his uuid:  
```
{
    "user_uuid": "19034c2c-d9ef-41e7-8f87-5fa7aa7ff836",
    "2fa_token": ""                                         # only for the second request to validate with 2FA
}
```
RESPONSE
```
{
    "message": "success_beneficiary_added",
    "status": true
}
```

### Remove beneficiary
_Authorized user: User_  
Remove a beneficiary from user's list.  

URI
```
POST /api/v1/user/beneficiary/remove
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
JSON  
Add with a public address (Polygon address):  
```
{
    "beneficiary_uuid": "900fe01c-d5f5-40d2-8927-7675f7cf1172"
}
```
RESPONSE
```
{
    "message": "success_removed",
    "status": true
}
```

### Get beneficiaries
_Authorized user: User_  
Get the beneficiaries of the user.  

URI
```
GET /api/v1/user/beneficiary
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
RESPONSE
```
{
    "beneficiaries": [
        {
            "beneficiary_uuid": "a703c152-aa4d-4157-867f-cc8e5db73a42",
            "created_date": "2024-01-15T16:45:14.194744Z",
            "email": null,
            "public_address": null,
            "user_uuid": "19034c2c-d9ef-41e7-8f87-5fa7aa7ff836"
        },
        {
            "beneficiary_uuid": "f7786284-4a9f-4733-af3a-d06f367d02f2",
            "created_date": "2024-01-15T16:45:23.300970Z",
            "email": "eve@mail.com",
            "public_address": "0x1234567890",
            "user_uuid": null
        }
    ],
    "message": "success_beneficiary_retrieved",
    "status": true
}
```
