import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, sentinel

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from .database import database_config


class DatabaseConfigTests(SimpleTestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.auth = self.base / "credentials" / "oracle"
        self.wallet = self.auth / "wallet"
        self.wallet.mkdir(parents=True)
        self.values = {"user": "test_user", "password": "test_password", "dsn": "test_low", "wallet_password": "test_wallet_password"}

    def configure(self):
        (self.auth / "connection.json").write_text(json.dumps(self.values))
        for filename in ("tnsnames.ora", "ewallet.pem"):
            (self.wallet / filename).touch()

    def test_without_credentials_keeps_local_demo(self):
        self.assertEqual(database_config(self.base, {})["ENGINE"], "django.db.backends.sqlite3")

    def test_oracle_required_without_credentials_fails(self):
        with self.assertRaises(ImproperlyConfigured):
            database_config(self.base, {"DATABASE_BACKEND": "oracle"})

    def test_complete_credentials_select_oracle_and_driver_receives_wallet(self):
        from django.db.backends.oracle.base import DatabaseWrapper

        self.configure()
        settings = database_config(self.base, {})
        self.assertEqual(settings["ENGINE"], "django.db.backends.oracle")
        wrapper = DatabaseWrapper(settings)
        with patch("django.db.backends.oracle.base.Database.connect", return_value=sentinel.connection) as connect:
            self.assertIs(wrapper.get_new_connection(wrapper.get_connection_params()), sentinel.connection)
        connect.assert_called_once_with(
            user="test_user", password="test_password", dsn="test_low",
            config_dir=str(self.wallet), wallet_location=str(self.wallet),
            wallet_password="test_wallet_password", ssl_server_dn_match=True,
        )

    def test_partial_credentials_fail_instead_of_falling_back(self):
        for key in self.values:
            with self.subTest(key=key):
                data = {**self.values, key: ""}
                (self.auth / "connection.json").write_text(json.dumps(data))
                with self.assertRaises(ImproperlyConfigured):
                    database_config(self.base, {})

    def test_corrupt_config_error_does_not_disclose_secrets(self):
        (self.auth / "connection.json").write_text('{"password": "do-not-expose"')
        with self.assertRaises(ImproperlyConfigured) as error:
            database_config(self.base, {})
        self.assertNotIn("do-not-expose", str(error.exception))
        (self.auth / "connection.json").write_text("[]")
        with self.assertRaises(ImproperlyConfigured):
            database_config(self.base, {})

    def test_missing_wallet_files_fail(self):
        for filename in ("tnsnames.ora", "ewallet.pem"):
            with self.subTest(filename=filename):
                self.configure()
                (self.wallet / filename).unlink()
                with self.assertRaisesMessage(ImproperlyConfigured, filename):
                    database_config(self.base, {})

    def test_explicit_sqlite_for_local_tests(self):
        self.configure()
        self.assertEqual(database_config(self.base, {"DATABASE_BACKEND": "sqlite"})["ENGINE"], "django.db.backends.sqlite3")

    def test_unknown_backend_fails(self):
        with self.assertRaises(ImproperlyConfigured):
            database_config(self.base, {"DATABASE_BACKEND": "typo"})
