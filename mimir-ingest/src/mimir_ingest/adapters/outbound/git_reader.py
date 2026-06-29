"""VaultReader 구현체 — GitPython으로 커밋 간 diff를 읽는다."""
from git import Repo

from mimir_ingest.ports.outbound import VaultReader

CHANGE_TYPE_MAP: dict[str, str] = {
    "A": "added",
    "M": "modified",
    "D": "deleted",
    "R": "modified",
    "C": "added",
    "T": "modified",
}


class GitVaultReader(VaultReader):
    """GitPython Repo.diff()를 사용해 두 커밋 사이의 변경 파일 목록을 반환한다."""

    def get_diff(
        self,
        repo_path: str,
        before_hash: str,
        after_hash: str,
    ) -> list[tuple[str, str, str]]:
        """두 커밋 사이에 변경된 파일 목록을 반환한다."""
        repo = Repo(repo_path)
        before_commit = repo.commit(before_hash)
        after_commit = repo.commit(after_hash)
        diffs = before_commit.diff(after_commit)

        results: list[tuple[str, str, str]] = []
        for diff in diffs:
            change_type = CHANGE_TYPE_MAP.get(diff.change_type, "modified")
            file_path: str = diff.b_path or diff.a_path

            if change_type == "deleted":
                content = ""
            else:
                content = self._read_file_content(after_commit, file_path)

            results.append((file_path, change_type, content))

        return results

    def _read_file_content(
            self,
            commit: object,
            file_path: str
    ) -> str:
        """after_commit 트리에서 파일 내용을 UTF-8로 읽는다. 실패 시 빈 문자열 반환."""
        try:
            return commit.tree[file_path].data_stream.read().decode("utf-8")
        except Exception:
            return ""
