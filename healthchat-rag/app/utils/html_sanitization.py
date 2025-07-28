"""
HTML and Script Tag Sanitization Utilities
Provides comprehensive sanitization to prevent XSS attacks
"""
import re
import logging
from typing import Any, Dict, List, Optional, Union
from html import escape, unescape
from urllib.parse import urlparse
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class HTMLSanitizer:
    """HTML and script tag sanitization for XSS prevention"""
    
    # Dangerous HTML tags that should be removed
    DANGEROUS_TAGS = {
        'script', 'object', 'embed', 'applet', 'form', 'input', 'textarea',
        'select', 'button', 'iframe', 'frame', 'frameset', 'noframes',
        'noscript', 'xmp', 'plaintext', 'listing', 'marquee', 'link',
        'meta', 'style', 'title', 'head', 'body', 'html', 'xml',
        'svg', 'math', 'foreignobject', 'desc', 'title'
    }
    
    # Dangerous attributes that should be removed
    DANGEROUS_ATTRIBUTES = {
        'onload', 'onunload', 'onclick', 'ondblclick', 'onmousedown',
        'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout',
        'onfocus', 'onblur', 'onkeypress', 'onkeydown', 'onkeyup',
        'onsubmit', 'onreset', 'onselect', 'onchange', 'onabort',
        'onerror', 'onbeforeunload', 'onbeforeprint', 'onafterprint',
        'onhashchange', 'onmessage', 'onoffline', 'ononline',
        'onpagehide', 'onpageshow', 'onpopstate', 'onresize',
        'onstorage', 'oncontextmenu', 'oninput', 'oninvalid',
        'onsearch', 'onwheel', 'oncopy', 'oncut', 'onpaste',
        'onbeforecopy', 'onbeforecut', 'onbeforepaste',
        'javascript:', 'vbscript:', 'data:', 'mocha:', 'livescript:'
    }
    
    # Allowed HTML tags with their allowed attributes
    ALLOWED_TAGS = {
        'p': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'div': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'span': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'br': {'class', 'id', 'style', 'title'},
        'hr': {'class', 'id', 'style', 'title', 'width', 'size', 'color'},
        'h1': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'h2': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'h3': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'h4': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'h5': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'h6': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'ul': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'ol': {'class', 'id', 'style', 'title', 'lang', 'dir', 'start', 'type'},
        'li': {'class', 'id', 'style', 'title', 'lang', 'dir', 'value'},
        'dl': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'dt': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'dd': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'table': {'class', 'id', 'style', 'title', 'lang', 'dir', 'border', 'cellpadding', 'cellspacing', 'width'},
        'thead': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'tbody': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'tfoot': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'tr': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'td': {'class', 'id', 'style', 'title', 'lang', 'dir', 'colspan', 'rowspan', 'width', 'height'},
        'th': {'class', 'id', 'style', 'title', 'lang', 'dir', 'colspan', 'rowspan', 'width', 'height', 'scope'},
        'caption': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'colgroup': {'class', 'id', 'style', 'title', 'lang', 'dir', 'span'},
        'col': {'class', 'id', 'style', 'title', 'lang', 'dir', 'span', 'width'},
        'a': {'class', 'id', 'style', 'title', 'lang', 'dir', 'href', 'target', 'rel'},
        'img': {'class', 'id', 'style', 'title', 'lang', 'dir', 'src', 'alt', 'width', 'height', 'border'},
        'strong': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'b': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'em': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'i': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'u': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        's': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'strike': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'del': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'ins': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'mark': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'small': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'big': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'sub': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'sup': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'code': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'pre': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'kbd': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'samp': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'var': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'cite': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'q': {'class', 'id', 'style', 'title', 'lang', 'dir', 'cite'},
        'abbr': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'acronym': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'address': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'blockquote': {'class', 'id', 'style', 'title', 'lang', 'dir', 'cite'},
        'fieldset': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'legend': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'article': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'section': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'nav': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'aside': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'header': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'footer': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'main': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'figure': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'figcaption': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'time': {'class', 'id', 'style', 'title', 'lang', 'dir', 'datetime'},
        'details': {'class', 'id', 'style', 'title', 'lang', 'dir', 'open'},
        'summary': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'ruby': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'rt': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'rp': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'bdi': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'bdo': {'class', 'id', 'style', 'title', 'lang', 'dir'},
        'wbr': {'class', 'id', 'style', 'title'},
        'meter': {'class', 'id', 'style', 'title', 'lang', 'dir', 'value', 'min', 'max', 'low', 'high', 'optimum'},
        'progress': {'class', 'id', 'style', 'title', 'lang', 'dir', 'value', 'max'},
        'output': {'class', 'id', 'style', 'title', 'lang', 'dir', 'for', 'form', 'name'},
        'canvas': {'class', 'id', 'style', 'title', 'lang', 'dir', 'width', 'height'},
        'audio': {'class', 'id', 'style', 'title', 'lang', 'dir', 'src', 'controls', 'autoplay', 'loop', 'muted', 'preload'},
        'video': {'class', 'id', 'style', 'title', 'lang', 'dir', 'src', 'controls', 'autoplay', 'loop', 'muted', 'preload', 'width', 'height', 'poster'},
        'source': {'class', 'id', 'style', 'title', 'lang', 'dir', 'src', 'type', 'media', 'sizes'},
        'track': {'class', 'id', 'style', 'title', 'lang', 'dir', 'src', 'kind', 'srclang', 'label', 'default'}
    }
    
    # Allowed CSS properties for style attributes
    ALLOWED_CSS_PROPERTIES = {
        'color', 'background-color', 'background-image', 'background-repeat',
        'background-position', 'background-size', 'border', 'border-color',
        'border-style', 'border-width', 'border-radius', 'margin', 'padding',
        'font-family', 'font-size', 'font-weight', 'font-style', 'text-align',
        'text-decoration', 'text-transform', 'line-height', 'letter-spacing',
        'word-spacing', 'text-indent', 'white-space', 'display', 'position',
        'top', 'right', 'bottom', 'left', 'width', 'height', 'max-width',
        'max-height', 'min-width', 'min-height', 'overflow', 'float', 'clear',
        'z-index', 'opacity', 'visibility', 'cursor', 'list-style', 'list-style-type',
        'list-style-position', 'list-style-image', 'table-layout', 'border-collapse',
        'border-spacing', 'caption-side', 'empty-cells', 'vertical-align'
    }
    
    # Allowed URL schemes
    ALLOWED_URL_SCHEMES = {'http', 'https', 'mailto', 'tel', 'ftp'}
    
    @classmethod
    def sanitize_html(cls, html_content: str, allowed_tags: Optional[Dict[str, set]] = None) -> str:
        """
        Sanitize HTML content to prevent XSS attacks
        
        Args:
            html_content: Raw HTML content to sanitize
            allowed_tags: Custom allowed tags and attributes (optional)
            
        Returns:
            Sanitized HTML content
        """
        if not html_content:
            return ""
        
        # Use custom allowed tags if provided, otherwise use defaults
        if allowed_tags is None:
            allowed_tags = cls.ALLOWED_TAGS
        
        try:
            # Sanitize the HTML content
            sanitized = cls._sanitize_html_content(html_content, allowed_tags)
            
            return sanitized
            
        except Exception as e:
            logger.error(f"HTML sanitization error: {str(e)}")
            # Return escaped content as fallback
            return cls.sanitize_text(html_content)
    
    @classmethod
    def _contains_dangerous_patterns(cls, content: str) -> bool:
        """Check if content contains dangerous patterns"""
        content_lower = content.lower()
        
        # Check for script tags and dangerous patterns
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'data:text/html',
            r'data:application/x-javascript',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<form[^>]*>',
            r'on\w+\s*=',
            r'expression\s*\(',
            r'url\s*\(',
            r'<svg[^>]*>',
            r'<math[^>]*>',
            r'<foreignobject[^>]*>'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                logger.debug(f"Dangerous pattern '{pattern}' found in HTML content")
                return True
        
        return False
    
    @classmethod
    def _sanitize_html_content(cls, content: str, allowed_tags: Dict[str, set]) -> str:
        """Sanitize HTML content by removing dangerous tags and attributes"""
        # Remove dangerous tags completely
        for tag in cls.DANGEROUS_TAGS:
            # Remove opening tags
            content = re.sub(rf'<{tag}[^>]*>', '', content, flags=re.IGNORECASE)
            # Remove closing tags
            content = re.sub(rf'</{tag}>', '', content, flags=re.IGNORECASE)
            # Remove self-closing tags
            content = re.sub(rf'<{tag}[^>]*/>', '', content, flags=re.IGNORECASE)
        
        # Sanitize allowed tags
        content = cls._sanitize_allowed_tags(content, allowed_tags)
        
        # Remove any remaining dangerous attributes
        content = cls._remove_dangerous_attributes(content)
        
        # Sanitize URLs in href and src attributes
        content = cls._sanitize_urls(content)
        
        # Sanitize style attributes
        content = cls._sanitize_style_attributes(content)
        
        # Remove any remaining dangerous patterns
        content = cls._remove_dangerous_patterns(content)
        
        return content
    
    @classmethod
    def _sanitize_allowed_tags(cls, content: str, allowed_tags: Dict[str, set]) -> str:
        """Sanitize allowed tags by keeping only allowed attributes"""
        def sanitize_tag(match):
            tag_name = match.group(1).lower()
            if tag_name not in allowed_tags:
                return ''  # Remove tag if not allowed
            
            # Get the full tag content
            full_tag = match.group(0)
            
            # Extract attributes
            attributes = cls._extract_attributes(full_tag)
            
            # Keep only allowed attributes
            allowed_attrs = allowed_tags[tag_name]
            sanitized_attrs = []
            
            for attr_name, attr_value in attributes.items():
                attr_name_lower = attr_name.lower()
                
                # Skip dangerous attributes
                if attr_name_lower in cls.DANGEROUS_ATTRIBUTES:
                    continue
                
                # Skip attributes not in allowed list
                if attr_name_lower not in allowed_attrs:
                    continue
                
                # Sanitize attribute value
                sanitized_value = cls._sanitize_attribute_value(attr_name_lower, attr_value)
                if sanitized_value is not None:
                    sanitized_attrs.append(f'{attr_name}="{sanitized_value}"')
            
            # Reconstruct tag
            if sanitized_attrs:
                return f'<{tag_name} {" ".join(sanitized_attrs)}>'
            else:
                return f'<{tag_name}>'
        
        # Apply sanitization to all tags
        content = re.sub(r'<([a-zA-Z][a-zA-Z0-9]*)[^>]*>', sanitize_tag, content)
        
        return content
    
    @classmethod
    def _extract_attributes(cls, tag: str) -> Dict[str, str]:
        """Extract attributes from an HTML tag"""
        attributes = {}
        
        # Find all attribute patterns
        attr_pattern = r'(\w+)\s*=\s*["\']([^"\']*)["\']'
        matches = re.findall(attr_pattern, tag)
        
        for attr_name, attr_value in matches:
            attributes[attr_name] = attr_value
        
        return attributes
    
    @classmethod
    def _sanitize_attribute_value(cls, attr_name: str, attr_value: str) -> Optional[str]:
        """Sanitize attribute value based on attribute type"""
        if not attr_value:
            return attr_value
        
        # Handle different attribute types
        if attr_name in {'href', 'src'}:
            return cls._sanitize_url(attr_value)
        elif attr_name == 'style':
            return cls._sanitize_css(attr_value)
        elif attr_name in {'class', 'id', 'title', 'lang', 'dir'}:
            # Simple text attributes - just escape
            return escape(attr_value)
        else:
            # Default: escape the value
            return escape(attr_value)
    
    @classmethod
    def _sanitize_urls(cls, content: str) -> str:
        """Sanitize URLs in href and src attributes"""
        def sanitize_url_attr(match):
            attr_name = match.group(1)
            url = match.group(2)
            
            sanitized_url = cls._sanitize_url(url)
            if sanitized_url is None:
                return ''  # Remove the entire attribute
            else:
                return f'{attr_name}="{sanitized_url}"'
        
        # Find and sanitize href and src attributes
        content = re.sub(r'(href|src)\s*=\s*["\']([^"\']*)["\']', sanitize_url_attr, content, flags=re.IGNORECASE)
        
        return content
    
    @classmethod
    def _sanitize_url(cls, url: str) -> Optional[str]:
        """Sanitize URL to prevent XSS"""
        if not url:
            return url
        
        # Check for dangerous schemes
        url_lower = url.lower()
        for scheme in ['javascript:', 'vbscript:', 'data:', 'mocha:', 'livescript:']:
            if url_lower.startswith(scheme):
                return None  # Remove dangerous URLs
        
        # Parse URL to check scheme
        try:
            parsed = urlparse(url)
            if parsed.scheme and parsed.scheme.lower() not in cls.ALLOWED_URL_SCHEMES:
                return None  # Remove URLs with disallowed schemes
        except Exception:
            # If URL parsing fails, treat as relative URL (allow it)
            pass
        
        return escape(url)
    
    @classmethod
    def _sanitize_css(cls, css: str) -> Optional[str]:
        """Sanitize CSS to prevent XSS"""
        if not css:
            return css
        
        # Remove dangerous CSS patterns
        dangerous_css_patterns = [
            r'expression\s*\(',
            r'url\s*\(\s*["\']?javascript:',
            r'url\s*\(\s*["\']?vbscript:',
            r'url\s*\(\s*["\']?data:',
            r'behavior\s*:',
            r'-moz-binding\s*:',
            r'<script',
            r'javascript:',
            r'vbscript:'
        ]
        
        css_lower = css.lower()
        for pattern in dangerous_css_patterns:
            if re.search(pattern, css_lower, re.IGNORECASE):
                return None  # Remove dangerous CSS
        
        # Only allow specific CSS properties
        sanitized_properties = []
        properties = css.split(';')
        
        for prop in properties:
            prop = prop.strip()
            if not prop:
                continue
            
            # Extract property name
            if ':' in prop:
                prop_name, prop_value = prop.split(':', 1)
                prop_name = prop_name.strip().lower()
                
                if prop_name in cls.ALLOWED_CSS_PROPERTIES:
                    sanitized_properties.append(f"{prop_name}: {prop_value.strip()}")
        
        return '; '.join(sanitized_properties) if sanitized_properties else None
    
    @classmethod
    def _remove_dangerous_attributes(cls, content: str) -> str:
        """Remove any remaining dangerous attributes"""
        for attr in cls.DANGEROUS_ATTRIBUTES:
            # Remove attribute patterns
            pattern = rf'\s+{re.escape(attr)}\s*=\s*["\'][^"\']*["\']'
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
            
            # Remove attribute patterns without quotes
            pattern = rf'\s+{re.escape(attr)}\s*=\s*[^\s>]+'
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        return content
    
    @classmethod
    def _remove_dangerous_patterns(cls, content: str) -> str:
        """Remove any remaining dangerous patterns from content"""
        # Remove javascript: URLs
        content = re.sub(r'javascript:[^"\']*', '', content, flags=re.IGNORECASE)
        
        # Remove vbscript: URLs
        content = re.sub(r'vbscript:[^"\']*', '', content, flags=re.IGNORECASE)
        
        # Remove data: URLs with dangerous content
        content = re.sub(r'data:text/html[^"\']*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'data:application/x-javascript[^"\']*', '', content, flags=re.IGNORECASE)
        
        # Remove expression() in CSS
        content = re.sub(r'expression\s*\([^)]*\)', '', content, flags=re.IGNORECASE)
        
        # Remove behavior: in CSS
        content = re.sub(r'behavior\s*:\s*url[^;]*', '', content, flags=re.IGNORECASE)
        
        return content
    
    @classmethod
    def _sanitize_style_attributes(cls, content: str) -> str:
        """Sanitize style attributes"""
        def sanitize_style_attr(match):
            style_content = match.group(1)
            sanitized_style = cls._sanitize_css(style_content)
            
            if sanitized_style is None:
                return ''  # Remove the entire style attribute
            else:
                return f'style="{sanitized_style}"'
        
        # Find and sanitize style attributes
        content = re.sub(r'style\s*=\s*["\']([^"\']*)["\']', sanitize_style_attr, content, flags=re.IGNORECASE)
        
        return content
    
    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Sanitize plain text by escaping HTML characters
        
        Args:
            text: Plain text to sanitize
            
        Returns:
            Escaped text safe for HTML output
        """
        if not text:
            return ""
        
        return escape(text)
    
    @classmethod
    def sanitize_json(cls, data: Any) -> Any:
        """
        Sanitize JSON data recursively
        
        Args:
            data: JSON data to sanitize
            
        Returns:
            Sanitized JSON data
        """
        if isinstance(data, dict):
            return {key: cls.sanitize_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [cls.sanitize_json(item) for item in data]
        elif isinstance(data, str):
            return cls.sanitize_text(data)
        else:
            return data

# Global sanitizer instance
html_sanitizer = HTMLSanitizer() 