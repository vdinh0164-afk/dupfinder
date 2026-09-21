"""test for pure duplicate detection
deleted right after without creating any unwanted files"""

from dupfinder.core import find_duplicates


def test_no_files_means_no_duplicates(tmp_path):
    assert find_duplicates(tmp_path) == {}


def test_identical_files_are_detected_as_duplicates(tmp_path):
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    file_a.write_text("hello world")
    file_b.write_text("hello world")

    duplicates = find_duplicates(tmp_path)

    assert len(duplicates) == 1
    (paths,) = duplicates.values()
    assert set(paths) == {file_a, file_b}


def test_different_content_is_not_flagged(tmp_path):
    (tmp_path / "a.txt").write_text("hello world")
    (tmp_path / "b.txt").write_text("something else entirely")

    assert find_duplicates(tmp_path) == {}


def test_same_size_different_content_is_not_a_false_positive(tmp_path):
    (tmp_path / "a.txt").write_text("aaaa")
    (tmp_path / "b.txt").write_text("bbbb")

    assert find_duplicates(tmp_path) == {}


def test_duplicates_are_found_across_subfolders(tmp_path):
    subfolder = tmp_path / "nested"
    subfolder.mkdir()

    file_a = tmp_path / "a.txt"
    file_b = subfolder / "b.txt"
    file_a.write_text("same content")
    file_b.write_text("same content")

    duplicates = find_duplicates(tmp_path)
    assert len(duplicates) == 1
    (paths,) = duplicates.values()
    assert set(paths) == {file_a, file_b}


def test_multiple_separate_duplicate_groups(tmp_path):
    (tmp_path / "a1.txt").write_text("group one")
    (tmp_path / "a2.txt").write_text("group one")
    (tmp_path / "b1.txt").write_text("group two")
    (tmp_path / "b2.txt").write_text("group two")
    (tmp_path / "unique.txt").write_text("nobody matches me")

    duplicates = find_duplicates(tmp_path)
    assert len(duplicates) == 2

    all_grouped_files = {p.name for group in duplicates.values() for p in group}
    assert all_grouped_files == {"a1.txt", "a2.txt", "b1.txt", "b2.txt"}


def test_three_way_duplicate_is_one_group_of_three(tmp_path):
    for name in ("a.txt", "b.txt", "c.txt"):
        (tmp_path / name).write_text("triplet content")

    duplicates = find_duplicates(tmp_path)
    assert len(duplicates) == 1
    (paths,) = duplicates.values()
    assert len(paths) == 3