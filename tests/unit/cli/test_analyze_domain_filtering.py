from claude_builder.cli.analyze_commands import _resolve_domain_flags


def test_resolve_domain_flags_legacy_only():
    assert _resolve_domain_flags((), False, False) == (False, False)
    assert _resolve_domain_flags((), True, False) == (True, False)
    assert _resolve_domain_flags((), False, True) == (False, True)


def test_resolve_domain_flags_domains_override():
    # infra enables infra only
    assert _resolve_domain_flags(("infra",), False, False) == (True, False)
    # devops maps to infra bucket
    assert _resolve_domain_flags(("devops",), False, False) == (True, False)
    # mlops enables mlops bucket
    assert _resolve_domain_flags(("mlops",), False, False) == (False, True)
    # multiple values combine
    assert _resolve_domain_flags(("infra", "mlops"), False, False) == (True, True)
