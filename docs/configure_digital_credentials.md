### Digital Credentials Configuration

Digital credentials requires an instance of the []`sign-and-verify`]() service to be running.

#### Settings


| Setting | Value | Notes |
|---|---|---|
| `DIGITAL_CREDENTIALS_DEEP_LINK_URL` | `dcwallet://deep_link` | The deep link url to the digital credentials wallet app. This will typically involve a custom url scheme. |
| `DIGITAL_CREDENTIALS_ISSUER_ID` | - | The digital credentials issuer id to be included in the credential template. This value is determined by the digital credentials team. |
| `DIGITAL_CREDENTIALS_VERIFICATION_METHOD` | - | The digital credentials verification method to be included in the credential template. This value is determined by the digital credentials team. |
| `MITOL_DIGITAL_CREDENTIALS_HMAC_SECRET` | - | Any random string, MUST match the corresponding HMAC secret `sign-and-verify` is deployed with. |
| `MITOL_DIGITAL_CREDENTIALS_VERIFY_SERVICE_BASE_URL` | `http://sign-and-verify.example.com:5678/` | The addressable base url for the `sign-and-verify` service. |


#### Feature flags

We will ONLY turn these on when we're ready to enable the feature in production:

| Setting | Value | Notes |
|---|---|---|
| `FEATURE_DIGITAL_CREDENTIALS` | `True`, `False` (default)| Enables the generation of digital credential requests, the prerequisite to being able to generate and sign digital credentials. The corresponding code is triggered when program and course certificates are generated. |
| `FEATURE_DIGITAL_CREDENTIALS_EMAIL` | `True`, `False` (default)| Enables the sending of email notifications for digital credential requests. |
