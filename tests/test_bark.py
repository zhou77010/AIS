"""Tests for the Bark notification (MVP)."""

from __future__ import annotations

from communication.bark import build_push_url


def test_keeps_only_the_key_from_a_sample_url() -> None:
    target = "https://api.day.app/ABC123/推送测试内容/点击查看详情"

    assert build_push_url(target) == "https://api.day.app/ABC123"


def test_accepts_a_bare_key() -> None:
    assert build_push_url("ABC123") == "https://api.day.app/ABC123"


def test_keeps_a_self_hosted_host() -> None:
    target = "https://bark.example.com/ABC123/"

    assert build_push_url(target) == "https://bark.example.com/ABC123"
