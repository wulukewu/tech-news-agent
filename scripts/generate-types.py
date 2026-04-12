#!/usr/bin/env python3
"""
TypeScript Type Generator from Pydantic Models

This script generates TypeScript interfaces from Pydantic models in the backend.
It scans all schema files and creates corresponding TypeScript type definitions.

Requirements: 1.5, 8.1, 8.3
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime


# Type mapping from Python/Pydantic to TypeScript
TYPE_MAPPING = {
    'str': 'string',
    'int': 'number',
    'float': 'number',
    'bool': 'boolean',
    'datetime': 'string',  # ISO 8601 string
    'date': 'string',
    'UUID': 'string',
    'HttpUrl': 'string',
    'Any': 'any',
    'Dict': 'Record<string, any>',
    'List': 'Array',
    'Optional': 'null',
}


class PydanticModelExtractor(ast.NodeVisitor):
    """Extract Pydantic model definitions from Python AST"""

    def __init__(self):
        self.models: Dict[str, Dict] = {}
        self.current_class: Optional[str] = None
        self.imports: Set[str] = set()

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports to understand type dependencies"""
        if node.module:
            for alias in node.names:
                self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Extract class definitions that inherit from BaseModel"""
        # Check if class inherits from BaseModel
        is_pydantic = any(
            (isinstance(base, ast.Name) and base.id == 'BaseModel') or
            (isinstance(base, ast.Attribute) and base.attr == 'BaseModel')
            for base in node.bases
        )

        if is_pydantic:
            self.current_class = node.name
            self.models[node.name] = {
                'fields': {},
                'docstring': ast.get_docstring(node),
                'generics': self._extract_generics(node)
            }

            # Visit class body to extract fields
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    field_name = item.target.id

                    # Skip private fields and Config class
                    if field_name.startswith('_') or field_name == 'model_config':
                        continue

                    field_type = self._extract_type(item.annotation)
                    field_info = self._extract_field_info(item.value)

                    self.models[node.name]['fields'][field_name] = {
                        'type': field_type,
                        'optional': field_info.get('optional', False),
                        'description': field_info.get('description'),
                        'alias': field_info.get('alias'),
                    }

            self.current_class = None

        self.generic_visit(node)

    def _extract_generics(self, node: ast.ClassDef) -> List[str]:
        """Extract generic type parameters from class definition"""
        generics = []
        for base in node.bases:
            if isinstance(base, ast.Subscript):
                if isinstance(base.value, ast.Name) and base.value.id == 'Generic':
                    if isinstance(base.slice, ast.Name):
                        generics.append(base.slice.id)
                    elif isinstance(base.slice, ast.Tuple):
                        for elt in base.slice.elts:
                            if isinstance(elt, ast.Name):
                                generics.append(elt.id)
        return generics

    def _extract_type(self, annotation) -> str:
        """Extract type annotation as string"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            # Handle List[T], Optional[T], etc.
            if isinstance(annotation.value, ast.Name):
                base_type = annotation.value.id
                if isinstance(annotation.slice, ast.Name):
                    inner_type = annotation.slice.id
                    return f"{base_type}[{inner_type}]"
                elif isinstance(annotation.slice, ast.Tuple):
                    inner_types = [self._extract_type(elt) for elt in annotation.slice.elts]
                    return f"{base_type}[{', '.join(inner_types)}]"
            return str(ast.unparse(annotation))
        elif isinstance(annotation, ast.Attribute):
            return f"{annotation.value.id}.{annotation.attr}" if isinstance(annotation.value, ast.Name) else str(ast.unparse(annotation))
        return str(ast.unparse(annotation))

    def _extract_field_info(self, value) -> Dict:
        """Extract Field() information"""
        info = {}

        if isinstance(value, ast.Call):
            # Check if it's a Field() call
            if isinstance(value.func, ast.Name) and value.func.id == 'Field':
                # Extract default value
                if value.args:
                    first_arg = value.args[0]
                    if isinstance(first_arg, ast.Constant) and first_arg.value is None:
                        info['optional'] = True
                    elif isinstance(first_arg, ast.Name) and first_arg.id == 'None':
                        info['optional'] = True

                # Extract keyword arguments
                for keyword in value.keywords:
                    if keyword.arg == 'description' and isinstance(keyword.value, ast.Constant):
                        info['description'] = keyword.value.value
                    elif keyword.arg == 'alias' and isinstance(keyword.value, ast.Constant):
                        info['alias'] = keyword.value.value
                    elif keyword.arg == 'default' and isinstance(keyword.value, ast.Constant):
                        if keyword.value.value is None:
                            info['optional'] = True

        return info


def python_type_to_typescript(py_type: str, optional: bool = False) -> str:
    """Convert Python type annotation to TypeScript type"""
    # Handle Optional[T]
    if py_type.startswith('Optional['):
        inner = py_type[9:-1]
        return python_type_to_typescript(inner, optional=True)

    # Handle List[T]
    if py_type.startswith('List['):
        inner = py_type[5:-1]
        ts_inner = python_type_to_typescript(inner)
        result = f"{ts_inner}[]"
        return f"{result} | null" if optional else result

    # Handle Dict[K, V]
    if py_type.startswith('Dict['):
        result = 'Record<string, any>'
        return f"{result} | null" if optional else result

    # Direct mapping
    ts_type = TYPE_MAPPING.get(py_type, py_type)

    return f"{ts_type} | null" if optional else ts_type


def generate_typescript_interface(model_name: str, model_info: Dict) -> str:
    """Generate TypeScript interface from Pydantic model"""
    lines = []

    # Add docstring as comment
    if model_info.get('docstring'):
        lines.append('/**')
        for line in model_info['docstring'].split('\n'):
            lines.append(f' * {line}'.rstrip())
        lines.append(' */')

    # Generate interface declaration
    if model_info.get('generics'):
        generics_str = ', '.join(model_info['generics'])
        lines.append(f"export interface {model_name}<{generics_str}> {{")
    else:
        lines.append(f"export interface {model_name} {{")

    # Generate fields
    for field_name, field_info in model_info['fields'].items():
        # Use alias if available, otherwise use field name
        ts_field_name = field_info.get('alias') if field_info.get('alias') else field_name

        # Add field description as comment
        if field_info.get('description'):
            lines.append(f"  /** {field_info['description']} */")

        # Generate field type
        ts_type = python_type_to_typescript(field_info['type'], field_info.get('optional', False))
        optional_marker = '?' if field_info.get('optional') else ''

        lines.append(f"  {ts_field_name}{optional_marker}: {ts_type};")

    lines.append('}')
    lines.append('')

    return '\n'.join(lines)


def process_schema_file(file_path: Path) -> str:
    """Process a single schema file and generate TypeScript types"""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    tree = ast.parse(source)
    extractor = PydanticModelExtractor()
    extractor.visit(tree)

    # Generate TypeScript interfaces
    ts_code = []
    ts_code.append(f"// Generated from {file_path.name}")
    ts_code.append(f"// Generated at: {datetime.now().isoformat()}")
    ts_code.append('')

    for model_name, model_info in extractor.models.items():
        ts_code.append(generate_typescript_interface(model_name, model_info))

    return '\n'.join(ts_code)


def main():
    """Main entry point"""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Schema directory
    schema_dir = project_root / 'backend' / 'app' / 'schemas'

    # Output directory
    output_dir = project_root / 'frontend' / 'types' / 'api'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process all schema files
    schema_files = list(schema_dir.glob('*.py'))
    schema_files = [f for f in schema_files if f.name != '__init__.py']

    print(f"Found {len(schema_files)} schema files")

    all_types = []

    for schema_file in schema_files:
        print(f"Processing {schema_file.name}...")

        try:
            ts_code = process_schema_file(schema_file)

            # Write to individual file
            output_file = output_dir / f"{schema_file.stem}.ts"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(ts_code)

            print(f"  ✓ Generated {output_file.name}")

            # Collect for index file
            all_types.append((schema_file.stem, ts_code))

        except Exception as e:
            print(f"  ✗ Error processing {schema_file.name}: {e}")
            import traceback
            traceback.print_exc()

    # Generate index file
    index_content = []
    index_content.append("// Auto-generated API types")
    index_content.append(f"// Generated at: {datetime.now().isoformat()}")
    index_content.append("")

    for module_name, _ in all_types:
        index_content.append(f"export * from './{module_name}';")

    index_file = output_dir / 'index.ts'
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(index_content))

    print(f"\n✓ Generated {len(all_types)} type files")
    print(f"✓ Generated index file: {index_file}")
    print(f"\nTypes available at: frontend/types/api/")


if __name__ == '__main__':
    main()
