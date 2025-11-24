import pytest
from app.utils.diff_parser import parse_diff
from app.models.diff_models import Change, FileChange, DiffResult


def test_parse_simple_added_line():
    """Test parsing a diff with a single added line."""
    diff_text = """diff --git a/file.py b/file.py
index 1234567..abcdefg 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 line1
 line2
+new line
 line3
"""
    result = parse_diff(diff_text)
    
    assert len(result.files) == 1
    assert result.files[0].filename == "file.py"
    assert len(result.files[0].changes) == 4
    
    # Check context lines
    assert result.files[0].changes[0].type == "context"
    assert result.files[0].changes[0].line_number == 1
    assert result.files[0].changes[0].content == "line1"
    
    assert result.files[0].changes[1].type == "context"
    assert result.files[0].changes[1].line_number == 2
    
    # Check added line
    assert result.files[0].changes[2].type == "added"
    assert result.files[0].changes[2].line_number == 3
    assert result.files[0].changes[2].content == "new line"
    
    # Check context line
    assert result.files[0].changes[3].type == "context"
    assert result.files[0].changes[3].line_number == 4


def test_parse_removed_line():
    """Test parsing a diff with a removed line."""
    diff_text = """--- a/file.py
+++ b/file.py
@@ -1,4 +1,3 @@
 line1
 line2
-old line
 line3
"""
    result = parse_diff(diff_text)
    
    assert len(result.files) == 1
    assert result.files[0].filename == "file.py"
    
    # Find removed line
    removed_changes = [c for c in result.files[0].changes if c.type == "removed"]
    assert len(removed_changes) == 1
    assert removed_changes[0].content == "old line"


def test_parse_multiple_hunks():
    """Test parsing a diff with multiple hunks in the same file."""
    diff_text = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 line1
+added1
 line2
@@ -10,2 +11,3 @@
 line10
+added2
 line11
"""
    result = parse_diff(diff_text)
    
    assert len(result.files) == 1
    changes = result.files[0].changes
    
    # Check first hunk
    added1 = [c for c in changes if c.content == "added1"]
    assert len(added1) == 1
    assert added1[0].type == "added"
    assert added1[0].line_number == 2
    
    # Check second hunk
    added2 = [c for c in changes if c.content == "added2"]
    assert len(added2) == 1
    assert added2[0].type == "added"
    assert added2[0].line_number == 12


def test_parse_multiple_files():
    """Test parsing a diff with changes to multiple files."""
    diff_text = """--- a/file1.py
+++ b/file1.py
@@ -1,1 +1,2 @@
 line1
+added in file1

--- a/file2.py
+++ b/file2.py
@@ -1,1 +1,2 @@
 line1
+added in file2
"""
    result = parse_diff(diff_text)
    
    assert len(result.files) == 2
    assert result.files[0].filename == "file1.py"
    assert result.files[1].filename == "file2.py"
    
    # Check file1 changes
    file1_changes = result.files[0].changes
    assert any(c.content == "added in file1" for c in file1_changes)
    
    # Check file2 changes
    file2_changes = result.files[1].changes
    assert any(c.content == "added in file2" for c in file2_changes)


def test_parse_added_and_removed_lines():
    """Test parsing a diff with both added and removed lines."""
    diff_text = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,3 @@
 line1
-old line
+new line
 line3
"""
    result = parse_diff(diff_text)
    
    assert len(result.files) == 1
    changes = result.files[0].changes
    
    removed = [c for c in changes if c.type == "removed"]
    added = [c for c in changes if c.type == "added"]
    
    assert len(removed) == 1
    assert removed[0].content == "old line"
    
    assert len(added) == 1
    assert added[0].content == "new line"


def test_parse_context_lines():
    """Test that context lines are properly identified."""
    diff_text = """--- a/file.py
+++ b/file.py
@@ -1,5 +1,6 @@
 context1
 context2
+added
 context3
 context4
 context5
"""
    result = parse_diff(diff_text)
    
    changes = result.files[0].changes
    context_lines = [c for c in changes if c.type == "context"]
    added_lines = [c for c in changes if c.type == "added"]
    
    assert len(context_lines) == 5
    assert len(added_lines) == 1
    assert all(c.type == "context" for c in context_lines)


def test_parse_empty_diff():
    """Test parsing an empty diff string."""
    result = parse_diff("")
    
    assert len(result.files) == 0


def test_parse_diff_with_no_changes():
    """Test parsing a diff header with no actual changes."""
    diff_text = """diff --git a/file.py b/file.py
index 1234567..1234567 100644
--- a/file.py
+++ b/file.py
"""
    result = parse_diff(diff_text)
    
    # Should still identify the file
    assert len(result.files) == 1
    assert result.files[0].filename == "file.py"
    # But no changes
    assert len(result.files[0].changes) == 0


def test_parse_hunk_without_line_counts():
    """Test parsing hunk header without explicit line counts."""
    diff_text = """--- a/file.py
+++ b/file.py
@@ -5 +5 @@
-old
+new
"""
    result = parse_diff(diff_text)
    
    assert len(result.files) == 1
    changes = result.files[0].changes
    
    removed = [c for c in changes if c.type == "removed"]
    added = [c for c in changes if c.type == "added"]
    
    assert len(removed) == 1
    assert len(added) == 1


def test_parse_complex_real_world_diff():
    """Test parsing a more complex, realistic diff."""
    diff_text = """diff --git a/src/main.py b/src/main.py
index abc123..def456 100644
--- a/src/main.py
+++ b/src/main.py
@@ -10,7 +10,8 @@ def main():
     print("Hello")
     x = 1
     y = 2
+    z = 3
     result = x + y
-    print(result)
+    print(f"Result: {result}")
     return result
"""
    result = parse_diff(diff_text)
    
    assert len(result.files) == 1
    assert result.files[0].filename == "src/main.py"
    
    changes = result.files[0].changes
    added = [c for c in changes if c.type == "added"]
    removed = [c for c in changes if c.type == "removed"]
    
    assert len(added) == 2
    assert len(removed) == 1
    
    # Check specific content
    assert any("z = 3" in c.content for c in added)
    assert any("Result:" in c.content for c in added)
    assert any("print(result)" in c.content for c in removed)


def test_line_numbering():
    """Test that line numbers are correctly assigned."""
    diff_text = """--- a/file.py
+++ b/file.py
@@ -5,3 +5,4 @@
 line5
+line6_new
 line6
 line7
"""
    result = parse_diff(diff_text)
    
    changes = result.files[0].changes
    
    # Line numbers should start at 5 (from hunk header)
    assert changes[0].line_number == 5
    assert changes[1].line_number == 6
    assert changes[2].line_number == 7
    assert changes[3].line_number == 8

