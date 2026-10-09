"""Offline smoke: forbid outbound network creation while exercising core work."""
from pathlib import Path
from contextlib import closing
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import socket
from localquote.storage.db import open_db
from localquote import service

class OfflineTest(TestCase):
    def test_no_socket_calls(self):
        with TemporaryDirectory() as folder, patch.object(socket,"create_connection",side_effect=AssertionError("network forbidden")):
            with closing(open_db(Path(folder)/"offline.db")) as conn:
                c=service.create_customer(conn,"Yerel")
                q=service.create_quote(conn,c)
                service.add_line(conn,q,None,"Kurulum","1","100.00")
                service.approve_quote(conn,q)
                self.assertEqual(service.quote_detail(conn,q)["totals"]["total_cents"],12000)
