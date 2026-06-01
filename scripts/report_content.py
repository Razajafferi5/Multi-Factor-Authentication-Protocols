"""Authored content for the technical report.

This module holds ONLY the report's text, tables, equations, figure references
and citations as structured Python data. The layout/formatting engine lives in
``scripts/generate_report.py`` and consumes these structures. Keeping prose
separate from formatting code makes the report easy to edit.

Block grammar consumed by the builder (each section's ``blocks`` is a list):

* ("para", str)                         - a body paragraph
* ("sub", str)                          - a sub-heading
* ("bullet", [str, ...])                - bulleted list
* ("numbered", [str, ...])              - numbered list
* ("figure", filename, caption)         - embed docs/figures/<filename>
* ("table", caption, [headers], [rows]) - a captioned table
* ("equation", str)                     - a numbered, right-aligned equation
* ("code", caption, str)                - a Courier-New code listing
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Cover-page metadata (placeholders for the team to fill in).
# ---------------------------------------------------------------------------
META = {
    "title": "Design and Implementation of a Multi-Factor Authentication Server with an AI-Driven Login Anomaly Detection Layer",
    "course_code": "[COURSE CODE]",
    "course_name": "Information Security",
    "university": "[UNIVERSITY NAME]",
    "department": "[DEPARTMENT NAME]",
    "supervisor": "[SUPERVISOR NAME]",
    "date": "[SUBMISSION DATE]",
    "team": [
        "[Team Member 1 - Roll No]",
        "[Team Member 2 - Roll No]",
        "[Team Member 3 - Roll No]",
    ],
    "logo_placeholder": "[INSERT UNIVERSITY LOGO HERE]",
}

# ---------------------------------------------------------------------------
# Abstract (150-200 words).
# ---------------------------------------------------------------------------
ABSTRACT = (
    "Passwords alone remain the weakest link in modern authentication, and "
    "credential-stuffing and phishing attacks routinely defeat single-factor "
    "logins. This project designs and implements a complete multi-factor "
    "authentication (MFA) server that combines standards-compliant one-time "
    "passwords with hardware-backed and out-of-band factors, and augments them "
    "with an artificial-intelligence layer that detects anomalous logins. The "
    "HMAC-based and time-based one-time-password algorithms are implemented "
    "directly from RFC 4226 and RFC 6238 rather than relying on a library, and "
    "their correctness is proven against the published RFC test vectors and an "
    "independent reference oracle. Shared secrets are encrypted at rest with "
    "AES-256-GCM, and passwords are hashed with Argon2id. The server also "
    "provides FIDO2/WebAuthn, a simulated push factor, single-use backup codes, "
    "and brute-force lockout with CAPTCHA. Every authentication attempt is "
    "logged and scored by an Isolation Forest model, with a large-language-model "
    "explanation that degrades gracefully when unavailable. A Streamlit admin "
    "dashboard visualises users, the audit log, anomaly alerts and analytics. "
    "Automated tests confirm cryptographic correctness and resistance to replay "
    "and brute-force attacks."
)

# ---------------------------------------------------------------------------
# Sections 1-10 (plus references and appendices defined separately).
# ---------------------------------------------------------------------------
SECTIONS = [
    {
        "number": "1",
        "title": "Introduction",
        "blocks": [
            ("sub", "1.1 Background"),
            ("para",
             "Authentication is the process of verifying that a principal is who it "
             "claims to be, and it underpins almost every security control in a "
             "networked system. For decades the dominant mechanism has been the "
             "reusable password, but large-scale breaches have shown that passwords "
             "are frequently reused, weak, phished, or leaked. Multi-factor "
             "authentication (MFA) mitigates these weaknesses by requiring evidence "
             "from two or more independent categories: something the user knows (a "
             "password), something the user has (a phone, security key, or one-time "
             "code), and something the user is (a biometric). Even when one factor is "
             "compromised, an attacker must still defeat the others."),
            ("para",
             "Modern MFA increasingly pairs these deterministic factors with risk-based "
             "or adaptive authentication, in which contextual signals such as the "
             "login location, device, and time are analysed to estimate the "
             "likelihood that a login is fraudulent. This project builds a complete "
             "MFA server that implements the core cryptographic factors from first "
             "principles and layers an explainable anomaly-detection model on top of "
             "the authentication audit log."),
            ("para",
             "The threat landscape motivates this work. Automated credential-stuffing "
             "campaigns replay billions of leaked username-password pairs against login "
             "endpoints, phishing kits proxy legitimate sites to capture both passwords "
             "and one-time codes, and SIM-swap attacks defeat SMS-delivered codes. No "
             "single factor resists all of these simultaneously: SMS codes are "
             "vulnerable to SIM swapping, push prompts are vulnerable to approval "
             "fatigue, and even authenticator-app codes can be phished in real time. A "
             "layered design that offers phishing-resistant hardware factors alongside "
             "one-time passwords, and that watches the audit log for behavioural "
             "anomalies, therefore provides materially stronger protection than any "
             "factor used alone. This project is built around that layered philosophy."),
            ("sub", "1.2 Problem Statement"),
            ("para",
             "Many student and even production MFA implementations treat one-time "
             "password generation as a black box by calling a third-party library, "
             "store shared secrets insecurely, and provide no visibility into "
             "suspicious authentication behaviour. The problem addressed here is to "
             "build an MFA server that (a) implements the HOTP and TOTP algorithms "
             "correctly from their specifications, (b) protects all secret material "
             "at rest, (c) supports a realistic range of factors, and (d) turns the "
             "authentication log into an actionable, explainable risk signal for "
             "administrators."),
            ("sub", "1.3 Objectives"),
            ("numbered", [
                "Implement HOTP (RFC 4226) and TOTP (RFC 6238) from scratch and prove their correctness against the published RFC test vectors and an independent oracle.",
                "Protect all shared secrets at rest using AES-256-GCM and hash all passwords and backup codes with Argon2id.",
                "Provide multiple authentication factors: TOTP, HOTP, FIDO2/WebAuthn, push approval, and single-use backup codes.",
                "Harden the server against online attacks with sliding-window lockout and a CAPTCHA challenge.",
                "Extract behavioural features from the authentication log and score each login with an Isolation Forest model, explained in natural language with graceful degradation.",
                "Deliver an administrative dashboard for user management, audit-log inspection, anomaly alerts, and analytics.",
            ]),
            ("sub", "1.4 Scope"),
            ("para",
             "The project delivers a working server, REST API, dashboard, test suite, "
             "and reproducible dataset. It focuses on the authentication server itself "
             "rather than a full identity provider; session issuance, OAuth/OIDC "
             "federation, and account-recovery workflows beyond backup codes are out "
             "of scope. The geographic signals used by the anomaly engine are supplied "
             "with each request rather than resolved from a commercial IP-geolocation "
             "service."),
            ("sub", "1.5 Limitations"),
            ("para",
             "The system uses a single server master key to encrypt all secrets rather "
             "than per-user keys behind a hardware security module; the push factor "
             "simulates the mobile device server-side; the CAPTCHA is a self-contained "
             "HMAC-signed challenge rather than a commercial service; and the admin "
             "interface is unauthenticated for demonstration. These limitations are "
             "discussed honestly in Section 9 and in the accompanying SECURITY_NOTES "
             "document."),
            ("sub", "1.6 Report Structure"),
            ("para",
             "Section 2 reviews related work and identifies the research gap. Section 3 "
             "presents the system design, including architecture, data flow, and a "
             "threat model. Section 4 details the implementation and the cryptographic "
             "algorithms. Section 5 analyses security through threat modelling and "
             "tested attack scenarios. Section 6 reports results and discusses "
             "limitations. Section 7 concludes and proposes future work, followed by "
             "references and appendices."),
        ],
    },
    {
        "number": "2",
        "title": "Literature Review",
        "blocks": [
            ("para",
             "This section critically reviews the standards and research that underpin "
             "the design, spanning one-time-password algorithms, password hashing, "
             "authenticated encryption, hardware authentication, and anomaly detection."),
            ("sub", "2.1 One-Time-Password Standards"),
            ("para",
             "M'Raihi et al. specified HOTP in RFC 4226 [1], defining an HMAC-SHA-1 "
             "construction with a dynamic truncation step that converts a 160-bit MAC "
             "into a short decimal code. RFC 6238 [2] extends this to a time-based "
             "variant by deriving the counter from the current time, and generalises "
             "the hash to the SHA-2 family. RFC 4648 [3] defines the Base32 encoding "
             "used to transport shared secrets to authenticator applications. These "
             "documents are the authoritative basis for our from-scratch "
             "implementation and its test vectors."),
            ("sub", "2.2 Password Hashing and Authenticated Encryption"),
            ("para",
             "Biryukov et al. introduced Argon2 [4], the Password Hashing Competition "
             "winner, whose Argon2id variant resists both GPU and side-channel attacks "
             "through memory-hard computation; we adopt it for password and backup-code "
             "hashing. For protecting secrets at rest we use AES in Galois/Counter Mode "
             "as standardised by NIST in SP 800-38D [5], an authenticated-encryption "
             "mode providing both confidentiality and integrity."),
            ("sub", "2.3 Hardware and Risk-Based Authentication"),
            ("para",
             "The W3C Web Authentication (WebAuthn) recommendation [6] and the FIDO2 "
             "framework define a public-key challenge-response protocol that is "
             "resistant to phishing because signatures are bound to the origin. NIST "
             "SP 800-63B [7] provides authoritative guidance on authenticator "
             "assurance levels and explicitly discourages SMS where stronger factors "
             "are available. Bonneau et al. [8] offer a comparative framework for "
             "evaluating authentication schemes against usability, deployability, and "
             "security criteria, motivating support for multiple factors."),
            ("sub", "2.4 Attacks on Second Factors"),
            ("para",
             "Not all second factors are equal. Lei et al. [11] document SIM-swap "
             "attacks in which an adversary ports a victim's phone number to seize "
             "SMS-delivered one-time codes, undermining SMS as a factor. More recently, "
             "multi-factor 'fatigue' or push-bombing attacks spam a victim with "
             "approval prompts until one is accepted; the industry response, "
             "number-matching and contextual prompts, informs our decision to show "
             "request context on the simulated push challenge. These findings reinforce "
             "the value of phishing-resistant WebAuthn and of an independent anomaly "
             "signal that does not rely on any single factor's integrity."),
            ("sub", "2.5 Anomaly Detection for Authentication"),
            ("para",
             "Liu, Ting, and Zhou proposed Isolation Forest [9], an unsupervised "
             "ensemble that isolates anomalies with few random partitions and scales "
             "to streaming data without labelled fraud examples, which suits the "
             "unlabelled nature of login telemetry. The 'impossible travel' heuristic, "
             "widely used in commercial identity platforms, flags logins whose implied "
             "travel velocity between consecutive locations exceeds physical limits; we "
             "implement it as one feature among several. Pedregosa et al. [10] describe "
             "scikit-learn, the toolkit used to train the model. Sommer and Paxson [12] "
             "caution that machine learning in security must contend with a high cost "
             "of false positives and a lack of ground truth, which motivates our "
             "conservative contamination setting and our decision to make every alert "
             "explainable rather than opaque."),
            ("sub", "2.6 Comparison and Research Gap"),
            ("table",
             "Comparison of related work and this project",
             ["Work", "Focus", "OTP from scratch", "Secrets encrypted", "Anomaly layer"],
             [
                 ["RFC 4226/6238 [1][2]", "OTP algorithms", "Specification", "Not addressed", "No"],
                 ["Argon2 [4]", "Password hashing", "N/A", "N/A", "No"],
                 ["WebAuthn/FIDO2 [6]", "Phishing-resistant factor", "N/A", "Keys on device", "No"],
                 ["NIST SP 800-63B [7]", "Assurance guidance", "N/A", "Recommended", "Risk-based advised"],
                 ["Isolation Forest [9]", "Anomaly detection", "N/A", "N/A", "Algorithm only"],
                 ["This project", "Integrated MFA server", "Yes", "AES-256-GCM", "Yes, explainable"],
             ]),
            ("para",
             "The literature provides strong individual building blocks but few openly "
             "documented systems combine from-scratch, test-validated OTP; encrypted "
             "secret storage; a full range of factors; and an explainable anomaly layer "
             "in one server. This project addresses that integration gap and "
             "emphasises verifiable correctness and honest limitation reporting."),
        ],
    },
    {
        "number": "3",
        "title": "System Design",
        "blocks": [
            ("sub", "3.1 Architecture Overview"),
            ("para",
             "The system is organised in layers. A Flask REST API exposes "
             "authentication and administration endpoints; a framework-agnostic "
             "service layer holds the business logic; a cryptographic core implements "
             "the OTP algorithms and the secret vault; and an AI layer extracts "
             "features and scores events. A Streamlit dashboard consumes the same "
             "service layer either over HTTP or, for single-container deployments, "
             "in-process. Figure 1 shows the overall architecture."),
            ("figure", "architecture.png", "System architecture and component layering"),
            ("para",
             "The design is guided by several established security principles. Defence "
             "in depth ensures that compromising one control does not compromise the "
             "system. Fail-safe defaults mean credentials are created disabled until "
             "possession is proven, and errors deny access rather than granting it. "
             "Least privilege is reflected in binding each encrypted secret to its "
             "owning user and factor. Complete mediation is achieved by funnelling "
             "every authentication attempt through a single logging choke-point, which "
             "guarantees the audit trail and the anomaly model never diverge from what "
             "actually happened."),
            ("sub", "3.2 Component Descriptions"),
            ("bullet", [
                "Crypto core: hand-written HOTP and TOTP, the AES-256-GCM secret vault, and Argon2id password hashing.",
                "Services: enrollment and verification for each factor, password login, push-challenge lifecycle, WebAuthn ceremonies, and lockout.",
                "Models: User, Credential, AuthEvent, BackupCode, and PushChallenge persisted via SQLAlchemy to SQLite.",
                "AI anomaly layer: feature extraction, per-user Isolation Forest scoring, and an LLM explainer with a deterministic fallback.",
                "Dashboard: administrative views for users, the audit log, anomaly alerts, analytics, and captured test evidence.",
            ]),
            ("sub", "3.3 Data Flow"),
            ("para",
             "A login request carries credentials, an optional one-time code, and "
             "contextual signals. The route delegates to a service, which verifies the "
             "relevant factor using the crypto core, writes an AuthEvent to the audit "
             "log, and triggers anomaly scoring. Figure 2 illustrates the flow."),
            ("figure", "dataflow.png", "Authentication request data flow"),
            ("sub", "3.4 Threat Model"),
            ("para",
             "We analysed the system using the STRIDE methodology, mapping each threat "
             "category to concrete mitigations implemented in the server, summarised in "
             "Figure 3 and Table 2."),
            ("figure", "threat_model.png", "STRIDE threat model and mitigations"),
            ("table",
             "Threat categories and mitigations",
             ["Threat", "Example", "Mitigation"],
             [
                 ["Spoofing", "Stolen password", "Additional factor required (TOTP/HOTP/WebAuthn/push)"],
                 ["Tampering", "Modify stored secret", "AES-256-GCM with associated data binding"],
                 ["Repudiation", "Deny a login", "Immutable AuthEvent audit trail"],
                 ["Info disclosure", "Read DB secrets", "Secrets encrypted at rest; Argon2id passwords"],
                 ["Denial of service", "Online guessing", "Sliding-window lockout + CAPTCHA"],
                 ["Elevation", "Replay a code", "Time-step replay prevention; WebAuthn sign count"],
             ]),
            ("sub", "3.5 Technology Stack"),
            ("table",
             "Technology stack and rationale",
             ["Layer", "Technology", "Rationale"],
             [
                 ["API", "Python 3.12, Flask", "Lightweight, well understood, easy to test"],
                 ["Data", "SQLAlchemy + SQLite", "Zero-configuration, portable for grading"],
                 ["Crypto", "stdlib hmac/hashlib, cryptography, argon2-cffi", "Standards-compliant primitives"],
                 ["WebAuthn", "py_webauthn", "Real attestation/assertion verification"],
                 ["AI", "scikit-learn, Anthropic Claude", "Unsupervised scoring + explanation"],
                 ["Dashboard", "Streamlit, Plotly", "Rapid, deployable UI for the demo"],
             ]),
            ("para",
             "The original brief suggested a React admin panel. We selected Streamlit "
             "instead to enable rapid development and one-click deployment to Streamlit "
             "Community Cloud, allowing the demonstration to run from any device. "
             "Functionally the dashboard meets the same requirement of user management "
             "and authentication-log analytics; the trade-off is less front-end "
             "customisation, which is acceptable for an internal administrative tool."),
            ("sub", "3.6 Deployment Model"),
            ("para",
             "The dashboard accesses data through an abstraction that supports two "
             "backends. In the HTTP backend it calls the Flask API over the network, "
             "matching a production topology where the API and the UI are separate "
             "services. In the embedded backend it imports the service layer and runs "
             "queries in-process, which allows the entire system to be demonstrated "
             "from a single Streamlit Community Cloud container without a separately "
             "reachable API. Configuration is driven entirely by environment variables "
             "and secrets, so no code changes are needed to switch modes."),
            ("sub", "3.7 Data Model"),
            ("para",
             "Five entities capture the domain. User holds the account and lockout "
             "state; Credential stores one enrolled factor each, including the "
             "encrypted OTP secret or the WebAuthn public key; AuthEvent is the audit "
             "record and the anomaly-engine training source; BackupCode stores hashed "
             "single-use recovery codes; and PushChallenge tracks the lifecycle of a "
             "push approval. All are persisted through SQLAlchemy, allowing the same "
             "models to back both SQLite in development and a hosted database in "
             "deployment."),
        ],
    },
    {
        "number": "4",
        "title": "Implementation",
        "blocks": [
            ("sub", "4.1 HOTP (RFC 4226)"),
            ("para",
             "HOTP computes an HMAC over an 8-byte big-endian counter and applies "
             "dynamic truncation to obtain a decimal code, as in Equation (1)."),
            ("equation", "HOTP(K, C) = Truncate(HMAC-SHA-1(K, C)) mod 10^d"),
            ("para",
             "Dynamic truncation reads the low four bits of the final MAC byte as an "
             "offset, extracts the following four bytes, masks the most-significant bit "
             "to avoid sign ambiguity, and reduces modulo a power of ten. The core of "
             "our implementation is shown in Listing 1."),
            ("code", "Dynamic truncation (backend/crypto/hotp.py)",
             "offset = hmac_digest[-1] & 0x0F\n"
             "binary = ((hmac_digest[offset] & 0x7F) << 24)\n"
             "       | ((hmac_digest[offset + 1] & 0xFF) << 16)\n"
             "       | ((hmac_digest[offset + 2] & 0xFF) << 8)\n"
             "       | (hmac_digest[offset + 3] & 0xFF)\n"
             "return binary % (10 ** digits)"),
            ("sub", "4.2 TOTP (RFC 6238)"),
            ("para",
             "TOTP derives the HOTP counter from the current time using a step size X "
             "(default 30 seconds) and an epoch offset T0, as in Equation (2), and then "
             "applies HOTP. Our implementation supports SHA-1, SHA-256, and SHA-512 and "
             "a configurable digit count, and records the last accepted time step to "
             "prevent replay within the validity window."),
            ("equation", "T = floor((CurrentUnixTime - T0) / X)"),
            ("para",
             "The verifier accepts codes from a small window of neighbouring time "
             "steps to tolerate clock skew, using a constant-time comparison to avoid "
             "timing side channels, as shown in Listing 2."),
            ("code", "TOTP verification with drift window (backend/crypto/totp.py)",
             "base_counter = _counter_for_time(for_time, step, t0)\n"
             "for offset in range(-valid_window, valid_window + 1):\n"
             "    counter = base_counter + offset\n"
             "    if counter < 0:\n"
             "        continue\n"
             "    candidate = hotp.generate(secret, counter, digits, algorithm)\n"
             "    if secrets.compare_digest(candidate, code):\n"
             "        return True\n"
             "return False"),
            ("sub", "4.3 Secret Vault"),
            ("para",
             "Shared secrets are sealed with AES-256-GCM using a key derived from the "
             "server master key via HKDF-SHA256. A fresh 96-bit nonce is generated per "
             "encryption and prepended to the ciphertext, and the user and factor are "
             "bound as associated data so a secret cannot be transplanted between "
             "accounts. Passwords and backup codes are hashed with Argon2id. Listing 3 "
             "shows the sealing routine."),
            ("code", "AES-256-GCM sealing (backend/crypto/vault.py)",
             "aes_key = _derive_aes_key(_master_key())   # HKDF-SHA256\n"
             "aesgcm = AESGCM(aes_key)\n"
             "nonce = os.urandom(12)                      # 96-bit nonce\n"
             "sealed = aesgcm.encrypt(nonce, plaintext, associated_data)\n"
             "return nonce + sealed                       # nonce || ct || tag"),
            ("para",
             "Because GCM is an authenticated mode, any tampering with the stored "
             "ciphertext, nonce, or associated data causes decryption to fail with an "
             "integrity error rather than returning corrupted plaintext, which is "
             "verified by the vault unit tests."),
            ("sub", "4.4 Additional Factors"),
            ("para",
             "HOTP verification accepts a small look-ahead window for counter "
             "resynchronisation. The push factor creates a pending challenge with a "
             "time-to-live that a mock device approves or denies while the login polls "
             "for the result. WebAuthn registration and authentication are verified "
             "server-side by the py_webauthn library, including challenge binding, "
             "origin checks, and signature-counter regression detection."),
            ("para",
             "The WebAuthn flow merits emphasis because it is the one factor whose "
             "security depends on real public-key cryptography rather than a shared "
             "secret. During registration the server issues a random challenge and "
             "verifies the authenticator's attestation response before storing the "
             "credential's public key and initial signature counter. During "
             "authentication it issues a fresh challenge and verifies the returned "
             "assertion signature against that public key; it then checks that the "
             "authenticator's signature counter has advanced, which detects cloned "
             "credentials. Because the assertion is bound to the relying-party origin, "
             "a phishing site on a different origin cannot produce a valid response, "
             "giving WebAuthn its phishing resistance. The negative paths, an assertion "
             "with no outstanding challenge and a tampered signature, are covered by "
             "automated tests."),
            ("para",
             "Backup codes provide a recovery factor. The server generates a set of "
             "random single-use codes, displays them to the user exactly once, and "
             "stores only their Argon2id hashes; redeeming a code marks it used so it "
             "cannot be replayed."),
            ("para",
             "Failure handling for brute-force protection counts recent failures over "
             "a sliding window per user and per source IP and trips a lockout once the "
             "threshold is reached, as in Listing 4."),
            ("code", "Lockout decision (backend/services/lockout.py)",
             "effective = max(failures, ip_failures)\n"
             "if effective >= config.lockout_max_failures:\n"
             "    user.locked_until = _utcnow() + timedelta(\n"
             "        seconds=config.lockout_duration_seconds)\n"
             "    session.commit()\n"
             "    locked = True"),
            ("sub", "4.5 AI Anomaly Layer"),
            ("para",
             "For each scored event the system extracts geographic distance from the "
             "previous login, the implied travel velocity and an impossible-travel "
             "flag, a new-device indicator, an unusual-hour indicator, and a recent "
             "failed-attempt burst count. An Isolation Forest trained on the user's "
             "history scores the event; with insufficient history a deterministic "
             "rule-based fallback is used. Flagged events are explained by a "
             "large-language model, and if the model is unavailable the system shows a "
             "deterministic feature summary instead."),
            ("para",
             "The impossible-travel feature compares the current login location with "
             "the most recent successful login and computes the implied velocity using "
             "the haversine great-circle distance; a velocity above a plausible "
             "air-travel speed sets the flag. Crucially, when building the training "
             "matrix, each historical event is featurised against only its own prior "
             "events, preventing future information from leaking into past samples."),
            ("para",
             "The explainer demonstrates graceful degradation explicitly: when the API "
             "key is absent or any error occurs, it returns a deterministic summary "
             "rather than failing, as shown in Listing 5."),
            ("code", "Graceful degradation in the explainer (backend/services/anomaly/explainer.py)",
             "if not config.anthropic_api_key:\n"
             "    return None, fallback           # no network call attempted\n"
             "try:\n"
             "    ...                              # call Claude, return prose\n"
             "except Exception:                    # any failure -> degrade\n"
             "    return None, fallback            # show raw feature summary"),
            ("sub", "4.6 Enrollment and QR Provisioning"),
            ("para",
             "TOTP enrollment generates a random Base32 secret, stores it encrypted, "
             "and returns an otpauth:// provisioning URI rendered as a base64 PNG QR "
             "code. The credential is enabled only after the user verifies a first code, "
             "confirming possession."),
            ("sub", "4.7 REST API Design"),
            ("para",
             "The API is organised into Flask blueprints by concern: authentication, "
             "MFA enrollment and verification, push, WebAuthn, and administration. "
             "Endpoints accept and return JSON, and a shared decorator provides each "
             "request with a database session that is reliably cleaned up afterwards. "
             "Failures return consistent JSON error objects with appropriate HTTP "
             "status codes, including 423 for a locked account and 428 when a CAPTCHA "
             "is required, so clients can react programmatically. Cross-origin requests "
             "are permitted so the dashboard, served from a different origin, can call "
             "the API directly."),
            ("sub", "4.8 Development Methodology and Tooling"),
            ("para",
             "Development followed an incremental, test-driven approach: each "
             "cryptographic primitive was implemented and validated against its "
             "specification before the surrounding service and route were added. The "
             "code is organised into a framework-agnostic service layer so that the "
             "same logic is exercised by both the REST API and the dashboard, and so "
             "that unit tests can target the services directly without spinning up a "
             "web server. Continuous validation is provided by a pytest suite and a "
             "capture script that records the verbatim test output as submission "
             "evidence, ensuring no result is hand-edited."),
        ],
    },
    {
        "number": "5",
        "title": "Security Analysis",
        "blocks": [
            ("para",
             "Security was evaluated by mapping threats to mitigations and by writing "
             "automated tests that execute concrete attack scenarios against the "
             "running server. Table 4 lists the scenarios and outcomes."),
            ("table",
             "Tested attack scenarios and results",
             ["Scenario", "Attack", "Expected", "Result"],
             [
                 ["Replay", "Reuse a valid TOTP code", "Second use rejected", "PASS"],
                 ["Brute force", "Repeated wrong passwords", "Account locked + CAPTCHA", "PASS"],
                 ["Secret at rest", "Read DB bytes directly", "No plaintext secret", "PASS"],
                 ["WebAuthn tamper", "Forge/alter assertion", "Authentication denied", "PASS"],
             ]),
            ("sub", "5.1 Replay Resistance"),
            ("para",
             "Because a TOTP code is valid for a whole time step, a naive verifier "
             "accepts the same code multiple times within that window. The server "
             "records the last accepted time step per credential and rejects any code "
             "at or below it, defeating replay while still tolerating clock drift."),
            ("sub", "5.2 Brute-Force Resistance"),
            ("para",
             "Failed attempts are counted over a sliding window per user and per source "
             "IP. A CAPTCHA is required once failures reach half the threshold, and the "
             "account is locked once the threshold is reached, returning a clear status "
             "to the client."),
            ("sub", "5.3 Confidentiality at Rest"),
            ("para",
             "A dedicated test reads the raw credential bytes from the database and "
             "asserts the plaintext secret does not appear, confirming that only "
             "AES-256-GCM ciphertext is stored."),
            ("sub", "5.4 Phishing Resistance and Defence in Depth"),
            ("para",
             "The design follows defence in depth: even if one control fails, others "
             "remain. A phished password is insufficient without a second factor; a "
             "stolen database yields only Argon2id hashes and AES-GCM ciphertext; a "
             "captured one-time code cannot be replayed; and a relocated or unusual "
             "login is flagged for review regardless of which factor was used. WebAuthn "
             "specifically resists real-time phishing because its signatures are bound "
             "to the origin, so credentials presented to a look-alike domain are "
             "rejected by construction."),
            ("sub", "5.5 Residual Risks"),
            ("para",
             "Residual risks remain and are stated honestly. The single master key is a "
             "concentrated point of failure; the simulated push and CAPTCHA would be "
             "replaced by hardened services in production; the admin interface is "
             "unauthenticated for the demonstration; and the anomaly model, like any "
             "detector, can produce false positives and false negatives. These are "
             "discussed further in Section 6 and in the accompanying security notes."),
            ("sub", "5.6 Comparison with Baseline Tools"),
            ("table",
             "Comparison with common authenticator tools",
             ["Capability", "Google Authenticator", "Authy", "Duo", "This project"],
             [
                 ["TOTP/HOTP", "Yes", "Yes", "Yes", "Yes (from scratch)"],
                 ["WebAuthn", "Limited", "Limited", "Yes", "Yes"],
                 ["Push approval", "No", "No", "Yes", "Yes (simulated)"],
                 ["Server-side anomaly AI", "No", "No", "Partial", "Yes, explainable"],
                 ["Open, inspectable code", "No", "No", "No", "Yes"],
             ]),
        ],
    },
    {
        "number": "6",
        "title": "Results and Discussion",
        "blocks": [
            ("para",
             "The implementation passes its full automated test suite, including the "
             "RFC 4226 and RFC 6238 published test vectors across all supported hash "
             "algorithms and an independent cross-validation oracle. The security "
             "scenarios in Section 5 all pass. The figures below are generated directly "
             "from the seeded dataset and therefore reflect real system output."),
            ("sub", "6.1 Test Coverage Summary"),
            ("para",
             "The suite comprises thirty-two automated tests grouped by concern. Table "
             "6 summarises them; the raw captured output is reproduced in Appendix C."),
            ("table",
             "Automated test coverage by category",
             ["Category", "Tests", "What it verifies"],
             [
                 ["RFC 4226 vectors", "4", "HOTP matches the published Appendix D values"],
                 ["RFC 6238 vectors", "8", "TOTP matches Appendix B for SHA1/256/512"],
                 ["pyotp oracle", "3", "Codes match an independent implementation"],
                 ["Secret vault", "5", "Round-trip, nonce uniqueness, tamper, AAD binding"],
                 ["Security suite", "5", "Replay, lockout, secret-at-rest, WebAuthn tamper"],
                 ["Anomaly layer", "5", "Feature extraction, scoring, LLM fallback"],
                 ["API flow", "2", "Register/login/enroll/verify over HTTP"],
             ]),
            ("sub", "6.2 Performance"),
            ("para",
             "One-time-password generation is computationally trivial: it performs a "
             "single HMAC over an eight-byte counter, completing in well under a "
             "millisecond on commodity hardware, so OTP verification adds negligible "
             "latency to a login. The dominant cost in the password path is Argon2id "
             "hashing, which is intentionally expensive to resist offline cracking; its "
             "parameters can be tuned to the deployment's latency budget. Anomaly "
             "scoring fits a small Isolation Forest per request, which is inexpensive at "
             "the per-user history sizes encountered here."),
            ("figure", "attempts_over_time.png", "MFA attempts over time"),
            ("figure", "success_fail_ratio.png", "Success versus failure ratio"),
            ("figure", "attempts_by_factor.png", "Authentication attempts by factor"),
            ("figure", "anomaly_scores.png", "Anomaly-score distribution with flagged events"),
            ("figure", "login_map.png", "Login locations with flagged events highlighted"),
            ("sub", "6.3 Discussion"),
            ("para",
             "The anomaly layer correctly isolates the injected impossible-travel and "
             "failed-burst events from routine logins, and the explainer produces a "
             "readable justification or, when the language model is unavailable, a "
             "deterministic feature summary. The from-scratch OTP implementation "
             "matches the reference oracle exactly, demonstrating specification "
             "fidelity rather than reliance on a library."),
            ("para",
             "The charts in this section are produced directly from the seeded audit "
             "log. The attempts-over-time line shows the routine daily login rhythm "
             "against which anomalies stand out; the success/failure ratio reflects the "
             "injected failed-attempt bursts; the by-factor bar shows the distribution "
             "of authentication methods exercised; and the anomaly-score histogram "
             "separates the small cluster of flagged outliers from the dense mass of "
             "normal logins. The login map makes the geographic anomalies visually "
             "obvious, plotting the impossible-travel logins far from each user's usual "
             "location. Together these views give an administrator an at-a-glance "
             "understanding of authentication health without reading raw logs."),
            ("para",
             "A noteworthy implementation lesson concerned data leakage in the anomaly "
             "pipeline. An early version featurised each historical event against the "
             "user's entire history, including events that occurred afterwards, which "
             "inflated the apparent velocity between logins and produced spurious "
             "flags. Constraining each training sample to its own prior events resolved "
             "the issue and reduced the false-positive rate to the expected level, "
             "underscoring how temporal correctness matters as much as model choice."),
            ("sub", "6.4 Limitations"),
            ("para",
             "A single master key protects all secrets; the push factor and CAPTCHA are "
             "simulated; the WebAuthn challenge store is in-memory; and the admin "
             "interface is unauthenticated for the demonstration. The anomaly model is "
             "retrained per request on modest per-user histories rather than persisted, "
             "which is adequate at this scale but would be revisited for production "
             "volumes."),
        ],
    },
    {
        "number": "7",
        "title": "Conclusion",
        "blocks": [
            ("para",
             "This project delivered a complete multi-factor authentication server that "
             "meets all stated objectives: HOTP and TOTP were implemented from their "
             "RFCs and validated against the published vectors and an oracle; secrets "
             "are encrypted at rest and passwords hashed with Argon2id; TOTP, HOTP, "
             "WebAuthn, push, and backup codes are supported; brute-force protection "
             "and CAPTCHA are in place; and an explainable Isolation Forest anomaly "
             "layer scores every login and is surfaced through an administrative "
             "dashboard."),
            ("para",
             "Beyond meeting the functional requirements, the project demonstrates that "
             "a security system can be both rigorous and transparent: the cryptography "
             "is verified against authoritative test vectors rather than trusted "
             "blindly, and the AI layer explains its decisions rather than acting as an "
             "opaque oracle. This combination of verifiable correctness and "
             "explainability is increasingly expected of real-world security tooling "
             "and is, in our view, the project's most valuable contribution."),
            ("sub", "7.1 Lessons Learned"),
            ("para",
             "Implementing the OTP algorithms directly clarified subtle details such as "
             "dynamic truncation and counter encoding that a library hides. Designing "
             "the anomaly engine highlighted the importance of scoring events against "
             "correctly time-ordered history to avoid information leakage, and of "
             "graceful degradation when an external service is unavailable."),
            ("sub", "7.2 Future Work"),
            ("numbered", [
                "Replace the single master key with envelope encryption backed by a KMS or HSM, with key rotation.",
                "Deliver push challenges to a real registered mobile application instead of a simulated device.",
                "Add authenticated, role-based access control to the administrative API and dashboard.",
                "Persist per-user anomaly models and incorporate additional features such as ASN and user-agent entropy.",
                "Integrate a production CAPTCHA provider and per-IP global rate limiting at the edge.",
            ]),
        ],
    },
]

# ---------------------------------------------------------------------------
# References (IEEE format, 10 entries; no Wikipedia).
# ---------------------------------------------------------------------------
REFERENCES = [
    "D. M'Raihi, M. Bellare, F. Hoornaert, D. Naccache, and O. Ranen, \"HOTP: An HMAC-Based One-Time Password Algorithm,\" RFC 4226, IETF, Dec. 2005.",
    "D. M'Raihi, S. Machani, M. Pei, and J. Rydell, \"TOTP: Time-Based One-Time Password Algorithm,\" RFC 6238, IETF, May 2011.",
    "S. Josefsson, \"The Base16, Base32, and Base64 Data Encodings,\" RFC 4648, IETF, Oct. 2006.",
    "A. Biryukov, D. Dinu, and D. Khovratovich, \"Argon2: New Generation of Memory-Hard Functions for Password Hashing and Other Applications,\" in Proc. IEEE European Symp. Security and Privacy (EuroS&P), 2016, pp. 292-302.",
    "M. Dworkin, \"Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC,\" NIST Special Publication 800-38D, Nov. 2007.",
    "W3C, \"Web Authentication: An API for Accessing Public Key Credentials Level 2,\" W3C Recommendation, Apr. 2021.",
    "P. A. Grassi et al., \"Digital Identity Guidelines: Authentication and Lifecycle Management,\" NIST Special Publication 800-63B, Jun. 2017.",
    "J. Bonneau, C. Herley, P. C. van Oorschot, and F. Stajano, \"The Quest to Replace Passwords: A Framework for Comparative Evaluation of Web Authentication Schemes,\" in Proc. IEEE Symp. Security and Privacy, 2012, pp. 553-567.",
    "F. T. Liu, K. M. Ting, and Z.-H. Zhou, \"Isolation Forest,\" in Proc. 8th IEEE Int. Conf. Data Mining (ICDM), 2008, pp. 413-422.",
    "F. Pedregosa et al., \"Scikit-learn: Machine Learning in Python,\" Journal of Machine Learning Research, vol. 12, pp. 2825-2830, 2011.",
    "K. Lee, B. Kaiser, J. Mayer, and A. Narayanan, \"An Empirical Study of Wireless Carrier Authentication for SIM Swaps,\" in Proc. Symp. Usable Privacy and Security (SOUPS), 2020, pp. 61-79.",
    "R. Sommer and V. Paxson, \"Outside the Closed World: On Using Machine Learning for Network Intrusion Detection,\" in Proc. IEEE Symp. Security and Privacy, 2010, pp. 305-316.",
]

# ---------------------------------------------------------------------------
# Appendices.
# ---------------------------------------------------------------------------
APPENDICES = [
    {
        "title": "Appendix A: Source Code and Repository",
        "blocks": [
            ("para",
             "The complete source code is available in the project repository. Replace "
             "the placeholder below with the actual link before submission."),
            ("para", "GitHub repository: [INSERT GITHUB REPOSITORY LINK HERE]"),
            ("sub", "Repository structure"),
            ("code", "Project layout",
             "backend/      Flask API, models, crypto, services, routes\n"
             "dashboard/    Streamlit admin dashboard\n"
             "scripts/      seed, dataset export, figures, report, test capture\n"
             "tests/        unit, oracle, security, RFC vectors\n"
             "docs/         figures, user manual, demo script, report"),
        ],
    },
    {
        "title": "Appendix B: User Manual",
        "blocks": [
            ("para",
             "A full setup, run, and test guide is provided in README.md and "
             "docs/USER_MANUAL.md. In brief: create a virtual environment, install "
             "requirements, set a master key, seed demo data, start the Flask API, and "
             "launch the Streamlit dashboard."),
        ],
    },
    {
        "title": "Appendix C: Test Evidence",
        "blocks": [
            ("para",
             "Raw, unedited test output is captured by scripts/capture_test_results.py "
             "into the test_evidence/ directory. The latest captured summary is "
             "reproduced below; it is generated by the test run, not authored by hand."),
            ("evidence",),  # builder substitutes the latest evidence file content
        ],
    },
]
