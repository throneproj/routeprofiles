# Service check definitions

`checks-v1.json` tells Throne's Service Check which services to probe through a profile and how to read
their answers. Throne fetches it at most once a day, only when the user starts a check, and uses it only
when it parses and its `revision` is higher than the copy built into the app.
