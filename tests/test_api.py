"""API endpoint tests using FakeVaultService (no filesystem)."""


class TestHealth:
    def test_health(self, fake_client):
        resp = fake_client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestNotesEndpoint:
    def test_list_all(self, fake_client):
        resp = fake_client.get("/notes")
        data = resp.json()
        assert resp.status_code == 200
        assert data["total"] == 5
        paths = {n["path"] for n in data["notes"]}
        assert "README.md" in paths
        assert "Projects/Homelab.md" in paths

    def test_list_filter_by_dir(self, fake_client):
        resp = fake_client.get("/notes", params={"dir": "Daily"})
        data = resp.json()
        assert data["total"] == 2
        assert all(n["path"].startswith("Daily/") for n in data["notes"])

    def test_list_filter_by_tag(self, fake_client):
        resp = fake_client.get("/notes", params={"tag": "infra"})
        data = resp.json()
        assert data["total"] == 1
        assert data["notes"][0]["path"] == "Projects/Homelab.md"

    def test_list_filter_by_dir_and_tag(self, fake_client):
        resp = fake_client.get("/notes", params={"dir": "Daily", "tag": "daily"})
        assert resp.json()["total"] == 2

    def test_list_nonexistent_dir(self, fake_client):
        resp = fake_client.get("/notes", params={"dir": "Nope"})
        assert resp.json()["total"] == 0

    def test_get_note(self, fake_client):
        resp = fake_client.get("/notes/Projects/Homelab.md")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Homelab"
        assert "kubernetes" in data["content"]
        assert "projects" in data["metadata"]["tags"]

    def test_get_note_not_found(self, fake_client):
        resp = fake_client.get("/notes/nonexistent.md")
        assert resp.status_code == 404

    def test_note_has_modified_timestamp(self, fake_client):
        resp = fake_client.get("/notes/Projects/Homelab.md")
        assert "modified" in resp.json()

    def test_note_summary_has_size(self, fake_client):
        resp = fake_client.get("/notes")
        for note in resp.json()["notes"]:
            assert "size" in note
            assert note["size"] > 0


class TestChangesEndpoint:
    def test_all_changes_since_epoch(self, fake_client):
        resp = fake_client.get("/changes", params={"since": "2000-01-01T00:00:00Z"})
        data = resp.json()
        assert resp.status_code == 200
        assert len(data["modified"]) == 5
        assert data["deleted"] == []
        assert "checked_at" in data

    def test_no_changes_since_future(self, fake_client):
        resp = fake_client.get("/changes", params={"since": "2099-01-01T00:00:00Z"})
        assert resp.json()["modified"] == []

    def test_changes_with_dir_filter(self, fake_client):
        resp = fake_client.get("/changes", params={
            "since": "2000-01-01T00:00:00Z", "dir": "Daily"
        })
        modified = resp.json()["modified"]
        assert all(p.startswith("Daily/") for p in modified)

    def test_changes_requires_since(self, fake_client):
        resp = fake_client.get("/changes")
        assert resp.status_code == 422


class TestSearchEndpoint:
    def test_search_finds_results(self, fake_client):
        resp = fake_client.get("/search", params={"q": "kubernetes"})
        data = resp.json()
        assert resp.status_code == 200
        assert data["total"] >= 1
        paths = {r["path"] for r in data["results"]}
        assert "Projects/Homelab.md" in paths

    def test_search_with_dir_filter(self, fake_client):
        resp = fake_client.get("/search", params={"q": "kubernetes", "dir": "Projects"})
        data = resp.json()
        assert data["total"] == 1

    def test_search_with_tag_filter(self, fake_client):
        resp = fake_client.get("/search", params={"q": "kubernetes", "tag": "daily"})
        data = resp.json()
        assert all(r["path"].startswith("Daily/") for r in data["results"])

    def test_search_no_results(self, fake_client):
        resp = fake_client.get("/search", params={"q": "xyznonexistent"})
        assert resp.json()["total"] == 0

    def test_search_requires_query(self, fake_client):
        resp = fake_client.get("/search")
        assert resp.status_code == 422

    def test_search_results_have_matches(self, fake_client):
        resp = fake_client.get("/search", params={"q": "obsidian"})
        for result in resp.json()["results"]:
            assert len(result["matches"]) > 0
