import time
from datetime import datetime, timezone


class TestListNotes:
    def test_lists_all_notes(self, vault_service):
        notes = vault_service.list_notes()
        paths = {n.path for n in notes}
        assert "README.md" in paths
        assert "Daily/2026-03-17.md" in paths
        assert "Projects/Homelab.md" in paths
        assert "plain.md" in paths
        assert len(notes) == 5

    def test_filter_by_directory(self, vault_service):
        notes = vault_service.list_notes(dir_filter="Daily")
        paths = {n.path for n in notes}
        assert paths == {"Daily/2026-03-17.md", "Daily/2026-03-18.md"}

    def test_filter_by_tag(self, vault_service):
        notes = vault_service.list_notes(tag="infra")
        assert len(notes) == 1
        assert notes[0].path == "Projects/Homelab.md"

    def test_filter_by_dir_and_tag(self, vault_service):
        notes = vault_service.list_notes(dir_filter="Daily", tag="daily")
        assert len(notes) == 2

    def test_nonexistent_directory_returns_empty(self, vault_service):
        notes = vault_service.list_notes(dir_filter="Nonexistent")
        assert notes == []

    def test_nonexistent_tag_returns_empty(self, vault_service):
        notes = vault_service.list_notes(tag="nonexistent")
        assert notes == []

    def test_note_metadata_parsed(self, vault_service):
        notes = vault_service.list_notes(tag="projects")
        assert len(notes) == 1
        assert "infra" in notes[0].metadata["tags"]

    def test_note_without_frontmatter(self, vault_service):
        notes = vault_service.list_notes()
        plain = [n for n in notes if n.path == "plain.md"][0]
        assert plain.title == "plain"
        assert plain.metadata == {}


class TestGetNote:
    def test_get_existing_note(self, vault_service):
        note = vault_service.get_note("Projects/Homelab.md")
        assert note is not None
        assert note["title"] == "Homelab"
        assert "kubernetes" in note["content"]
        assert "projects" in note["metadata"]["tags"]
        assert note["modified"] is not None

    def test_get_nonexistent_note(self, vault_service):
        assert vault_service.get_note("nope.md") is None

    def test_path_traversal_blocked(self, vault_service):
        assert vault_service.get_note("../../../etc/passwd") is None

    def test_plain_note_content(self, vault_service):
        note = vault_service.get_note("plain.md")
        assert note is not None
        assert "No frontmatter here." in note["content"]


class TestGetChanges:
    def test_all_files_modified_since_epoch(self, vault_service):
        changes = vault_service.get_changes(datetime(2000, 1, 1, tzinfo=timezone.utc))
        assert len(changes["modified"]) == 5
        assert changes["deleted"] == []
        assert changes["checked_at"] is not None

    def test_no_changes_since_future(self, vault_service):
        changes = vault_service.get_changes(datetime(2099, 1, 1, tzinfo=timezone.utc))
        assert changes["modified"] == []

    def test_changes_filtered_by_dir(self, vault_service):
        changes = vault_service.get_changes(
            datetime(2000, 1, 1, tzinfo=timezone.utc), dir_filter="Daily"
        )
        assert set(changes["modified"]) == {"Daily/2026-03-17.md", "Daily/2026-03-18.md"}

    def test_detects_modified_file(self, vault_service, vault_dir):
        before = datetime.now(tz=timezone.utc)
        time.sleep(0.05)
        (vault_dir / "README.md").write_text("updated")
        changes = vault_service.get_changes(before)
        assert "README.md" in changes["modified"]
        assert len(changes["modified"]) == 1


class TestSearch:
    def test_search_finds_matching_content(self, vault_service):
        results = vault_service.search("kubernetes")
        paths = {r["path"] for r in results}
        assert "Projects/Homelab.md" in paths
        assert "Daily/2026-03-17.md" in paths

    def test_search_case_insensitive(self, vault_service):
        results = vault_service.search("KUBERNETES")
        assert len(results) > 0

    def test_search_returns_matching_lines(self, vault_service):
        results = vault_service.search("obsidian")
        r = [r for r in results if r["path"] == "Daily/2026-03-18.md"][0]
        assert any("obsidian" in m.lower() for m in r["matches"])

    def test_search_with_dir_filter(self, vault_service):
        results = vault_service.search("kubernetes", dir_filter="Projects")
        assert len(results) == 1
        assert results[0]["path"] == "Projects/Homelab.md"

    def test_search_with_tag_filter(self, vault_service):
        results = vault_service.search("kubernetes", tag="daily")
        assert all(r["path"].startswith("Daily/") for r in results)

    def test_search_no_results(self, vault_service):
        results = vault_service.search("xyznonexistent")
        assert results == []


class TestCaching:
    def test_metadata_cache_used(self, vault_service):
        notes1 = vault_service.list_notes()
        notes2 = vault_service.list_notes()
        # Same objects from cache
        for n1, n2 in zip(notes1, notes2):
            assert n1 is n2

    def test_cache_invalidated_on_mtime_change(self, vault_service, vault_dir):
        notes_before = vault_service.list_notes(tag="meta")
        assert len(notes_before) == 1

        time.sleep(0.05)
        (vault_dir / "README.md").write_text("---\ntags: [updated]\n---\nNew content")

        notes_after = vault_service.list_notes(tag="meta")
        assert len(notes_after) == 0
        notes_updated = vault_service.list_notes(tag="updated")
        assert len(notes_updated) == 1
