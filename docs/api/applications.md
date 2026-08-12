# Applications API

The Applications API allows you to retrieve information about applications within a project.

## List Applications

This endpoint retrieves a list of all applications within a specific project.

- **Endpoint:** `GET /api/o/{org}/p/{prj}/a/`
- **Authentication:** `ApiKeyAuthentication`
- **Permissions:** `organization:read`

### URL Parameters

-   `org` (string, required): The slug of the organization.
-   `prj` (string, required): The slug of the project.

### Response

-   **`200 OK`**: The request was successful. The response body will contain a list of application objects.
    ```json
    [
        {
            "name": "<application_name>",
            "slug": "<application_slug>",
            "events": "<url_to_events_list>"
        },
        ...
    ]
    ```
-   **`401 UNAUTHORIZED`**: The API key is invalid or missing.
-   **`403 FORBIDDEN`**: The API key does not have the required `organization:read` permission.
-   **`404 NOT FOUND`**: The specified organization or project does not exist.

---

## Register User as Application Member

This endpoint registers a user as member of a specific application. It is
intended to be called by the remote application when a user signs up. To stop a
user's notifications from an application, see the
[unsubscribe endpoint](distribution_lists.md#unsubscribe-user-from-application-distribution-lists).

The endpoint is idempotent: calling it twice with the same payload does not
fail nor duplicate records.

- **Endpoint:** `POST /api/o/{org}/p/{prj}/a/{app}/register/`
- **Authentication:** `ApiKeyAuthentication`
- **Permissions:** `manage_application_users`

### URL Parameters

-   `org` (string, required): The slug of the organization.
-   `prj` (string, required): The slug of the project.
-   `app` (string, required): The slug of the application.

### Request Body

```json
{
    "username": "u123",
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane@example.com",
    "custom_fields": {"plan": "gold"},
    "active": true,
    "addresses": [
        {
            "value": "jane@example.com",
            "name": "work email",
            "assign_to_preferred_channel": true
        }
    ],
    "distribution_list": "customers"
}
```

-   `username` (string, required): The username of the user to register. If no
    user with this username exists, it is created with the provided
    `first_name`, `last_name` and `email`; an existing user is never updated.
-   `custom_fields` (object, optional): Merged into the membership custom
    fields. Data is stored per application: registering the same user in
    another application keeps independent custom fields.
-   `active` (boolean, optional, default `true`): Mirrors the client
    application's "active" state for the user; each register call sets it.
    When `false` the user receives no notifications for this application.
    The membership also has `locked` (managed only via the Bitcaster admin)
    and `enable_notifications` flags: notifications are delivered only when
    the membership is active, not locked and has notifications enabled.
    Users without a membership record are unaffected.
-   `addresses` (list, optional): Addresses to create for the user. The address
    type (email, phone, ...) is derived from `value`; `name` defaults to the
    derived type. When `assign_to_preferred_channel` is true, an assignment is
    created (already validated) between the address and every *preferred*
    channel whose protocol is compatible with the address type. Channels of the
    application's project take precedence over organization-level ones.
-   `distribution_list` (string, optional): Name of a distribution list of the
    application's project; the created assignments are added to its recipients.

### Response

-   **`201 CREATED`** / **`200 OK`**: The user was created (201) or already
    existed (200).
    ```json
    {
        "user": {
            "username": "u123",
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com"
        },
        "created": true,
        "membership": {
            "custom_fields": {"plan": "gold"},
            "active": true,
            "locked": false,
            "enable_notifications": true
        },
        "addresses": [
            {"value": "jane@example.com", "name": "work email", "type": "email"}
        ],
        "assignments": [
            {"address": "jane@example.com", "channel": "email-channel", "protocol": "EMAIL"}
        ],
        "distribution_list": {"name": "customers", "recipients_added": 1}
    }
    ```
-   **`400 BAD REQUEST`**: Validation error: malformed payload, unknown
    distribution list, or distribution list pinned to another application.
-   **`401 UNAUTHORIZED`**: The API key is invalid or missing.
-   **`403 FORBIDDEN`**: The API key does not have the required
    `MANAGE_APPLICATION_USERS` grant, or its scope does not match the URL.
-   **`404 NOT FOUND`**: The specified organization, project, or application
    does not exist.

---

## Unregister User from Application

This endpoint deletes the [application membership](../glossary/terms/application-member.md)
of a user, reversing the register endpoint. Distribution list subscriptions
are not affected — use the
[unsubscribe endpoint](distribution_lists.md#unsubscribe-user-from-application-distribution-lists)
for that.

- **Endpoint:** `POST /api/o/{org}/p/{prj}/a/{app}/unregister/{username}/`
- **Authentication:** `ApiKeyAuthentication`
- **Permissions:** `manage_application_users`

### URL Parameters

-   `org` (string, required): The slug of the organization.
-   `prj` (string, required): The slug of the project.
-   `app` (string, required): The slug of the application.
-   `username` (string, required): The username of the user to unregister.

### Response

-   **`200 OK`**: Returns the number of deleted memberships (`0` when the user
    has no membership for the application — the call is idempotent).
    ```json
    {
        "deleted": 1
    }
    ```
-   **`401 UNAUTHORIZED`**: The API key is invalid or missing.
-   **`403 FORBIDDEN`**: The API key does not have the required
    `MANAGE_APPLICATION_USERS` grant, or its scope does not match the URL.
-   **`404 NOT FOUND`**: The specified organization, project, application, or
    user does not exist.
