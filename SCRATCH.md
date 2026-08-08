

infer the variable header type

```python
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Infer the runtime variable-header class from the generic packet type."""
        super().__init_subclass__(**kwargs)
        if "VARIABLE_HEADER" in cls.__dict__:
            return

        for base in getattr(cls, "__orig_bases__", ()):
            if get_origin(base) is not AcknowledgementPacket:
                continue
            variable_header = get_args(base)[0]
            if isinstance(variable_header, type) and issubclass(variable_header, AcknowledgementVariableHeader):
                cls.VARIABLE_HEADER = cast("type[_AckVariableHeader]", variable_header)
                return

        msg = f"{cls.__name__} must specify AcknowledgementPacket[VariableHeader] or define VARIABLE_HEADER"
        raise TypeError(msg)
```


in `test_db_plugin.py`
- remove `passlib`
- add `pip install "pwdlib[argon2]"`
- replace this:
    pwd_hasher.crypt_context = CryptContext(schemes=["argon2", ], deprecated="auto")
with
```python
from pwdlib import PasswordHash

# Initialize the modern replacement
pwd_hasher = PasswordHash.recommended()

# To use specifically with Argon2 only:
# pwd_hasher = PasswordHash(backends=["argon2"])

# Hashing a password
hashed_password = pwd_hasher.hash("secret_password")

# Verifying a password (and checking if it needs an upgrade)
is_valid, new_hash = pwd_hasher.verify_and_update("secret_password", hashed_password)
if is_valid and new_hash:
    # Update the hash in your database
    pass
```

------

update `pytest` to 'v9' (from 8.x)

  /Users/andrew/dev/amqtt-ghsa-2hjf-7455-w946/.venv/lib/python3.13/site-packages/_hypothesis_pytestplugin.py:442: PytestRemovedIn9Warning: Marks applied to fixtures have no effect
  See docs: https://docs.pytest.org/en/stable/deprecations.html#applying-a-mark-to-a-fixture-function
    return _orig_call(self, function)


-----

make sure all warnings.warn are marked as 'deprecation'

  /Users/andrew/dev/amqtt-ghsa-2hjf-7455-w946/amqtt/plugins/persistence.py:11: UserWarning: SQLitePlugin is deprecated, use amqtt.contrib.persistence.SessionDBPlugin

  /Users/andrew/dev/amqtt-ghsa-2hjf-7455-w946/amqtt/plugins/topic_checking.py:33: UserWarning: The 'acl' option is deprecated, please use 'subscribe-acl' instead.

-----

PGP key guidance for SECURITY.md

Providing a PGP key means publishing an OpenPGP public key so reporters can
encrypt vulnerability emails to the project. It also means the maintainers must
safely manage the matching private key, because only that private key can
decrypt those reports.

Operational requirements:
- Create an OpenPGP/GPG key for the reporting address, such as support@amqtt.io.
- Publish the public key or a link to it in SECURITY.md, plus its fingerprint.
- Keep the private key encrypted, backed up, and limited to maintainers who need
  to read security reports.
- Generate and safely store a revocation certificate so the key can be revoked
  if it is lost or compromised.
- Decide rotation and expiration policy, and update SECURITY.md when the key
  changes.
- Test that an external reporter can encrypt to the key and that maintainers can
  decrypt the message.

Main tradeoff: if the project advertises PGP, maintainers need to reliably
monitor and decrypt encrypted reports. Otherwise, PGP can make reporting harder.
GitHub Security Advisories already provide a private channel, so PGP is useful
but not required.

Suggested SECURITY.md wording if PGP is added later:

```markdown
For encrypted email, use the OpenPGP key for support@amqtt.io:

Fingerprint: XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX
Public key: https://amqtt.io/security.asc
```

-----

Security advisory coordination response

Coordination means keeping aMQTT, the reporter, GitHub/GHSA, and any
third-party vulnerability database aligned on the same issue before anything
becomes public.

Practically, that means agreeing on:
- whether the issue is valid
- affected versions and fixed versions
- whether a CVE is needed
- whether a CVE/GHSA/CNVD ID already exists
- who is submitting to which database
- whether the third-party submission stays private or creates public disclosure
- the disclosure date and advisory text

Response if someone asks to submit a report to CNVD:

```text
Thanks for asking. Please do not submit this vulnerability to CNVD independently
while it is being handled through the aMQTT GitHub Security Advisory process.

Because we use GitHub Security Advisories as the private reporting channel and
GitHub is a CVE Numbering Authority, we need to coordinate CVE/CNVD tracking
there first to avoid duplicate or conflicting records and premature disclosure.

Please add the CNVD request details to the GitHub Security Advisory, including
whether you have already submitted anything, any tracking IDs, and whether CNVD
can keep the report private until a fix or mitigation is available. Once we have
triaged the issue, we can agree on the appropriate submission path and disclosure
timing.
```

Key stance: not "never CNVD," but "not separately or publicly before we
coordinate."





<br/>- yaml-based configuration, as standard.

<br/>- EOL of inconsistent and project-based plugin configuration options (deprecated in `0.11.2)` in favor of yaml config)



??? warning "`pbkdf2_sha256` and `scrypt` hashing schemes are deprecated, replaced by `argon2`  (v0.12.0)"


    Due to the removal of Python's standard library `crypt` module in Python 3.13 and the no-longer-supported `passlib` library, `pbkdf2_sha256` and `scrypt` have been deprecated, in favor of `argon2` or `bcrypt`.

    Deprecation include updating the password hash to `argon2` upon successfully verifying a password encrypted with `pbkdf2_sha256` or `scrypt`. As all hashes are one-way, it _cannot_ do a full migration of all passwords; only the passwords that are verified, where the original password is provided, can be hashed with the new scheme.   
