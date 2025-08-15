#!/usr/bin/env python
import os
from pathlib import Path
import subprocess


def remove_whitespace_nodes(node):
    """Recursively remove unnecessary whitespace-only text nodes."""
    from xml.dom.minidom import Node

    remove_list = []
    for child in node.childNodes:
        if child.nodeType == Node.TEXT_NODE and child.data.strip() == "":
            remove_list.append(child)
        elif child.hasChildNodes():
            remove_whitespace_nodes(child)
    for node in remove_list:
        node.parentNode.removeChild(node)


def format_xml(file_path):
    """Format XML file using xmllint or fallback to Python."""
    try:
        # First try with xmllint (if available)
        subprocess.run(
            ["xmllint", "--format", str(file_path), "-o", str(file_path)], check=True
        )
        print(f"[xmllint] Prettified {file_path}")
    except Exception:
        # Fallback: use minidom + fix whitespace issue
        import xml.dom.minidom

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        try:
            dom = xml.dom.minidom.parseString(content)
            remove_whitespace_nodes(dom)
            pretty_xml = dom.toprettyxml(indent="  ")
            # Avoid extra blank lines
            pretty_xml = "\n".join(
                [line for line in pretty_xml.splitlines() if line.strip()]
            )
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(pretty_xml)
            print(f"[python] Prettified {file_path}")
        except Exception as e:
            print(f"[error] Failed to parse {file_path}: {e}")


def main():
    # Get list of staged files
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
    )
    files = result.stdout.strip().splitlines()

    xml_files = [f for f in files if f.lower().endswith(".xml") and os.path.isfile(f)]
    for file in xml_files:
        print(f"Prettifying {file}")
        format_xml(file)
        subprocess.run(["git", "add", file])


if __name__ == "__main__":
    main()
