"""Layered backend for ACSL Agent.

``domain`` holds framework-free contracts and ports, ``application`` holds use
cases, ``adapters`` holds external integrations, and ``infrastructure`` holds
shared deployment settings. HTTP routing stays in ``apps/api/app`` and language
algorithms stay in ``engine``.
"""
