

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
