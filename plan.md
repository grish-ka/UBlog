# Plan

## Summary
Create a simple-but-powerful blogging platform where users can sign up, create topics, post content, and view lightweight analytics. The app should support role-based permissions (admin, moderator, regular user) and use Gravatar for avatars.

## Goals
- Provide a friendly UX for writing and browsing posts
- Enable user registration and authentication
- Offer topics/tags to organize posts
- Provide basic analytics (views, likes, post counts)
- Support role-based controls for moderation and site administration

## Roles & Permissions
- Admin: full access — change site title, manage users, global settings (display a blue cog for admin actions)
- Moderator: moderate content, flag/remove posts, manage comments (display a purple cog for moderator actions)
- User: create/edit their posts, comment, follow topics, view analytics for their posts

## Key Features
- Authentication: sign up, login, password reset
- Profiles: display name, email (Gravatar for avatar), bio
- Posts: create, edit, delete, drafts, publish
- Topics: create and subscribe to topics; each post belongs to one or more topics
- Analytics: per-post views, likes, and simple dashboard for users (last 30 days)
- Moderation tools: flagging, soft-delete, and restore
- Admin settings: change site title, manage roles and content

## Non-functional Requirements
- Keep the codebase minimal and easy to understand
- Docker-friendly for local testing and deployment
- Reasonable security: sanitize input, protect endpoints
- Responsive UI using simple templates/CSS

## Tech suggestions
- Backend: minimal web framework (Flask, Express, or similar depending on language)
- Storage: lightweight DB (SQLite for prototyping; Postgres for production)
- Templates: simple HTML templates under `templates/`
- Auth: session-based or JWT for API; integrate email later if needed

## Milestones
1. Project scaffolding, Dockerfile, basic README
2. Authentication and user profiles
3. Post editor, topics, and templates
4. Roles and moderation UI (blue/purple cogs)
5. Basic analytics dashboard and per-post metrics
6. Polish, tests, and documentation

## Acceptance criteria
- Users can register, login, and create posts
- Topics can be created and posts assigned to topics
- Admins can update site title and manage users
- Moderators can flag and remove posts
- Simple analytics page shows views/likes per post

## Next steps
- Turn milestones into issues/tickets
- Sketch UI for post editor and dashboard
- Implement milestone (1): scaffold and auth

