# Authentication Guide

To access a private ESPN fantasy league, you need to provide two cookie values from an authenticated browser session: `espn_s2` and `swid`. This method is secure as it does not require storing your username or password directly.

## How to find your credentials:

1.  **Log in to ESPN:** Open your web browser (like Chrome or Firefox) and navigate to your fantasy league's homepage on ESPN. Make sure you are logged in.

2.  **Open Developer Tools:**
    *   **Chrome:** Right-click anywhere on the page and select "Inspect", or press `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (Mac).
    *   **Firefox:** Right-click anywhere on the page and select "Inspect Element", or press `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (Mac).

3.  **Navigate to the Application/Storage Tab:**
    *   In the Developer Tools window, find the "Application" tab (in Chrome) or the "Storage" tab (in Firefox).

4.  **Find Cookies:**
    *   On the left-hand panel within the Application/Storage tab, expand the "Cookies" section.
    *   Select `http://fantasy.espn.com` or `http://www.espn.com`.

5.  **Locate the Values:**
    *   A table of cookies will appear. Look for the rows with the names `espn_s2` and `swid`.
    *   Copy the long alphanumeric string found in the "Value" column for each of these cookies. These are your credentials.

**Important:** Do not share these values with anyone. Treat them like passwords.
