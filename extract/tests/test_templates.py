from hawfinch.wikitext.templates import find_templates, normalize_name, scan


def test_named_and_positional_arguments():
    (t,) = find_templates("{{Wortart|Substantiv|Deutsch}}")
    assert t.name == "Wortart"
    assert t.positional() == ["Substantiv", "Deutsch"]
    assert t.get("1") == "Substantiv"

    (t,) = find_templates(
        "{{Deutsch Substantiv Übersicht\n|Genus=n\n|Nominativ Plural = Häuser \n}}"
    )
    assert t.params() == {"Genus": "n", "Nominativ Plural": "Häuser"}


def test_positional_values_keep_whitespace_and_the_later_argument_wins():
    (t,) = find_templates("{{x| a |2=b| c }}")
    assert t.args == ((None, " a "), ("2", "b"), (None, " c "))
    assert t.params() == {"1": " a ", "2": " c "}


def test_pipes_inside_links_nested_templates_and_refs_do_not_split():
    text = "{{T|Bild=Haus.jpg|[[Haus|ein Haus]]|{{U|a|b}}|x<ref>{{Lit|A=1|B}}</ref>}}"
    templates = scan(text).templates
    assert [t.name for t in templates] == ["T", "U", "Lit"]
    outer = templates[0]
    assert outer.positional() == ["[[Haus|ein Haus]]", "{{U|a|b}}", "x<ref>{{Lit|A=1|B}}</ref>"]
    assert outer.depth == 0 and templates[1].depth == 1
    assert templates[2].params() == {"A": "1", "1": "B"}
    assert text[templates[2].start : templates[2].end] == "{{Lit|A=1|B}}"


def test_equals_inside_nested_structures_does_not_name_an_argument():
    (t, _) = find_templates("{{T|{{U|k=v}}|[[a=b]]}}")
    assert t.args == ((None, "{{U|k=v}}"), (None, "[[a=b]]"))


def test_comments_are_removed_from_names_and_values():
    (t,) = find_templates("{{Wortart<!-- x -->|Verb|Deutsch}}")
    assert t.name == "Wortart"
    (t,) = find_templates("{{y|<!-- {{z}} -->a}}")
    assert t.params() == {"1": "a"}


def test_names_are_case_sensitive_and_lose_the_namespace_prefix():
    assert normalize_name(" Vorlage:Deutsch_Verb  Übersicht ") == "Deutsch Verb Übersicht"
    assert normalize_name("m") == "m" != normalize_name("M")
    assert normalize_name("#if: {{{1}}}") == "#if"


def test_links():
    links = scan("[[Haus]] und [[Garten|Gärten]]").links
    assert [(link.target, link.label) for link in links] == [("Haus", None), ("Garten", "Gärten")]


def test_unbalanced_markup_is_reported_not_raised():
    result = scan("{{a|[[b}} c]] {{d")
    assert [t.name for t in result.templates] == ["a"]
    assert sorted(a.kind for a in result.anomalies) == ["stray ]]", "unclosed [[", "unclosed {{"]
