# 02: Account session lifecycle on the remote host

**What to build:** the full local-account loop working remotely: signup
(where enabled), login, who-am-i, logout, and bad-password rejection.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] Login with valid credentials returns a session and `who-am-i` names the user
- [ ] Wrong password is rejected without a session
- [ ] Logout destroys the session (who-am-i afterwards is anonymous)
- [ ] First run result recorded (login/me/logout green as `darren`)
