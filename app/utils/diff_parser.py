import re
from typing import List
from app.models.diff_models import Change, FileChange, DiffResult


def parse_diff(diff_text: str) -> DiffResult:
    """
    Parse a unified diff string and extract structured information.
    
    Args:
        diff_text: A unified diff patch string
        
    Returns:
        DiffResult containing parsed file changes with hunks, added/removed lines,
        and surrounding context
    """
    files: List[FileChange] = []
    
    # Split diff into file sections
    # Unified diff format: starts with "diff --git" or "--- a/file" or "+++ b/file"
    file_sections = _split_into_file_sections(diff_text)
    
    for section in file_sections:
        if not section.strip():
            continue
            
        filename = _extract_filename(section)
        if not filename:
            continue
            
        changes = _parse_file_changes(section)
        # Include file even if there are no changes (empty changes list)
        files.append(FileChange(filename=filename, changes=changes))
    
    return DiffResult(files=files)


def _split_into_file_sections(diff_text: str) -> List[str]:
    """Split diff text into sections for each file."""
    # Pattern to match the start of a new file section (diff --git)
    # We use "diff --git" as the primary marker for new files
    file_start_pattern = r'^diff --git'
    
    sections = []
    current_section = []
    lines = diff_text.split('\n')
    
    for line in lines:
        if re.match(file_start_pattern, line):
            if current_section:
                sections.append('\n'.join(current_section))
            current_section = [line]
        else:
            current_section.append(line)
    
    if current_section:
        sections.append('\n'.join(current_section))
    
    # If no "diff --git" found, try splitting by "--- a/" (fallback for simpler diffs)
    if not sections or (len(sections) == 1 and not re.match(file_start_pattern, sections[0].split('\n')[0])):
        sections = []
        current_section = []
        for line in lines:
            if line.startswith('--- a/'):
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        if current_section:
            sections.append('\n'.join(current_section))
    
    return sections if sections else [diff_text]


def _extract_filename(section: str) -> str:
    """Extract filename from a diff section."""
    lines = section.split('\n')
    
    # Try to extract from "--- a/path" or "+++ b/path"
    for line in lines:
        if line.startswith('--- a/'):
            # Remove "--- a/" prefix and any trailing whitespace
            filename = line[6:].strip()
            # Handle case where filename might have tab or additional info
            filename = filename.split('\t')[0]
            return filename
        elif line.startswith('+++ b/'):
            filename = line[6:].strip()
            filename = filename.split('\t')[0]
            return filename
        elif line.startswith('diff --git'):
            # Format: "diff --git a/path b/path"
            match = re.search(r'diff --git a/(.+?)\s+b/(.+)', line)
            if match:
                return match.group(2).strip()
    
    return ""


def _parse_file_changes(section: str) -> List[Change]:
    """Parse hunks and line changes from a file section."""
    changes: List[Change] = []
    lines = section.split('\n')
    
    # Track current line numbers for old and new files
    old_line_num = 0
    new_line_num = 0
    in_hunk = False
    
    for line in lines:
        # Skip file headers and metadata
        if line.startswith('---') or line.startswith('+++') or line.startswith('diff'):
            continue
        if line.startswith('index ') or line.startswith('new file') or line.startswith('deleted file'):
            continue
        if line.startswith('similarity index') or line.startswith('rename'):
            continue
        
        # Hunk header: @@ -old_start,old_count +new_start,new_count @@
        hunk_match = re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
        if hunk_match:
            in_hunk = True
            old_start = int(hunk_match.group(1))
            old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 0
            new_start = int(hunk_match.group(3))
            new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 0
            
            # Reset line numbers to hunk start positions
            old_line_num = old_start
            new_line_num = new_start
            continue
        
        if not in_hunk:
            continue
        
        # Parse line changes
        if line.startswith(' '):
            # Context line (unchanged)
            changes.append(Change(
                line_number=new_line_num,
                type="context",
                content=line[1:]  # Remove leading space
            ))
            old_line_num += 1
            new_line_num += 1
        elif line.startswith('-'):
            # Removed line
            changes.append(Change(
                line_number=old_line_num,
                type="removed",
                content=line[1:]  # Remove leading minus
            ))
            old_line_num += 1
        elif line.startswith('+'):
            # Added line
            changes.append(Change(
                line_number=new_line_num,
                type="added",
                content=line[1:]  # Remove leading plus
            ))
            new_line_num += 1
        elif line.startswith('\\'):
            # No newline at end of file marker
            continue
    
    return changes

