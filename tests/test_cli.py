"""Tests for the command-line layer in cli.py.

These call main() directly with an explicit argv list, instead of
actually spawning a subprocess — this is exactly why we designed main()
to accept `argv: list[str] | None` back when we first wrote cli.py.
pytest's `capsys` fixture captures whatever the program printed, so we
can check it like any other return value.
"""

from dupfinder.cli import main


def test_no_duplicates_prints_message_and_exits_zero(tmp_path, capsys):
    (tmp_path / "a.txt").write_text("one")
    (tmp_path / "b.txt").write_text("two")

    exit_code = main([str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "No duplicates found." in captured.out


def test_duplicates_found_exits_zero_and_reports_them(tmp_path, capsys):
    (tmp_path / "a.txt").write_text("same")
    (tmp_path / "b.txt").write_text("same")

    exit_code = main([str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Duplicate set" in captured.out
    assert "1 duplicate set(s) found" in captured.out


def test_nonexistent_folder_exits_one_with_error_on_stderr(capsys):
    exit_code = main(["this_folder_should_not_exist_12345"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "is not a folder" in captured.err
    assert captured.out == ""


def test_absolute_flag_prints_full_paths(tmp_path, capsys):
    (tmp_path / "a.txt").write_text("same")
    (tmp_path / "b.txt").write_text("same")

    main([str(tmp_path), "--absolute"])

    captured = capsys.readouterr()
    assert str(tmp_path.resolve()) in captured.out


def test_version_flag_exits_cleanly(capsys):
    import pytest

    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "dupfinder" in captured.out