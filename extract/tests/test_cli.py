import pytest

from hawfinch.cli import SUBCOMMANDS, main


def test_help_lists_subcommands(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    for name in SUBCOMMANDS:
        assert name in out


@pytest.mark.parametrize("name", SUBCOMMANDS)
def test_unimplemented_subcommand_fails(name, capsys):
    assert main([name]) == 1
    assert "not implemented" in capsys.readouterr().err
