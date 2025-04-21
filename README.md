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

| Full name       | Group     | Email                              |
|-----------------|-----------|------------------------------------|
| Azamat Bayramov | B22-SD-03 | <a.bayramov@innopolis.university>  |
| Darya Koncheva  | B22-SD-02 | <d.koncheva@innopolis.university>  |
| Matthew Rusakov | B22-SD-03 | <m.rusakov@innopolis.university>   |
| Denis Mikhailov | B22-SD-03 | <d.mikhailov@innopolis.university> |
| Ilya Zubkov     | B22-SD-03 | <i.zubkov@innopolis.university>    |

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

* `username` must be unique and at least 3 symbols and at most 20 symbols.
* Password must be at least 8 symbols, at most 32 symbols, with upper-case and lower-case letters, number and custom
  symbols in it.
* Password will be stored in hashed format as `hashed_password` with salt in it.
* `name` must be at least 3 symbols and at most 32 symbols.
* `created_at` is assigned during registration.
* `updated_at` and `password_updated_at` are the same as `created_at` by default.
* `updated_at` changes after any user profile update.
* `password_updated_at` changes after password update.

### Tokens

For auth, access and refresh JWT tokens are used.
Access and refresh tokens lifetimes are specified in .env file.

### Endpoints

1) `POST /auth/register`
    * Request Body: `{"username": "string", "password": "string", "name": "string"}`
    * Response:
        * Success: 200 with JSON
          `{"id": "string", "username": "string", "name": "string", "created_at": datetime, "updated_at": datetime, "password_updated_at": datetime}`
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
        * Success: 200 with JSON
          `{"id": "string", "username": "string", "name": "string", "created_at": datetime, "updated_at": datetime, "password_updated_at": datetime}`
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
        * Success: 200 with JSON
          `{"id": "string", "username": "string", "name": "string", "created_at": datetime, "updated_at": datetime, "password_updated_at": datetime}`
        * Error: 422 with error message - Incorrect name format.

## MoodStamps flow

### MoodStamp database fields

* `id`: uuid4
* `user_id`: string
* `entry_date`: datetime
* `type`: int
* `note`: string
* `created_at`: datetime
* `updated_at`: datetime

### Specific requirements

* `entry_date` is assigned during recording new stamp, must be unique.
* `type` is the mood of the user from 1 to 10.
* `note` is optional. Must be at least empty string, at most 200 symbols.
* `created_at` is assigned during recording new stamp.
* `updated_at` is the same as `created_at` by default.
* `updated_at` changes after any moodStamp update, such as changing note or type.

### Endpoints

1) `POST /mood_diary/record_mood`
    * Request Body: `{"user_id": "string", "type": "int", "note": "string"}`
    * Response:
        * Success: 200 with JSON `{"id": "string", "user_id": "string", "entry_date": datetime,
            "type": "string", "created_at": datetime, "updated_at": datetime}`
        * Error: 400 with error message - MoodStamp already exists.
        * Error: 404 with error message - User not found.
        * Error: 422 with error message - Type/note are in the wrong format.
2) `GET /mood_diary/moodstamp/<entry_date>`
    * Request Body: `{"entry_date": datetime}`
    * Response:
        * Success: 200 with JSON `{"id": "string", "user_id": "string", "entry_date": datetime,
            "type": "string", "created_at": datetime, "updated_at": datetime}`
        * Error: 404 with error message - MoodStamp not found.
3) `GET /mood_diary/month`
    * Request Body: `{"entry_date": datetime}`
    * Response:
        * Success: 200 with JSON `{"entry_date": datetime, "moodstamp": 
               {"id": "string", "user_id": "string", "entry_date": datetime,
                  "type": "string", "created_at": datetime, "updated_at": datetime}}`
4) `GET /mood_diary/diary`
    * Request Body: `{"entry_date": datetime}`
    * Response:
        * Success: 200 with JSON `{"entry_date": datetime, "moodstamp": 
               {"id": "string", "user_id": "string", "entry_date": datetime,
                  "type": "string", "created_at": datetime, "updated_at": datetime}}`
5) `PUT /mood_diary/type`
    * Request Body: `{"entry_date": datetime, "type": "int"}`
    * Response:
        * Success: 200
        * Error: 404 with error message - MoodStamp not found.
        * Error: 400 with error message - New type is in the wrong format.
6) `PUT /mood_diary/note`
    * Request Body: `{"entry_date": datetime, "note": "string"}`
    * Response:
        * Success: 200
        * Error: 404 with error message - MoodStamp not found.
        * Error: 422 with error message - Incorrect note format.
7) `DELETE /mood_diary/unrecord_mood>`
    * Request Body: `{"entry_date": datetime}`
    * Response:
        * Success: 200
        * Error: 404 with error message - MoodStamp not found.
