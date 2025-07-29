"""
Template rendering with Jinja2.
"""
from typing import Dict, Any, Optional, List
from jinja2 import Environment, Template, StrictUndefined, meta


class TemplateRenderer:
    """Renderer for Jinja2 templates with LLM-specific features."""
    
    def __init__(self):
        # Create Jinja2 environment with strict undefined handling
        self.env = Environment(
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['capitalize_first'] = self._capitalize_first
        self.env.filters['number_to_words'] = self._number_to_words
        self.env.filters['pluralize'] = self._pluralize
    
    def render_prompt(
        self, 
        prompt_template: str, 
        variables: Dict[str, Any],
        variable_definitions: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """
        Render a prompt template with variables.
        
        Args:
            prompt_template: Jinja2 template string
            variables: Variable values to use
            variable_definitions: Optional variable definitions with defaults
            
        Returns:
            Rendered prompt string
        """
        # Merge with defaults if variable definitions provided
        if variable_definitions:
            merged_vars = self._apply_defaults(variables, variable_definitions)
        else:
            merged_vars = variables
        
        # Create template and render
        template = self.env.from_string(prompt_template)
        return template.render(**merged_vars)
    
    def _apply_defaults(
        self, 
        variables: Dict[str, Any], 
        definitions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply default values for missing variables."""
        result = variables.copy()
        
        for var_name, var_def in definitions.items():
            if var_name not in result and "default" in var_def:
                result[var_name] = var_def["default"]
        
        return result
    
    # Custom filters
    def _capitalize_first(self, text: str) -> str:
        """Capitalize only the first letter."""
        return text[0].upper() + text[1:] if text else ""
    
    def _number_to_words(self, number: int) -> str:
        """Convert number to words (simple implementation)."""
        ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
        tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
        teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", 
                "sixteen", "seventeen", "eighteen", "nineteen"]
        
        if number == 0:
            return "zero"
        elif number < 10:
            return ones[number]
        elif number < 20:
            return teens[number - 10]
        elif number < 100:
            return tens[number // 10] + (" " + ones[number % 10] if number % 10 else "")
        else:
            return str(number)  # Fallback for larger numbers
    
    def _pluralize(self, word: str, count: int = 2) -> str:
        """Simple pluralization (English)."""
        if count == 1:
            return word
        
        # Simple rules
        if word.endswith('y') and not word.endswith(('ay', 'ey', 'oy', 'uy')):
            return word[:-1] + 'ies'
        elif word.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return word + 'es'
        else:
            return word + 's'
    
    def extract_variables(self, prompt_template: str) -> List[str]:
        """Extract variable names from a template."""
        try:
            ast = self.env.parse(prompt_template)
            return list(meta.find_undeclared_variables(ast))
        except:
            return []