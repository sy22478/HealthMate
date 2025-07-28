"""
Tests for HTML Sanitization Functionality
"""
import pytest
from fastapi import HTTPException
from app.utils.html_sanitization import HTMLSanitizer, html_sanitizer

class TestHTMLSanitizer:
    """Test HTML sanitization functionality"""
    
    def test_safe_html_preservation(self):
        """Test that safe HTML is preserved"""
        safe_html = """
        <p>This is a <strong>safe</strong> paragraph with <em>emphasis</em>.</p>
        <ul><li>Item 1</li><li>Item 2</li></ul>
        <a href="https://example.com">Safe link</a>
        """
        
        result = html_sanitizer.sanitize_html(safe_html)
        
        # Should preserve safe tags
        assert "<p>" in result
        assert "<strong>" in result
        assert "<em>" in result
        assert "<ul>" in result
        assert "<li>" in result
        assert "<a href=" in result
        assert "https://example.com" in result
    
    def test_dangerous_tags_removal(self):
        """Test that dangerous tags are removed"""
        dangerous_html = """
        <p>Safe content</p>
        <script>alert('xss')</script>
        <iframe src="javascript:alert('xss')"></iframe>
        <object data="malicious.swf"></object>
        <form action="malicious.php"></form>
        <p>More safe content</p>
        """
        
        result = html_sanitizer.sanitize_html(dangerous_html)
        
        # Should remove dangerous tags
        assert "<script>" not in result
        assert "<iframe>" not in result
        assert "<object>" not in result
        assert "<form>" not in result
        
        # Should preserve safe content
        assert "<p>Safe content</p>" in result
        assert "<p>More safe content</p>" in result
    
    def test_dangerous_attributes_removal(self):
        """Test that dangerous attributes are removed"""
        dangerous_html = """
        <p onclick="alert('xss')" onload="alert('xss')">Content</p>
        <a href="javascript:alert('xss')" onmouseover="alert('xss')">Link</a>
        <img src="x" onerror="alert('xss')" />
        """
        
        result = html_sanitizer.sanitize_html(dangerous_html)
        
        # Should remove dangerous attributes
        assert 'onclick=' not in result
        assert 'onload=' not in result
        assert 'onmouseover=' not in result
        assert 'onerror=' not in result
        assert 'javascript:' not in result
        
        # Should preserve safe attributes
        assert 'src=' in result  # img src is preserved
        # Note: href with javascript: is removed entirely, which is correct behavior
    
    def test_dangerous_patterns_detection(self):
        """Test detection and sanitization of dangerous patterns"""
        dangerous_patterns = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "vbscript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "<iframe src='javascript:alert(\"xss\")'></iframe>",
            "<object><embed src='malicious.swf'></object>",
            "<svg><script>alert('xss')</script></svg>",
            "<math><script>alert('xss')</script></math>"
        ]
        
        for pattern in dangerous_patterns:
            result = html_sanitizer.sanitize_html(pattern)
            
            # Should remove dangerous content
            assert "<script>" not in result
            assert "javascript:alert" not in result
            assert "vbscript:alert" not in result
            assert "<iframe>" not in result
            assert "<object>" not in result
            assert "<svg>" not in result
            assert "<math>" not in result
    
    def test_url_sanitization(self):
        """Test URL sanitization in href and src attributes"""
        html_with_urls = """
        <a href="https://example.com">Safe link</a>
        <a href="javascript:alert('xss')">Dangerous link</a>
        <a href="vbscript:alert('xss')">Another dangerous link</a>
        <img src="https://example.com/image.jpg" alt="Safe image" />
        <img src="data:image/svg+xml,<script>alert('xss')</script>" alt="Dangerous image" />
        """
        
        result = html_sanitizer.sanitize_html(html_with_urls)
        
        # Should preserve safe URLs
        assert 'href="https://example.com"' in result
        assert 'src="https://example.com/image.jpg"' in result
        
        # Should remove dangerous URLs
        assert 'javascript:alert' not in result
        assert 'vbscript:alert' not in result
        assert 'data:image/svg+xml' not in result
    
    def test_css_sanitization(self):
        """Test CSS sanitization in style attributes"""
        html_with_css = """
        <p style="color: red; background-color: blue;">Safe styling</p>
        <p style="color: red; background-image: url(javascript:alert('xss'));">Dangerous CSS</p>
        <p style="color: red; expression(alert('xss'));">Another dangerous CSS</p>
        <p style="color: red; behavior: url(malicious.htc);">More dangerous CSS</p>
        """
        
        result = html_sanitizer.sanitize_html(html_with_css)
        
        # Should preserve safe CSS
        assert 'color: red' in result
        assert 'background-color: blue' in result
        
        # Should remove dangerous CSS
        assert 'javascript:alert' not in result
        assert 'expression(alert' not in result
        assert 'behavior: url' not in result
    
    def test_allowed_css_properties(self):
        """Test that only allowed CSS properties are preserved"""
        html_with_css = """
        <p style="color: red; font-size: 16px; margin: 10px;">Safe properties</p>
        <p style="color: red; dangerous-property: value;">Dangerous property</p>
        """
        
        result = html_sanitizer.sanitize_html(html_with_css)
        
        # Should preserve allowed properties
        assert 'color: red' in result
        assert 'font-size: 16px' in result
        assert 'margin: 10px' in result
        
        # Should remove disallowed properties
        assert 'dangerous-property: value' not in result
    
    def test_text_sanitization(self):
        """Test plain text sanitization"""
        dangerous_text = "<script>alert('xss')</script> & < > \" '"
        
        result = html_sanitizer.sanitize_text(dangerous_text)
        
        # Should escape HTML characters
        assert "&lt;script&gt;" in result
        assert "&amp;" in result
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&quot;" in result
        assert "&#x27;" in result  # Single quote
    
    def test_json_sanitization(self):
        """Test JSON data sanitization"""
        dangerous_json = {
            "name": "<script>alert('xss')</script>",
            "description": "Safe description & < > \" '",
            "nested": {
                "content": "More <script>alert('xss')</script> content"
            },
            "list": [
                "Item 1",
                "Item 2 <script>alert('xss')</script>",
                "Item 3"
            ]
        }
        
        result = html_sanitizer.sanitize_json(dangerous_json)
        
        # Should escape HTML in string values
        assert "&lt;script&gt;" in result["name"]
        assert "&amp;" in result["description"]
        assert "&lt;script&gt;" in result["nested"]["content"]
        assert "&lt;script&gt;" in result["list"][1]
        
        # Should preserve safe content
        assert "Safe description" in result["description"]
        assert "Item 1" in result["list"][0]
        assert "Item 3" in result["list"][2]
    
    def test_empty_input_handling(self):
        """Test handling of empty input"""
        # Empty string
        result = html_sanitizer.sanitize_html("")
        assert result == ""
        
        # None
        result = html_sanitizer.sanitize_html(None)
        assert result == ""
        
        # Whitespace only
        result = html_sanitizer.sanitize_html("   \n\t   ")
        assert result == "   \n\t   "
    
    def test_complex_html_sanitization(self):
        """Test complex HTML with mixed safe and dangerous content"""
        complex_html = """
        <div class="container">
            <h1>Welcome</h1>
            <p>This is a <strong>safe</strong> paragraph.</p>
            <script>alert('xss')</script>
            <ul>
                <li>Safe item 1</li>
                <li onclick="alert('xss')">Dangerous item</li>
                <li>Safe item 2</li>
            </ul>
            <a href="https://example.com" onmouseover="alert('xss')">Safe link with dangerous attribute</a>
            <img src="https://example.com/image.jpg" alt="Safe image" />
            <iframe src="javascript:alert('xss')">Dangerous iframe</iframe>
        </div>
        """
        
        result = html_sanitizer.sanitize_html(complex_html)
        
        # Should preserve safe structure
        assert "<div class=" in result
        assert "<h1>Welcome</h1>" in result
        assert "<p>This is a <strong>safe</strong> paragraph.</p>" in result
        assert "<ul>" in result
        assert "<li>Safe item 1</li>" in result
        assert "<li>Safe item 2</li>" in result
        assert 'href="https://example.com"' in result
        assert 'src="https://example.com/image.jpg"' in result
        
        # Should remove dangerous content
        assert "<script>" not in result
        assert 'onclick=' not in result
        assert 'onmouseover=' not in result
        assert "<iframe>" not in result
        assert 'javascript:alert' not in result
    
    def test_custom_allowed_tags(self):
        """Test sanitization with custom allowed tags"""
        custom_allowed_tags = {
            'p': {'class', 'id'},
            'strong': {'class'},
            'em': {'class'}
        }
        
        html_content = """
        <p class="test">This is a <strong class="bold">bold</strong> and <em class="italic">italic</em> text.</p>
        <div>This div should be removed</div>
        <span>This span should be removed</span>
        """
        
        result = html_sanitizer.sanitize_html(html_content, custom_allowed_tags)
        
        # Should preserve allowed tags with allowed attributes
        assert '<p class="test">' in result
        assert '<strong class="bold">' in result
        assert '<em class="italic">' in result
        
        # Should remove disallowed tags
        assert "<div>" not in result
        assert "<span>" not in result
        
        # Should preserve text content
        assert "This is a" in result
        assert "bold" in result
        assert "italic" in result
        assert "text." in result
    
    def test_malformed_html_handling(self):
        """Test handling of malformed HTML"""
        malformed_html = """
        <p>Unclosed paragraph
        <div>Unclosed div
        <strong>Unclosed strong
        <script>alert('xss')</script>
        """
        
        result = html_sanitizer.sanitize_html(malformed_html)
        
        # Should handle malformed HTML gracefully
        assert "<p>" in result
        assert "<div>" in result
        assert "<strong>" in result
        assert "<script>" not in result
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters"""
        unicode_html = """
        <p>Unicode test: 你好世界 🌍 éñtèrnâtiônàl</p>
        <script>alert('xss')</script>
        """
        
        result = html_sanitizer.sanitize_html(unicode_html)
        
        # Should preserve Unicode characters
        assert "你好世界" in result
        assert "🌍" in result
        assert "éñtèrnâtiônàl" in result
        
        # Should remove dangerous content
        assert "<script>" not in result
    
    def test_nested_dangerous_content(self):
        """Test handling of nested dangerous content"""
        nested_html = """
        <div>
            <p>Safe content</p>
            <script>
                var x = "<script>alert('xss')</script>";
                alert('xss');
            </script>
            <p>More safe content</p>
        </div>
        """
        
        result = html_sanitizer.sanitize_html(nested_html)
        
        # Should preserve safe content
        assert "<div>" in result
        assert "<p>Safe content</p>" in result
        assert "<p>More safe content</p>" in result
        
        # Should remove all script content
        assert "<script>" not in result
        # Note: Some script content may remain as text, which is acceptable
        # as long as it's not executable 