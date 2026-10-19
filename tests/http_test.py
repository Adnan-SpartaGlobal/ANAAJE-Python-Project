import pytest
import requests

from checks.__init__ import DEGRADED, DOWN, OK
from checks.http import CHECK_NAME, check_http

NAME = "node-8801"
URL = "http://localhost:8801/health"
TIMEOUT = 2.5


# ---------------------------------------------------------------------------
# Helpers: a fake response and fake versions of requests.get.
# monkeypatch (built into pytest, like tmp_path) swaps requests.get for the
# duration of one test, so no real network call is ever made.
# ---------------------------------------------------------------------------

class FakeResponse:
    def __init__(self, status_code=200, body=None, text="", json_error=None):
        self.status_code = status_code
        self.text = text
        self._body = body
        self._json_error = json_error

    def json(self):
        if self._json_error is not None:
            raise self._json_error
        return self._body


def returns(response):
    """Make requests.get return this response."""
    def fake_get(url, timeout):
        return response
    return fake_get


def raises(error):
    """Make requests.get raise this error."""
    def fake_get(url, timeout):
        raise error
    return fake_get


# ---------------------------------------------------------------------------
# OK
# ---------------------------------------------------------------------------

def test_200_with_status_ok_is_ok(monkeypatch):
    # Arrange
    monkeypatch.setattr(requests, "get", returns(FakeResponse(200, body={"status": "ok"})))

    # Act
    result = check_http(NAME, URL, TIMEOUT)

    # Assert
    assert result.state == OK
    assert "200" in result.detail


def test_ok_puts_parsed_body_in_extra_payload(monkeypatch):
    body = {"status": "ok", "disk": {"used": 40}}
    monkeypatch.setattr(requests, "get", returns(FakeResponse(200, body=body)))

    result = check_http(NAME, URL, TIMEOUT)

    assert result.extra == {"payload": body}


def test_timeout_is_passed_to_requests_get(monkeypatch):
    # requests has no default timeout, so check_http must always pass one.
    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return FakeResponse(200, body={"status": "ok"})

    monkeypatch.setattr(requests, "get", fake_get)

    check_http(NAME, URL, TIMEOUT)

    assert calls == [(URL, TIMEOUT)]


# ---------------------------------------------------------------------------
# DEGRADED: we reached it, but it is unwell
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("status_code", [201, 204, 301, 400, 404, 500, 502, 503])
def test_any_non_200_is_degraded(monkeypatch, status_code):
    monkeypatch.setattr(requests, "get", returns(FakeResponse(status_code, text="nope")))

    result = check_http(NAME, URL, TIMEOUT)

    assert result.state == DEGRADED
    assert str(status_code) in result.detail


def test_non_200_puts_response_body_in_detail(monkeypatch):
    response = FakeResponse(500, text="database connection pool exhausted")
    monkeypatch.setattr(requests, "get", returns(response))

    result = check_http(NAME, URL, TIMEOUT)

    assert result.detail == "HTTP 500, database connection pool exhausted"


@pytest.mark.parametrize("text", ["", "   \n  "])
def test_non_200_with_empty_body_uses_fallback(monkeypatch, text):
    monkeypatch.setattr(requests, "get", returns(FakeResponse(503, text=text)))

    result = check_http(NAME, URL, TIMEOUT)

    assert "no reason given" in result.detail


def test_non_200_body_is_truncated_to_100_characters(monkeypatch):
    monkeypatch.setattr(requests, "get", returns(FakeResponse(500, text="x" * 500)))

    result = check_http(NAME, URL, TIMEOUT)

    assert result.detail == "HTTP 500, " + "x" * 100


@pytest.mark.parametrize("body, expected_in_detail", [
    ({"status": "degraded"}, "'degraded'"),
    ({"status": "error"}, "'error'"),
    ({"uptime": 123}, "None"),
    ({}, "None"),
])
def test_200_with_status_not_ok_is_degraded(monkeypatch, body, expected_in_detail):
    monkeypatch.setattr(requests, "get", returns(FakeResponse(200, body=body)))

    result = check_http(NAME, URL, TIMEOUT)

    assert result.state == DEGRADED
    assert expected_in_detail in result.detail


def test_invalid_json_is_degraded(monkeypatch):
    error = requests.exceptions.JSONDecodeError("Expecting value", "<html>", 0)
    monkeypatch.setattr(requests, "get", returns(FakeResponse(200, json_error=error)))

    result = check_http(NAME, URL, TIMEOUT)

    assert result.state == DEGRADED
    assert "JSON is invalid" in result.detail


@pytest.mark.parametrize("body", [["ok"], "ok", 42, None])
def test_json_that_is_not_an_object_is_degraded(monkeypatch, body):
    monkeypatch.setattr(requests, "get", returns(FakeResponse(200, body=body)))

    result = check_http(NAME, URL, TIMEOUT)

    assert result.state == DEGRADED
    assert "not a JSON object" in result.detail


# ---------------------------------------------------------------------------
# DOWN: could not reach it at all
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("error, expected_in_detail", [
    (requests.exceptions.ReadTimeout(), "No response within"),
    # ConnectTimeout is BOTH a ConnectionError and a Timeout, so this proves
    # the Timeout except block comes first.
    (requests.exceptions.ConnectTimeout(), "No response within"),
    (requests.exceptions.ConnectionError("Connection refused"), "refused"),
    (requests.exceptions.ConnectionError("Failed to resolve 'nope.invalid'"), "resolve"),
    (requests.exceptions.ConnectionError("[Errno -2] Name or service not known"), "resolve"),
    (requests.exceptions.ConnectionError("nodename nor servname provided"), "resolve"),
    (requests.exceptions.ConnectionError("connection reset"), "Connection failed"),
    (requests.exceptions.TooManyRedirects(), "TooManyRedirects"),
])
def test_unreachable_is_down(monkeypatch, error, expected_in_detail):
    monkeypatch.setattr(requests, "get", raises(error))

    result = check_http(NAME, URL, TIMEOUT)

    assert result.state == DOWN
    assert expected_in_detail in result.detail


def test_timeout_detail_includes_the_timeout_value(monkeypatch):
    monkeypatch.setattr(requests, "get", raises(requests.exceptions.ReadTimeout()))

    result = check_http(NAME, URL, TIMEOUT)

    assert "2.5s" in result.detail


def test_connection_refused_is_not_reported_as_timeout(monkeypatch):
    monkeypatch.setattr(requests, "get", raises(requests.exceptions.ConnectionError("refused")))

    result = check_http(NAME, URL, TIMEOUT)

    assert "No response within" not in result.detail


# ---------------------------------------------------------------------------
# Failures never carry a payload, and unrelated bugs are not swallowed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("response", [
    FakeResponse(500, text="boom"),
    FakeResponse(200, body={"status": "degraded"}),
])
def test_non_ok_results_have_empty_extra(monkeypatch, response):
    monkeypatch.setattr(requests, "get", returns(response))

    result = check_http(NAME, URL, TIMEOUT)

    assert result.extra == {}


def test_unrelated_exception_is_not_swallowed(monkeypatch):
    monkeypatch.setattr(requests, "get", raises(RuntimeError("bug")))

    with pytest.raises(RuntimeError):
        check_http(NAME, URL, TIMEOUT)