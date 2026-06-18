# Security Features Quickstart

To use the newly implemented security features locally:

1. **Start the Application**:
   Run `scripts/dev/newstart.bat` to bring up the backend and frontend.

2. **Access Security Center**:
   - Sign in as the platform owner using the `PLATFORM_OWNER_USERNAME` defined in your `.env`.
   - The system will prompt you to set up MFA via a TOTP app (e.g., Google Authenticator).
   - Once set up, you can access the Security Center at `http://localhost:3001/admin/security`.

3. **Manage Roles**:
   - Navigate to the Roles section in the Security Center.
   - You can assign `security_engineer` or `admin` roles to other users.

4. **Run a Simulation**:
   - In the Security Center, trigger a "Suspicious Input Simulation".
   - View the generated events in the Event History tab, which will be explicitly marked as `[SIMULATION]`.
