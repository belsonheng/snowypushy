import hvac
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

class Vault(object):
    def open(self, **kwargs):
        try:
            # Connect to Keeper to collect secrets
            client = hvac.Client(url=kwargs["keeper_url"], namespace=kwargs["keeper_ns"], token=kwargs["keeper_token"])
            password = client.read(kwargs["keeper_password_path"])["data"]["passwd"]
            passphrase = client.read(kwargs["keeper_secret_path"])["data"]["SNOWSQL_PRIVATE_KEY_PASSPHRASE"]
            private_key = client.read(kwargs["keeper_secret_path"])["data"]["private_key"]
            key = serialization.load_pem_private_key(
                bytes(private_key, "utf-8"),
                password = passphrase.encode(),
                backend = default_backend()).private_bytes(
                encoding = serialization.Encoding.DER,
                format = serialization.PrivateFormat.PKCS8,
                encryption_algorithm = serialization.NoEncryption()
            )
            return {"password": password, "private_key": key}
        except Exception as err:
            print("Unable to open keeper vault:")
            sys.exit(err)
