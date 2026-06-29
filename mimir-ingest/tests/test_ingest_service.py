"""IngestService 단위 테스트"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from mimir_ingest.services.ingest_service import IngestService


SAMPLE_MARKDOWN = """\
---
tags:
  - mimir
  - design
project: mimir
date: "2026-06-29"
status: draft
---
# Design Notes
내용입니다.
"""


@pytest.fixture
def mock_vault_reader():
    reader = MagicMock()
    reader.get_diff.return_value = [
        ("projects/mimir/design.md", "added", SAMPLE_MARKDOWN),
    ]
    return reader


@pytest.fixture
def mock_event_publisher():
    return AsyncMock()


@pytest.fixture
def service(mock_vault_reader, mock_event_publisher):
    return IngestService(vault_reader=mock_vault_reader, event_publisher=mock_event_publisher)


@pytest.mark.asyncio
async def test_handle_git_push_publishes_event(service, mock_event_publisher):
    """마크다운 파일 변경 시 NoteChangedEvent가 발행되어야 한다."""
    events = await service.handle_git_push(
        repo_path="/vault",
        before_hash="abc123",
        after_hash="def456",
    )

    assert len(events) == 1
    event = events[0]
    assert event.file_path == "projects/mimir/design.md"
    assert event.change_type == "added"
    assert event.commit_hash == "def456"
    assert event.frontmatter.tags == ["mimir", "design"]
    assert event.frontmatter.project == "mimir"
    assert event.frontmatter.status == "draft"
    mock_event_publisher.publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_git_push_skips_non_markdown(service, mock_vault_reader, mock_event_publisher):
    """마크다운이 아닌 파일은 이벤트를 발행하지 않고 건너뛴다."""
    mock_vault_reader.get_diff.return_value = [
        ("assets/diagram.png", "added", ""),
        ("scripts/setup.sh", "modified", "#!/bin/bash"),
    ]

    events = await service.handle_git_push("/vault", "abc123", "def456")

    assert events == []
    mock_event_publisher.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_git_push_with_deleted_file(service, mock_vault_reader, mock_event_publisher):
    """삭제된 마크다운 파일도 'deleted' 이벤트로 발행되어야 한다."""
    mock_vault_reader.get_diff.return_value = [
        ("old_note.md", "deleted", ""),
    ]

    events = await service.handle_git_push("/vault", "abc123", "def456")

    assert len(events) == 1
    assert events[0].change_type == "deleted"
    assert events[0].content == ""


@pytest.mark.asyncio
async def test_derive_note_id_from_file_path(service):
    """note_id는 파일 경로에서 슬러그 형태로 생성되어야 한다."""
    note_id = service._derive_note_id("projects/mimir/design.md")
    assert note_id == "projects_mimir_design_md"


def test_parse_frontmatter_with_empty_content(service):
    """빈 내용은 기본 FrontmatterData를 반환해야 한다."""
    result = service._parse_frontmatter("")
    assert result.tags == []
    assert result.project == ""


def test_parse_frontmatter_with_invalid_yaml(service):
    """YAML 파싱 실패 시 기본 FrontmatterData를 반환해야 한다 (예외 전파 없음)."""
    result = service._parse_frontmatter("---\n{{invalid: yaml\n---\n내용")
    assert result.tags == []
