# Mood Diary

## Table of contents

* [Team Information](#team-information)
* [Auth flow](#auth-flow)
  * [User database fields](#user-database-fields)
  * [Specific requirements](#specific-requirements)
  * [Tokens](#tokens)
  * [Endpoints](#endpoints)

## Team information

### DOBR BOBR

| Full name       | Group     | Email                           |
|-----------------|-----------|---------------------------------|
| Azamat Bayramov | B22-SD-03 | <a.bayramov@innopolis.university> |
| Darya Koncheva  | B22-SD-02 | <d.koncheva@innopolis.university> |
| Matthew Rusakov | B22-SD-03 | <m.rusakov@innopolis.university>  |
| Denis Mikhailov | B22-SD-03 | <d.mikhailov@innopolis.university>|
| Ilya Zubkov     | B22-SD-03 | <i.zubkov@innopolis.university>   |

## Auth flow

### User database fields

* `id`: uuid4
* `username`: string
* `hashed_password`: string
* `name`: string
* `created_at`: datetime
* `updated_at`: datetime
* `password_updated_at`: datetime

### Specific requirements

* Username must be unique and at least 3 symbols and at most 20 symbols.
* Password must be at least 8 symbols, at most 32 symbols, with upper-case and lower-case letters, number and custom symbols in it.
* Password will be stored in hashed format with salt in it.
* Name must be at least 3 symbols and at most 32 symbols.

### Tokens

For auth, access and refresh JWT tokens are used.
Access and refresh tokens lifetimes are specified in .env file.

### Endpoints

1) `POST /auth/register`
    * Request Body: `{"username": "string", "password": "string", "name": "string"}`
    * Response:
        * Success: 200 with JSON `{"id": "string", "username": "string", "name": "string", "created_at": datetime, "updated_at": datetime, "password_updated_at": datetime}`
        * Error: 400 with error message - Username already exists.
        * Error: 422 with error message - Username/name/password are in the wrong format.
2) `POST /auth/login`
    * Request Body: `{"username": "string", "password": "string"}`
    * Response:
        * Success: 200 with JSON `{"access_token": "string", "refresh_token": "string"}`
        * Error: 401 with error message - Incorrect password or username does not exist.
3) `POST /auth/validate`
    * Request Header: `Authorization: Bearer <access_token>`
    * Response:
        * Success: 200
        * Error: 401 with error message - Invalid or expired token.
4) `POST /auth/refresh`
    * Request Body: `{"refresh_token": "string"}`
    * Response:
        * Success: 200 with JSON `{"access_token": "string"}`
        * Error: 401 with error message - Invalid or expired refresh token.
5) `GET /auth/profile`
    * Request Header: `Authorization: Bearer <access_token>`
    * Response:
        * Success: 200 with JSON `{"id": "string", "username": "string", "name": "string", "created_at": datetime, "updated_at": datetime, "password_updated_at": datetime}`
6) `PUT /auth/password`
    * Request Header: `Authorization: Bearer <access_token>`
    * Request Body: `{"old_password": "string", "new_password": "string"}`
    * Response:
        * Success: 200
        * Error: 401 with error message - Incorrect old password.
        * Error: 400 with error message - New password is in the wrong format.
7) `PUT /auth/profile`
    * Request Header: `Authorization: Bearer <access_token>`
    * Request Body: `{"name": "string"}`
    * Response:
        * Success: 200 with JSON `{"id": "string", "username": "string", "name": "string", "created_at": datetime, "updated_at": datetime, "password_updated_at": datetime}`
        * Error: 422 with error message - Incorrect name format.
