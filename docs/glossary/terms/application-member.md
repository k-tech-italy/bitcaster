---
description:  A <glossary:User> registered as member of an <glossary:Application>
template: term.html
terms:
  - glossary:
    - Application Member
    - ApplicationMembership
---

a <glossary:User> registered as member of an <glossary:Application>.

The membership is a qualified relationship between the user and the
application: it stores per-application custom fields provided by the
<glossary:remote system>. Members are created through the application
`register` API and removed through the `unregister` API.

The membership gates notifications: the user receives notifications from the
application only when the membership is `active` (mirrors the client
application state, settable via the `register` API), not `locked` (managed
only via the Bitcaster admin) and has `enable_notifications` set.
