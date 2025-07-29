"""Export functionality for generation results."""
import json
import csv
import io
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Union
from datetime import datetime


def export_results(results: List[Dict[str, Any]], format: str) -> Union[Any, bytes, str]:
    """Export results in specified format."""
    if format == "json":
        return results
    
    elif format == "csv":
        if not results:
            return ""
        
        # Flatten nested dictionaries
        flattened_results = []
        for result in results:
            flat_result = _flatten_dict(result)
            flattened_results.append(flat_result)
        
        # Get all unique keys
        keys = set()
        for result in flattened_results:
            keys.update(result.keys())
        keys = sorted(keys)
        
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=keys)
        writer.writeheader()
        writer.writerows(flattened_results)
        
        return output.getvalue()
    
    elif format in ["markdown", "md"]:
        if not results:
            return "# No Results\n"
        
        output = ["# Generation Results\n"]
        output.append(f"Generated at: {datetime.utcnow().isoformat()}\n")
        
        for i, result in enumerate(results, 1):
            output.append(f"\n## Result {i}\n")
            _dict_to_markdown(result, output)
        
        return "\n".join(output)
    
    elif format == "html":
        if not results:
            return "<html><body><h1>No Results</h1></body></html>"
        
        html = ['<!DOCTYPE html><html><head><title>Generation Results</title>']
        html.append('<style>body{font-family:Arial,sans-serif;margin:20px;}')
        html.append('table{border-collapse:collapse;width:100%;margin:20px 0;}')
        html.append('th,td{border:1px solid #ddd;padding:8px;text-align:left;}')
        html.append('th{background-color:#f2f2f2;}</style></head><body>')
        html.append('<h1>Generation Results</h1>')
        html.append(f'<p>Generated at: {datetime.utcnow().isoformat()}</p>')
        
        # If results have consistent structure, show as table
        if _has_consistent_structure(results):
            html.append('<table><thead><tr>')
            keys = sorted(results[0].keys())
            for key in keys:
                html.append(f'<th>{key}</th>')
            html.append('</tr></thead><tbody>')
            
            for result in results:
                html.append('<tr>')
                for key in keys:
                    value = result.get(key, '')
                    html.append(f'<td>{_escape_html(str(value))}</td>')
                html.append('</tr>')
            html.append('</tbody></table>')
        else:
            # Show as individual sections
            for i, result in enumerate(results, 1):
                html.append(f'<h2>Result {i}</h2>')
                html.append('<pre>')
                html.append(_escape_html(json.dumps(result, indent=2)))
                html.append('</pre>')
        
        html.append('</body></html>')
        return ''.join(html)
    
    elif format == "xml":
        root = ET.Element("results")
        root.set("generated_at", datetime.utcnow().isoformat())
        
        for i, result in enumerate(results):
            result_elem = ET.SubElement(root, "result")
            result_elem.set("index", str(i + 1))
            _dict_to_xml(result, result_elem)
        
        return ET.tostring(root, encoding='unicode', method='xml')
    
    elif format == "txt":
        if not results:
            return "No results generated."
        
        output = ["Generation Results"]
        output.append("=" * 50)
        output.append(f"Generated at: {datetime.utcnow().isoformat()}")
        output.append("")
        
        for i, result in enumerate(results, 1):
            output.append(f"Result {i}:")
            output.append("-" * 30)
            _dict_to_text(result, output)
            output.append("")
        
        return "\n".join(output)
    
    elif format == "xlsx":
        # For XLSX, we'll return the data structure
        # The API endpoint will handle creating the actual file
        if not results:
            return {"sheets": [{"name": "Results", "data": []}]}
        
        # Flatten results for Excel
        flattened = []
        for result in results:
            flat_result = _flatten_dict(result)
            flattened.append(flat_result)
        
        return {
            "sheets": [{
                "name": "Results",
                "data": flattened
            }]
        }
    
    elif format == "pdf":
        # For PDF, return structured data
        # The API endpoint will handle PDF generation
        return {
            "title": "Generation Results",
            "generated_at": datetime.utcnow().isoformat(),
            "results": results
        }
    
    else:
        # Default to JSON
        return results


def _flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, json.dumps(v)))
        else:
            items.append((new_key, v))
    return dict(items)


def _dict_to_markdown(d: Dict[str, Any], output: List[str], level: int = 0) -> None:
    """Convert dictionary to markdown format."""
    for key, value in d.items():
        if isinstance(value, dict):
            output.append(f"{'  ' * level}- **{key}**:")
            _dict_to_markdown(value, output, level + 1)
        elif isinstance(value, list):
            output.append(f"{'  ' * level}- **{key}**: {json.dumps(value)}")
        else:
            output.append(f"{'  ' * level}- **{key}**: {value}")


def _dict_to_xml(d: Dict[str, Any], parent: ET.Element) -> None:
    """Convert dictionary to XML elements."""
    for key, value in d.items():
        # Make key XML-safe
        safe_key = key.replace(' ', '_').replace('-', '_')
        
        if isinstance(value, dict):
            elem = ET.SubElement(parent, safe_key)
            _dict_to_xml(value, elem)
        elif isinstance(value, list):
            elem = ET.SubElement(parent, safe_key)
            elem.text = json.dumps(value)
        else:
            elem = ET.SubElement(parent, safe_key)
            elem.text = str(value)


def _dict_to_text(d: Dict[str, Any], output: List[str], indent: int = 0) -> None:
    """Convert dictionary to text format."""
    for key, value in d.items():
        if isinstance(value, dict):
            output.append(f"{'  ' * indent}{key}:")
            _dict_to_text(value, output, indent + 1)
        elif isinstance(value, list):
            output.append(f"{'  ' * indent}{key}: {json.dumps(value)}")
        else:
            output.append(f"{'  ' * indent}{key}: {value}")


def _has_consistent_structure(results: List[Dict[str, Any]]) -> bool:
    """Check if all results have the same keys."""
    if not results:
        return False
    
    first_keys = set(results[0].keys())
    for result in results[1:]:
        if set(result.keys()) != first_keys:
            return False
    
    # Check if values are simple (not nested)
    for result in results:
        for value in result.values():
            if isinstance(value, (dict, list)):
                return False
    
    return True


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))