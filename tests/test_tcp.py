from unittest.mock import patch
from checks.tcp import check_tcp
from checks import OK, DOWN
import socket


def test_tcp_success():
    with patch("checks.tcp.socket.create_connection") as mock_connection:
        result = check_tcp("node-01", "127.0.0.1", 8801, 3)
        assert result.state == OK
        assert result.target == "node-01"
        assert result.check == "tcp"
        mock_connection.assert_called_once_with(
            ("127.0.0.1", 8801),
            timeout=3
        )


def test_tcp_connection_refused():

    with patch(
        "checks.tcp.socket.create_connection",
        side_effect=ConnectionRefusedError("Connection refused")
    ):
        result = check_tcp("node-04", "127.0.0.1", 8804, 3)

    assert result.state == DOWN
    assert "refused" in result.detail.lower()


def test_tcp_dns_failure():
    with patch(
            "checks.tcp.socket.create_connection",
            side_effect=socket.gaierror("Name or service not known")
    ):
        result = check_tcp("node-05", "fleet-node-05.invalid", 8801, 3)
        assert result.state == DOWN


def test_tcp_network_error():
    with patch(
        "checks.tcp.socket.create_connection",
        side_effect=OSError("Network unreachable")
    ):
        result = check_tcp("node-test", "127.0.0.1", 9999, 3)

    assert result.state == DOWN
    assert "network" in result.detail.lower()


