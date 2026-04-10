from chattool.explore.arxiv import PRESETS, ArxivQuery, build_query


def test_build_query_quotes_multi_word_keywords():
    query = build_query(
        categories=["cs.LO"],
        keywords=["interactive theorem proving", "formal mathematics"],
        title="synthetic differential geometry",
        author="Boon Suan Ho",
    )

    assert 'cat:cs.LO' in query
    assert 'all:"interactive theorem proving"' in query
    assert 'all:"formal mathematics"' in query
    assert 'ti:"synthetic differential geometry"' in query
    assert 'au:"Boon Suan Ho"' in query


def test_arxiv_query_builder_quotes_phrases():
    query = (
        ArxivQuery()
        .category("cs.LO")
        .keyword("interactive theorem proving")
        .title("formal mathematics")
        .author("Terence Tao")
        .build()
    )

    assert query == (
        'cat:cs.LO AND all:"interactive theorem proving" '
        'AND ti:"formal mathematics" AND au:"Terence Tao"'
    )


def test_weekly_preset_query_quotes_multi_word_terms():
    query = PRESETS["math-formalization-weekly"].query()

    assert 'all:"formal mathematics"' in query
    assert 'all:"interactive theorem proving"' in query
    assert 'all:"formal proof"' in query
    assert 'all:"proof search"' in query
