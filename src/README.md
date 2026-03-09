# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Persistent SQLite storage (data survives server restarts)
- Normalized foundational schema for users, clubs, memberships, events, and notifications

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |

## Data Model

The application now uses a normalized SQLite schema with validated models:

1. **users**

   - `email` (unique)
   - `role` (`STUDENT`, `CLUB_LEAD`, `ADMIN`)
   - `full_name` (optional)

2. **clubs**

   - `name` (unique)
   - `category`
   - `description`
   - `status` (`PENDING`, `APPROVED`)
   - `lead_user_id` (optional)

3. **memberships**

   - `user_id`, `club_id` (unique pair)
   - `status` (`PENDING`, `APPROVED`, `REJECTED`)
   - `created_at`, `updated_at`

4. **events** (current activities are stored here)

   - `name` (unique)
   - `description`
   - `schedule`
   - `max_participants`
   - `club_id` (optional)

5. **event_registrations**

   - `event_id`, `user_id` (unique pair)
   - `created_at`

6. **notifications**

   - `title`
   - `body`
   - `audience`
   - `created_at`

The API response shape for `/activities` is unchanged and still returns:

- Activity name as key
- Description
- Schedule
- Maximum participants
- List of participant emails

On first startup, the app auto-seeds the database with the original sample activities and registrations.
