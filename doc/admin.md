# MetaBank API - Admin related features
  
<i>This documentation will be updated after each update of the platform.</i>  

## Table of contents
[Admin Login](#login-2fa)  
[Refresh Login](#login-refresh)  
[Admin Logout](#logout)  
[Create Admin Account](#create-admin-account)  
[Update Admin Account](#update-admin-account)  
[Generate Admin TOTP](#generate-totp-key)  
[Activate Admin TOTP](#activate-totp)  
[Ask Reset Password Token](#create-reset-password-token)  
[Reset Password](#reset-password)  
[Get Admin Accounts](#get-admin-accounts)  
[Deactivate Admin Account](#deactivate-admin-account)  
[Reactivate Admin Account](#reactivate-admin-account)  
[Get User Accounts](#get-user-accounts)  
[Deactivate User Account](#deactivate-user-account)  
[Reactivate User Account](#reactivate-user-account)  
[Get Wallet Balance](#get-platform-wallet-balance)  

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
    "2fa_token": "098765"       # mandatory if totp is enabled, and only on the second request (2FA by email)
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

### Generate TOTP key
_Authorized user: Admin_  
Set the admin account totp key.  

URI
```
GET /api/v1/admin/totp/generate
```
RESPONSE
```
{
    "base32": "LLWIPYOEZZGKQ3YHKHEZSOVEROKT6ME6",
    "message": "success_totp",
    "otp_auth_url": "otpauth://totp/MetaBank:Admin?secret=LLWIPYOEZZGKQ3YHKHEZSOVEROKT6ME6&issuer=MetaBank",
    "status": true
}
```

### Activate TOTP
_Authorized user: Admin_  
Activate the TOTP authentication method.  

URI
```
POST /api/v1/admin/totp/activate
```
JSON
```
{
    "totp_token": "465426"
}
```
RESPONSE
```
{
    "message": "success_totp",
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
    "message": "success_admin_accounts",
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

### Invite users to register
_Authorized user: Admin_  
Send an invitation email, with optionally a number of tokens to claim.  

URI
```
POST /api/v1/admin/user/invite
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
JSON
```
{
    "emails_list": ["john@codinsight.com"],
    "claimable_tokens": 23.45
}
```
RESPONSE
```
{
    "accounts_not_created": [],                 # returns not created email addresses accounts
    "message": "success_user_accounts",
    "status": true
}
```

### Get user accounts
_Authorized user: Admin_  
Get all user accounts.  

URI  
_deactivated_ arg is optional. By default, the endpoint returns active accounts. Set 'deactivated=true' to get deactivated accounts.  
_pending_ arg is optional. By default, the endpoint returns completed accounts. Set 'pending=true' to get unconfirmed accounts.  
```
GET /api/v1/admin/users?deactivated=false&pending=false     # Return only main information of all the users
GET /api/v1/admin/users/<user_uuid>                         # Get all details of the user
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
RESPONSE (ALL USERS)
```
{
    "message": "success_user_accounts",
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
            "token_claims": {
                "already_claimed": [],
                "to_claim": []
            },
            "updated_date": "2024-01-10T14:49:08.082977Z",
            "user_uuid": "ddeba27c-3d95-450d-b971-33db6e9fbbec"
        }
    ]
}
```
RESPONSE (USER DETAILS)
```
{
    "message": "success_user_accounts",
    "status": true,
    "user_details": {
        "birthdate": "1996-01-16",
        "created_date": "2024-01-11T10:54:40.703862Z",
        "deactivated": false,
        "deactivated_date": null,
        "email_address": "john@doe.com",
        "email_validated": true,
        "firstname": "John",
        "last_login_date": "2024-02-14T15:48:03.158734Z",
        "lastname": "Doe",
        "public_address": "0x...",
        "selfie": "IMG DATA",
        "selfie_ext": "jpg",
        "token_claims": {
            "already_claimed": [
                {
                    "claimed_date": "2024-01-31T16:42:53.181418Z",
                    "created_date": "2024-01-31T16:40:49.049071Z",
                    "nb_token": 66.66,
                    "token_claim_uuid": "1f82a13a-dabf-46f7-b34b-f68cc64561bc",
                    "tx_hash": "0x..."
                },
                {
                    "claimed_date": "2024-01-31T16:31:58.046910Z",
                    "created_date": "2024-01-31T16:17:09.416919Z",
                    "nb_token": 99.0,
                    "token_claim_uuid": "20c243a4-0965-4290-8f99-38748fbb07e0",
                    "tx_hash": "0x..."
                },
                {
                    "claimed_date": "2024-01-31T16:43:19.121733Z",
                    "created_date": "2024-01-31T16:39:35.317492Z",
                    "nb_token": 42.0,
                    "token_claim_uuid": "29b2bdb1-9943-4a88-ac2d-2f32ef18bf24",
                    "tx_hash": "0x..."
                }
            ],
            "to_claim": [
                {
                    "claimed_date": null,
                    "created_date": "2024-02-01T14:53:45.751256Z",
                    "nb_token": 1500.0,
                    "token_claim_uuid": "b9d9ce30-71ba-4c54-8e8e-917b20f27d71",
                    "tx_hash": null
                }
            ],
            "total_claimed": 1947.45,
            "total_to_claim": 1500.0
        },
        "updated_date": "2024-02-09T10:48:50.072856Z",
        "user_uuid": "2afa5a02-8b57-403d-8268-cfacbdf9faba",
        "wallet": {
            "matic": 0.3592487124946442,
            "token_balance": 10500.00001,
            "token_metadata": {
                "address": "0x5D7aA3749fb9bb9fe20534d26CB5a941d9e02871",
                "decimals": 6,
                "logo": null,
                "name": "CaaEURO Stablecoin",
                "symbol": "CaaEURO"
            }
        }
    }
}
```

### Get user operations
_Authorized user: Admin_  
Get CAA operations of the given user.  

URI  
_in_page_key_ arg is optional and used to get older received operations (pagination).  
_out_page_key_ arg is optional and used to get older sent operations (pagination).  
```
GET /api/v1/admin/user/operations/<user_uuid>?in_page_key=...&out_page_key=...
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
RESPONSE
```
{
    "in_page_key": null,                # send the value in a new request to get the next incoming operations
    "message": "success_operations",
    "operations": [
        {
            "asset": "CaaEURO",
            "block": 45111804,
            "block_time": "2024-01-24T14:21:34.000Z",
            "claim_uuid": "3ce1ce38-51c2-42b5-bebe-e3b3f4b33aaa",
            "from": "0x798bf397ee8601243fd76e57fa9fccbb3db7c1e6",
            "hash": "0x09ac51db842d87e98a2b3aeb792ab276fd25ece7bda8a64a0e586ba8b0c42187",
            "to": "0x78e178fe25c8f8247af84315f2ff618b55db0aa7",
            "value": 10
        },
        {
            "asset": "CaaEURO",
            "block": 45111401,
            "block_time": "2024-01-24T14:06:02.000Z",
            "claim_uuid": null,
            "from": "0x78e178fe25c8f8247af84315f2ff618b55db0aa7",
            "hash": "0x58964b3ef60fe5b70f9bdb544a336bfc79fe529c3e33af5d23a76ebabf88ce9f",
            "to": "0x6b2cd455d47026f1fc230a582fbf90f6918235cf",
            "value": 99
        },
        {
            "asset": "CaaEURO",
            "block": 44841952,
            "block_time": "2024-01-16T17:40:03.000Z",
            "claim_uuid": null,
            "from": "0x798bf397ee8601243fd76e57fa9fccbb3db7c1e6",
            "hash": "0xc14012446dd7569bbcee5065eb15ade3bb3ffc8c1e79e1e11c9653fb128d2214",
            "to": "0x78e178fe25c8f8247af84315f2ff618b55db0aa7",
            "value": 10
        }
    ],
    "out_page_key": null,               # send the value in a new request to get the next outgoing operations
    "status": true
}
```

### Deactivate user account
_Authorized user: Admin_  
Deactivate a user account.  

URI
```
POST /api/v1/admin/user/deactivate
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
JSON
```
{
    "user_uuid": ""
}
```
RESPONSE
```
{
    "message": "success_user_deactivated",
    "status": true
}
```

### Reactivate user account
_Authorized user: Admin_  
Reactivate a user account.  

URI
```
POST /api/v1/admin/user/reactivate
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
JSON
```
{
    "user_uuid": ""
}
```
RESPONSE
```
{
    "message": "success_user_reactivated",
    "status": true
}
```

### Get platform wallet balance
_Authorized user: Admin_  
Return MATIC and CAA balances of the platform wallet.  

URI
```
GET /api/v1/admin/wallet/balance
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
RESPONSE
```
{
    "address": "0x9940a09A974BC71b76D095cEF5E38CFF5fe0ea8c",
    "balances": {
        "matic": 0.399416997999685,
        "token_balance": 5000000.0,
        "token_metadata": {
            "address": "0x5D7aA3749fb9bb9fe20534d26CB5a941d9e02871",
            "decimals": 6,
            "logo": null,
            "name": "CaaEURO Stablecoin",
            "symbol": "CaaEURO"
        }
    },
    "message": "success_wallet_balance",
    "status": true
}
```
