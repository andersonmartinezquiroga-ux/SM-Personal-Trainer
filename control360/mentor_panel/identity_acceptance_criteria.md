# SJM Mentor: identity acceptance criteria

The server must validate every access token against the existing identity provider, reject expired sessions, pin a single owner UUID, reject anonymous and non-owner callers, and never expose privileged database keys to a mobile client.

Status: specification only; no real user login is configured or claimed.
