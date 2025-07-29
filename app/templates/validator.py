"""
Template validation functionality.
"""
import re
from typing import Dict, List, Any, Tuple
import jsonschema
from jinja2 import Environment, meta, TemplateSyntaxError


class TemplateValidator:
    """Validator for template structure and content."""
    
    def __init__(self):
        self.jinja_env = Environment()
    
    def validate_template(self, template_data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate template structure and content.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Validate Jinja2 syntax
        jinja_errors = self._validate_jinja_syntax(
            template_data.get("system_prompt", ""),
            template_data.get("user_prompt", "")
        )
        errors.extend(jinja_errors)
        
        # Check for undefined variables
        undefined_vars = self._check_undefined_variables(
            template_data.get("system_prompt", ""),
            template_data.get("user_prompt", ""),
            template_data.get("variables", {})
        )
        if undefined_vars:
            warnings.append(f"Undefined variables in prompts: {', '.join(undefined_vars)}")
        
        # Validate output schema if provided
        if "output_schema" in template_data:
            schema_errors = self._validate_json_schema(template_data["output_schema"])
            errors.extend(schema_errors)
        
        # Validate variable definitions
        var_errors = self._validate_variables(template_data.get("variables", {}))
        errors.extend(var_errors)
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    def _validate_jinja_syntax(self, system_prompt: str, user_prompt: str) -> List[str]:
        """Validate Jinja2 syntax in prompts."""
        errors = []
        
        for prompt_name, prompt in [("system_prompt", system_prompt), ("user_prompt", user_prompt)]:
            try:
                self.jinja_env.parse(prompt)
            except TemplateSyntaxError as e:
                errors.append(f"Invalid Jinja2 syntax in {prompt_name}: {str(e)}")
        
        return errors
    
    def _check_undefined_variables(
        self, system_prompt: str, user_prompt: str, variables: Dict[str, Any]
    ) -> List[str]:
        """Check for variables used in prompts but not defined."""
        undefined = []
        
        # Extract variables from prompts
        all_prompts = system_prompt + " " + user_prompt
        try:
            ast = self.jinja_env.parse(all_prompts)
            used_variables = meta.find_undeclared_variables(ast)
            
            # Check which ones are not defined
            for var in used_variables:
                if var not in variables:
                    undefined.append(var)
        except:
            pass  # Syntax errors handled elsewhere
        
        return undefined
    
    def _validate_json_schema(self, schema: Dict[str, Any]) -> List[str]:
        """Validate JSON schema structure."""
        errors = []
        
        # Basic validation of schema structure
        try:
            # Create a dummy validator to check schema validity
            jsonschema.Draft7Validator.check_schema(schema)
        except jsonschema.SchemaError as e:
            errors.append(f"Invalid JSON schema: {str(e)}")
        
        # Additional checks
        if "type" in schema:
            valid_types = ["object", "array", "string", "number", "boolean", "null"]
            if schema["type"] not in valid_types:
                errors.append(f"Invalid schema type: {schema['type']}")
        
        return errors
    
    def _validate_variables(self, variables: Dict[str, Any]) -> List[str]:
        """Validate variable definitions."""
        errors = []
        
        for var_name, var_def in variables.items():
            # Check variable name format
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name):
                errors.append(f"Invalid variable name: {var_name}")
            
            # Check variable definition
            if not isinstance(var_def, dict):
                errors.append(f"Variable {var_name} must be a dictionary")
                continue
            
            # Check required fields
            if "type" not in var_def:
                errors.append(f"Variable {var_name} missing 'type' field")
            elif var_def["type"] not in ["string", "number", "boolean", "array", "object"]:
                errors.append(f"Variable {var_name} has invalid type: {var_def['type']}")
            
            # Validate number constraints
            if var_def.get("type") == "number":
                if "min" in var_def and "max" in var_def:
                    if var_def["min"] > var_def["max"]:
                        errors.append(f"Variable {var_name}: min > max")
                
                if "default" in var_def:
                    default = var_def["default"]
                    if "min" in var_def and default < var_def["min"]:
                        errors.append(f"Variable {var_name}: default < min")
                    if "max" in var_def and default > var_def["max"]:
                        errors.append(f"Variable {var_name}: default > max")
        
        return errors