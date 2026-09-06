"""Unit tests for pre_push_verify.ponytail."""
from pre_push_verify.ponytail import analyze_diff


def test_detects_debug_print():
    diff = """
diff --git a/app.py b/app.py
@@ -1,3 +1,4 @@
+print("debug: here is value", val)
"""
    findings, removable = analyze_diff(diff)
    assert len(findings) == 1
    assert findings[0].tag == "delete"
    assert removable >= 1


def test_detects_commented_code():
    diff = """
diff --git a/app.py b/app.py
@@ -1,3 +1,4 @@
+# def old_function():
"""
    findings, removable = analyze_diff(diff)
    assert len(findings) == 1
    assert findings[0].tag == "delete"


def test_detects_stdlib_reinvention():
    diff = """
diff --git a/utils.py b/utils.py
@@ -1,3 +1,4 @@
+def join_path(a, b):
"""
    findings, removable = analyze_diff(diff)
    assert len(findings) == 1
    assert findings[0].tag == "stdlib"


def test_lean_code_passes():
    diff = """
diff --git a/app.py b/app.py
@@ -1,3 +1,4 @@
+def clean_code(data):
+    return [x.strip() for x in data if x]
"""
    findings, removable = analyze_diff(diff)
    assert len(findings) == 0
    assert removable == 0
