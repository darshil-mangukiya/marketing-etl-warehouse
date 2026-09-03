# OAuth and Secret Handling

`OAuthToken` models access/refresh tokens and expiration. `OAuth2RefreshClient` refreshes an expiring token via an injected HTTP session and emits only redacted failure messages. Tokens are not logged. Vendor-specific consent and scopes remain manual.

`SecretProvider` has environment and Google Secret Manager implementations. Local mode uses environment variables. Cloud mode may access `projects/<project>/secrets/<name>/versions/latest`; missing dependency/access errors identify the secret name but never its value. Use least privilege (`roles/secretmanager.secretAccessor`) on individual secrets and prefer keyless Application Default Credentials/service-account impersonation.

Never put credentials in `.env.example`, Terraform variables, GitHub logs, screenshots, test payloads, or committed `.env` files. Rotate any value accidentally exposed and invalidate its refresh token.
