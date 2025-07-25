import sys
import os
import pytest
import markdown
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs')))

def test_component_documentation_exists():
    """Test that component documentation file exists and is readable"""
    doc_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'component_documentation.md')
    assert os.path.exists(doc_path), "Component documentation file does not exist"
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert len(content) > 0, "Component documentation file is empty"
        assert "# HealthChat RAG Dashboard - Component Documentation" in content, "Component documentation missing title"

def test_style_guide_exists():
    """Test that style guide documentation file exists and is readable"""
    doc_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'style_guide.md')
    assert os.path.exists(doc_path), "Style guide file does not exist"
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert len(content) > 0, "Style guide file is empty"
        assert "# HealthChat RAG Dashboard - Style Guide" in content, "Style guide missing title"

def test_user_guide_exists():
    """Test that user guide documentation file exists and is readable"""
    doc_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'user_guide.md')
    assert os.path.exists(doc_path), "User guide file does not exist"
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert len(content) > 0, "User guide file is empty"
        assert "# HealthChat RAG Dashboard - User Guide" in content, "User guide missing title"

def test_deployment_guide_exists():
    """Test that deployment guide documentation file exists and is readable"""
    doc_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'deployment_guide.md')
    assert os.path.exists(doc_path), "Deployment guide file does not exist"
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert len(content) > 0, "Deployment guide file is empty"
        assert "# HealthChat RAG Dashboard - Deployment Guide" in content, "Deployment guide missing title"

def test_component_documentation_structure():
    """Test that component documentation has proper structure"""
    doc_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'component_documentation.md')
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for required sections
        required_sections = [
            "## Authentication Components",
            "## Layout Components", 
            "## Dashboard Components",
            "## Health Profile Components",
            "## Chat Components",
            "## Metrics Components",
            "## Reports Components",
            "## Settings Components",
            "## Interactive Components",
            "## Performance Components"
        ]
        
        for section in required_sections:
            assert section in content, f"Missing section: {section}"

def test_style_guide_structure():
    """Test that style guide has proper structure"""
    doc_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'style_guide.md')
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for required sections
        required_sections = [
            "## Color Palette",
            "## Typography",
            "## Spacing and Layout",
            "## Component Styling",
            "## Icons and Visual Elements",
            "## Responsive Design",
            "## Accessibility",
            "## Theme System"
        ]
        
        for section in required_sections:
            assert section in content, f"Missing section: {section}"

def test_user_guide_structure():
    """Test that user guide has proper structure"""
    doc_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'user_guide.md')
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for required sections
        required_sections = [
            "## Getting Started",
            "## Dashboard Overview",
            "## Authentication & Profile",
            "## Health Profile Management",
            "## Chat with AI Assistant",
            "## Health Metrics Tracking",
            "## Reports & Analytics",
            "## Settings & Preferences",
            "## FAQ",
            "## Troubleshooting"
        ]
        
        for section in required_sections:
            assert section in content, f"Missing section: {section}"

def test_deployment_guide_structure():
    """Test that deployment guide has proper structure"""
    doc_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'deployment_guide.md')
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for required sections
        required_sections = [
            "## Prerequisites",
            "## Environment Configuration",
            "## Build Configuration",
            "## Deployment Scripts",
            "## Production Deployment",
            "## Environment-Specific Configs",
            "## Deployment Checklist",
            "## Monitoring & Maintenance",
            "## Troubleshooting"
        ]
        
        for section in required_sections:
            assert section in content, f"Missing section: {section}"

def test_markdown_formatting():
    """Test that all documentation files have proper markdown formatting"""
    docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
    
    for filename in os.listdir(docs_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(docs_dir, filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for proper markdown structure
                assert content.startswith('# '), f"{filename} should start with a main heading"
                assert '## ' in content, f"{filename} should have section headings"
                # Check for either code blocks or other markdown elements
                has_code_blocks = '```' in content
                has_lists = '- ' in content or '1. ' in content
                has_links = '[' in content and '](' in content
                assert has_code_blocks or has_lists or has_links, f"{filename} should have code blocks, lists, or links"

def test_code_blocks_formatting():
    """Test that code blocks in documentation are properly formatted"""
    docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
    
    for filename in os.listdir(docs_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(docs_dir, filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for properly closed code blocks
                code_block_count = content.count('```')
                assert code_block_count % 2 == 0, f"{filename} has unclosed code blocks"

def test_table_of_contents():
    """Test that documentation files have table of contents"""
    docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
    
    for filename in os.listdir(docs_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(docs_dir, filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for table of contents
                assert '## Table of Contents' in content, f"{filename} should have a table of contents"
                assert '1. [' in content, f"{filename} should have numbered list in TOC"

def test_documentation_completeness():
    """Test that documentation covers all major components"""
    doc_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'component_documentation.md')
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for component coverage
        required_components = [
            "Login Page",
            "Registration Page", 
            "Dashboard Header",
            "Sidebar Navigation",
            "Quick Stats Cards",
            "Activity Feed",
            "Health Profile",
            "Chat Interface",
            "Health Metrics",
            "Reports",
            "Settings",
            "Performance Optimization"
        ]
        
        for component in required_components:
            assert component in content, f"Missing component documentation: {component}"

def test_style_guide_completeness():
    """Test that style guide covers all design aspects"""
    doc_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'style_guide.md')
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for design system coverage
        required_elements = [
            "--primary-color",
            "--font-family-primary",
            "--spacing-md",
            ".btn-primary",
            ".card",
            ".form-input",
            ".table",
            "CSS Variables",
            "Responsive Design",
            "Accessibility"
        ]
        
        for element in required_elements:
            assert element in content, f"Missing style guide element: {element}"

def test_user_guide_completeness():
    """Test that user guide covers all user workflows"""
    doc_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'user_guide.md')
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for user workflow coverage
        required_workflows = [
            "Create Account",
            "Login",
            "Health Profile",
            "Chat with AI",
            "Health Metrics",
            "Reports",
            "Settings",
            "FAQ",
            "Troubleshooting"
        ]
        
        for workflow in required_workflows:
            assert workflow in content, f"Missing user workflow: {workflow}"

def test_deployment_guide_completeness():
    """Test that deployment guide covers all deployment aspects"""
    doc_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'deployment_guide.md')
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for deployment coverage
        required_aspects = [
            "Prerequisites",
            "Environment Variables",
            "Docker",
            "Nginx",
            "Systemd",
            "Monitoring",
            "Backup",
            "Rollback",
            "Troubleshooting"
        ]
        
        for aspect in required_aspects:
            assert aspect in content, f"Missing deployment aspect: {aspect}"

def test_documentation_links():
    """Test that documentation has proper internal links"""
    docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
    
    for filename in os.listdir(docs_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(docs_dir, filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for proper markdown links
                link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
                links = re.findall(link_pattern, content)
                
                for link_text, link_url in links:
                    assert link_text.strip(), f"Empty link text in {filename}"
                    assert link_url.strip(), f"Empty link URL in {filename}"

def test_documentation_version_info():
    """Test that documentation includes version information"""
    docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
    
    for filename in os.listdir(docs_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(docs_dir, filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for version history section
                assert '## Version History' in content, f"{filename} should have version history"
                assert 'v1.0.0' in content, f"{filename} should specify current version"

def test_documentation_file_sizes():
    """Test that documentation files are reasonably sized"""
    docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
    
    for filename in os.listdir(docs_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(docs_dir, filename)
            
            file_size = os.path.getsize(file_path)
            assert file_size > 1000, f"{filename} is too small ({file_size} bytes)"
            assert file_size < 100000, f"{filename} is too large ({file_size} bytes)"

def test_documentation_encoding():
    """Test that all documentation files use UTF-8 encoding"""
    docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
    
    for filename in os.listdir(docs_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(docs_dir, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # If we can read it as UTF-8, the test passes
                    assert len(content) > 0, f"{filename} is empty"
            except UnicodeDecodeError:
                pytest.fail(f"{filename} is not UTF-8 encoded") 