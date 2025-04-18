# sqrs-project

## Auth flow

### User database fields

- `username`: string
- `hashed_password`: string
- `name`: string (optional)

### Specific requirements

- Username must be unique and at least 3 symbols and at most 20 symbols.
- Password must be at least 8 symbols, at most 32 symbols, with upper-case and lower-case letters, number and custom symbols in it.
- Password will be stored in hashed format with salt in it.
- Name is optional, but if present, it must be at least 3 symbols and at most 32 symbols.

### Tokens

For auth, access and refresh JWT tokens are used.
Access and refresh tokens lifetimes are specified in .env file.

### Endpoints

1) `POST /auth/register`
    - Request Body: `{"username": "string", "password": "string", "name": "string"}`
    - Name is optional.
    - Response:
        - Success: 200
        - Error: 400 with error message - Username already exists, or username/name/password are in the wrong format.
2) `POST /auth/generate-token`
    - Request Body: `{"username": "string", "password": "string"}`
    - Response:
        - Success: 200 with JSON `{"access_token": "string", "refresh_token": "string"}`
        - Error: 401 with error message - Incorrect password or username does not exist.
3) `POST /auth/validate-token`
    - Request Header: `Authorization: Bearer <access_token>`
    - Response:
        - Success: 200
        - Error: 401 with error message - Invalid or expired token.
4) `POST /auth/refresh`
    - Request Body: `{"refresh_token": "string"}`
    - Response:
        - Success: 200 with JSON `{"access_token": "string"}`
        - Error: 401 with error message - Invalid or expired refresh token.
5) `PUT /auth/update-password`
    - Request Header: `Authorization: Bearer <access_token>`
    - Request Body: `{"old_password": "string", "new_password": "string"}`
    - Response:
        - Success: 200
        - Error: 401 with error message - Incorrect old password or new password is in the wrong format.
6) `PUT /auth/update-info`
    - Request Header: `Authorization: Bearer <access_token>`
    - Request Body: `{"new_name": "string"}`
    - Response:
        - Success: 200
        - Error: 400 with error message - Incorrect name format.
