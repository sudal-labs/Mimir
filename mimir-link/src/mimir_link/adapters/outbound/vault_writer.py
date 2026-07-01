"""VaultWriter 구현체 — GitPython으로 backlink를 노트에 추가하고 커밋한다."""
import os

import frontmatter
from git import Actor, Repo

from mimir_link.domain.models import BacklinkEntry
from mimir_link.ports.outbound import VaultWriter

BACKLINK_FIELD = "relatedNotes"
COMMIT_AUTHOR = Actor("mimir-link", "mimir-link@local")


class GitVaultWriter(VaultWriter):
    """frontmatter에 relatedNotes 필드를 upsert하고 auto-commit한다."""

    def write_backlinks(self, entry: BacklinkEntry) -> None:
        """vault 노트 파일의 frontmatter를 갱신하고 git commit한다."""
        vault_path = os.getenv("VAULT_PATH", "/vault")
        absolute_file_path = os.path.join(vault_path, entry.file_path)

        if not os.path.exists(absolute_file_path):
            return

        with open(absolute_file_path, "r", encoding="utf-8") as file_handle:
            post = frontmatter.load(file_handle)

        existing_related: list[str] = list(post.metadata.get(BACKLINK_FIELD, []))
        merged = list(dict.fromkeys(existing_related + entry.related_note_ids))

        if merged == existing_related:
            return  # 변경 없음

        post.metadata[BACKLINK_FIELD] = merged
        with open(absolute_file_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(frontmatter.dumps(post))

        repo = Repo(vault_path)
        repo.index.add([entry.file_path])
        repo.index.commit(
            f"[mimir-link] backlink 갱신: {entry.file_path}",
            author=COMMIT_AUTHOR,
            committer=COMMIT_AUTHOR,
        )
