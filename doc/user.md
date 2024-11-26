# LiFiSe API - User related features
  
<i>This documentation will be updated after each update of the platform.</i>  

## Table of contents
[Register User](#register)  
[Decline Invitation](#decline-invitation)  
[Verify If Email Exists](#verify-if-an-email-already-exists)  
[Login](#login)  
[Refresh Login](#login-refresh)  
[Logout](#logout)  
[Update Account](#update-account)  
[Get Account](#get-account-information)  
[Retrieve Operations](#get-operations)  
[Search User](#search-user)  
[Add A Beneficiary](#add-beneficiary)  
[Remove A Beneficiary](#remove-beneficiary)  
[Get Beneficiaries](#get-beneficiaries)  
[Claim Tokens](#claim-tokens)  
[Assistance Message](#assistance-message)  
[Create Order](#create-order)  
[Get Orders](#get-orders)  
[Init KYC](#init-kyc-session)  
[Get KYC Status](#get-kyc-details)  

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
    "email_address": "john@doe.com",
    "did_token": "xxx",
    "user_uuid": ""                     # optional, only used if the user has been invited and pre-registered by LiFiSe
}
```
RESPONSE
```
{
    "message": "success_user_register",
    "status": true
}
```

### Decline Invitation
_Authorized user: User_  
Decline invitation and deactivate pre-registered account.  

URI
```
POST /api/v1/user/decline
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

### Verify if an email already exists
_Authorized user: User_  
Verify if the given email address is already registered on the platform.  

URI
```
POST /api/v1/user/is_registered
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
    "message": "success_already_exixts",
    "status": true                          # false if the email does not exist
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
    "did_token": "xxx"
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
        "kyc_status": "SUBMISSION_REQUIRED",
        "kyc_status_date": "2024-03-10T14:19:52.570413Z",
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
    "status": true,
    "wallet": {
        "matic": 0.35971071249755476,
        "token_balance": 1100.0,
        "token_metadata": {
            "address": "0x5D7aA3749fb9bb9fe20534d26CB5a941d9e02871",
            "decimals": 6,
            "logo": null,
            "name": "EuroLFS Stablecoin",
            "symbol": "EUROLFS"
        }
    }
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
        "kyc_status": "SUBMISSION_REQUIRED",
        "kyc_status_date": "2024-03-10T14:19:52.570413Z",
        "lastname": "D.",
        "public_address": "0x...",
        "selfie": "IMG_DATA",
        "selfie_ext": "png",
        "updated_date": "2023-12-27T18:00:40.916883Z",
        "user_uuid": "87780317-546e-4051-a8f1-da4fbbb06ac8"
    },
    "message": "success_account",
    "status": true,
    "token_claim": [
        {
            "created_date": "2024-01-19T17:04:22.440374Z",
            "nb_token": 11.0,
            "token_claim_uuid": "308d3996-45a3-440e-9e00-f5e5ee1cf0f2"
        },
        {
            "created_date": "2024-01-18T16:53:33.268209Z",
            "nb_token": 23.45,
            "token_claim_uuid": "8e34e7be-f04f-4710-b59b-66ff915a4bfc"
        },
        {
            "created_date": "2024-01-18T16:51:13.916527Z",
            "nb_token": 12.34,
            "token_claim_uuid": "8e47cd01-f150-47dd-88df-0a33026e56a5"
        }
    ],
    "total_to_claim": 46.79,
    "wallet": {
        "matic": 0.35971071249755476,
        "token_balance": 1100.0,
        "token_metadata": {
            "address": "0x5D7aA3749fb9bb9fe20534d26CB5a941d9e02871",
            "decimals": 6,
            "logo": null,
            "name": "EuroLFS Stablecoin",
            "symbol": "EUROLFS"
        }
    }
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

### Get operations
_Authorized user: User_  
Return user operations (EUROLFS).  

URI
_in_page_key_ arg is optional and used to get older received operations (pagination).  
_out_page_key_ arg is optional and used to get older sent operations (pagination).  
```
GET /api/v1/user/operations
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
RESPONSE
```
{
    "in_page_key": null,                        # send the value in a new request to get the next incoming operations
    "message": "success_operations",
    "operations": [
        {
            "asset": "EuroLFS",
            "block": 45111804,
            "block_time": "2024-01-24T14:21:34.000Z",
            "claim_uuid": null,
            "from": "0x798bf397ee8601243fd76e57fa9fccbb3db7c1e6",
            "hash": "0x09ac51db842d87e98a2b3aeb792ab276fd25ece7bda8a64a0e586ba8b0c42187",
            "to": "0x78e178fe25c8f8247af84315f2ff618b55db0aa7",
            "value": 10
        },
        {
            "asset": "EuroLFS",
            "block": 45111401,
            "block_time": "2024-01-24T14:06:02.000Z",
            "claim_uuid": null,
            "from": "0x78e178fe25c8f8247af84315f2ff618b55db0aa7",
            "hash": "0x58964b3ef60fe5b70f9bdb544a336bfc79fe529c3e33af5d23a76ebabf88ce9f",
            "to": "0x6b2cd455d47026f1fc230a582fbf90f6918235cf",
            "value": 99
        }
    ],
    "out_page_key": null,                       # send the value in a new request to get the next outgoing operations
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
Add with a public address (Wallet address):  
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

### Claim tokens
_Authorized user: User with KYC_  
Send a list of claim uuid to send tokens to the user.  

URI
```
POST /api/v1/user/claim
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
JSON  
```
{
    "claim_uuid": [
        "308d3996-45a3-440e-9e00-f5e5ee1cf0f2",
        "8e34e7be-f04f-4710-b59b-66ff915a4bfc",
        "8e47cd01-f150-47dd-88df-0a33026e56a5",
        "8e47cd01-f150-47dd-88df-0a33026e56a5",
        "8e47cd01-f150-47dd-88df-0a33026e56a1"
    ]
}
```
RESPONSE
```
{
    "message": "success_operation",
    "status": true,
    "transactions": {
        "8e34e7be-f04f-4710-b59b-66ff915a4bfc": {
            "nb_token": 23.45,
            "receiver": "0x78E178Fe25c8F8247aF84315F2Ff618b55Db0aA7",
            "tx_hash": "0x1cb5c41f6f35e49c2d4491dbc2ac27c3a70dd3038d8590fc021f5e9a66e845af"     # succeed
        },
        "8e47cd01-f150-47dd-88df-0a33026e56a5": {
            "nb_token": 12.34,
            "receiver": "0x78E178Fe25c8F8247aF84315F2Ff618b55Db0aA7",
            "tx_hash": None                                                                     # failed
        }
    }
}
```

### Assistance message
_Authorized user: User_  
Send a message to admin for assistance.  
Message is sent to email addresses of active administrators.  

URI
```
POST /api/v1/user/assistance
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
JSON  
```
{
    "message": "Help !"
}
```
RESPONSE
```
{
    "message": "success_sent",
    "status": true
}
```

### Create order
_Authorized user: User with KYC_  
Create an order to purchase EUROLFS tokens.  

URI
```
POST /api/v1/user/purchase/order
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
JSON  
```
{
    "nb_tokens": 100
}
```
RESPONSE
```
{
    "bank_account": {
        "bank_name": "ACME Pay Ltd.",
        "bic_swift": "FRXXXXX",
        "iban": "AAAA BBBB CCCC DDDD EEEE",
        "vendor_address": "16 Cours Alexandre Borodine - 26000 VALENCE",
        "vendor_name": "LiFiSe France SAS"
    },
    "message": "success_saved",
    "price_eur": 100,
    "reference": "xlfZXJMLigBJ",
    "status": true
}
```

### Get orders
_Authorized user: User_  
Get orders history of the user.  

URI
```
GET /api/v1/user/purchase/order
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
RESPONSE
```
{
    "message": "success_purchase",
    "orders": [
        {
            "created_date": "2024-03-25T15:01:26.318156Z",
            "nb_token": 400.0,
            "payment_date": null,
            "amount_received": null,
            "reference": "xlfZXJMLigBJ",
            "total_price_eur": 400.0,
            "tx_hash": null,
            "user_purchase_uuid": "d37b7356-c980-4c23-b77b-abc28ad60425"
        },
        {
            "created_date": "2024-03-25T15:00:44.418891Z",
            "nb_token": 150.0,
            "payment_date": null,
            "amount_received": null,
            "reference": "SJICTeDEhLpR",
            "total_price_eur": 150.0,
            "tx_hash": null,
            "user_purchase_uuid": "31149e74-9b88-4322-90d5-10a8f993edc8"
        }
    ],
    "status": true
}
```

### Init KYC session
_Authorized user: User_  
Init the KYC session for the user.  

URI
```
GET /api/v1/user/kyc/session
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
RESPONSE
```
{
    "kyc_session_id": "e7d34253-6865-484c-a702-8e2611d5789d",
    "message": "success_kyc_session",
    "status": true
}
```

### Get KYC details
_Authorized user: User_  
Get the KYC details and current status.  

URI
```
GET /api/v1/user/kyc/details
```
HEADER
```
X-AUTH-USER: "JWT_token"
```
RESPONSE
```
{
    "kyc_session_id": "e7d34253-6865-484c-a702-8e2611d5789d",
    "kyc_status": "SUBMISSION_REQUIRED",
    "kyc_status_date": "2024-03-27T17:09:12.064829Z",
    "message": "success_kyc_status",
    "status": true
}
```
