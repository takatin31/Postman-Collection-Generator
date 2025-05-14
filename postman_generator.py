import os
import re
import json
import uuid
import argparse
from pathlib import Path

def find_service_files(root_dir):
    """
    Find all files ending with 'Service.java' in projects ending with '-client'.
    - Ignores directories like node_modules and other common ignored folders
    """
    service_files = []
    ignored_dirs = {'node_modules', '.git', 'target', 'build', 'dist', 'bin', '.idea', '.vscode'}
    
    for root, dirs, files in os.walk(root_dir):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        
        # Check if we're in a project that ends with -client
        if any(part.endswith('-client') for part in root.split(os.sep)):
            for file in files:
                if file.endswith('Service.java'):
                    print(file)
                    service_files.append(os.path.join(root, file))
    
    return service_files

def find_model_files(root_dir):
    """Find all model/entity files in the project."""
    model_files = []
    ignored_dirs = {'node_modules', '.git', 'target', 'build', 'dist', 'bin', '.idea', '.vscode'}
    
    for root, dirs, files in os.walk(root_dir):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        
        for file in files:
            if file.endswith('.java') and not file.endswith('Service.java'):
                model_files.append(os.path.join(root, file))
    
    return model_files

def parse_model_file(file_path):
    """Parse a model file to extract fields."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract the class name
        class_name_match = re.search(r'public\s+(?:class|enum|interface)\s+(\w+)', content)
        if not class_name_match:
            return None
        
        class_name = class_name_match.group(1)
        
        # Extract fields
        fields = []
        
        # Look for field declarations
        field_pattern = re.compile(r'private\s+(\w+(?:<[^>]+>)?(?:\[\])?)\s+(\w+)\s*;', re.DOTALL)
        for match in field_pattern.finditer(content):
            field_type, field_name = match.groups()
            fields.append({
                'name': field_name,
                'type': field_type
            })
        
        return {
            'name': class_name,
            'fields': fields
        }
    except Exception as e:
        print(f"Error parsing model file {file_path}: {e}")
        return None

def create_model_template(model_info):
    """Create a template JSON object for a model."""
    if not model_info or not model_info.get('fields'):
        return {}
    
    template = {}
    for field in model_info['fields']:
        field_name = field['name']
        field_type = field['type']
        
        # Assign default values based on type
        if field_type in ['int', 'Integer', 'long', 'Long', 'short', 'Short', 'byte', 'Byte']:
            template[field_name] = 0
        elif field_type in ['float', 'Float', 'double', 'Double']:
            template[field_name] = 0.0
        elif field_type in ['boolean', 'Boolean']:
            template[field_name] = False
        elif field_type in ['String']:
            template[field_name] = ""
        elif field_type.endswith('[]') or 'List' in field_type or 'Set' in field_type:
            template[field_name] = []
        elif 'Map' in field_type:
            template[field_name] = {}
        else:
            # For complex types, use an empty object
            template[field_name] = {}
    
    return template

def parse_service_file(file_path, model_map):
    """Parse a Service interface file and extract API details with improved parameter parsing."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract the interface name
        interface_name_match = re.search(r'public\s+interface\s+(\w+)', content)
        interface_name = interface_name_match.group(1) if interface_name_match else os.path.basename(file_path).replace('.java', '')

        # Extract the base path
        path_match = re.search(r'@Path\("([^"]+)"\)', content)
        base_path = path_match.group(1) if path_match else ""

        # Extract methods
        methods = []

        method_pattern = re.compile(
            r'@(GET|POST|PUT|DELETE)\s+'
            r'@Path\("([^"]+)"\)\s*'
            r'(?:@(?:Produces|Consumes)\([^)]+\)\s*)*'
            r'([\w<>\[\],\s]+?)\s+'  # Return type
            r'(\w+)\s*\((.*?)\)\s*;',
            re.DOTALL
        )

        # Helper patterns
        query_param_pattern = re.compile(r'@QueryParam\s*\(\s*"([^"]+)"\s*\)')
        path_param_pattern = re.compile(r'@PathParam\s*\(\s*"([^"]+)"\s*\)')

        for match in method_pattern.finditer(content):
            http_method, path, return_type, method_name, params = match.groups()

            # Extract path params from the @Path
            path_params = re.findall(r'\{([^{}]+)\}', path)

            query_params = []
            path_params_annotated = []
            body_model = None

            # Safely split method parameters by commas (ignores generics/annotations)
            param_parts = [p.strip() for p in re.split(r',(?=(?:[^()]*\([^()]*\))*[^()]*$)', params)]

            for part in param_parts:
                # Query param
                qp_match = query_param_pattern.search(part)
                if qp_match:
                    query_params.append(qp_match.group(1))

                # Path param annotation
                pp_match = path_param_pattern.search(part)
                if pp_match:
                    path_params_annotated.append(pp_match.group(1))

                # Body model detection for POST/PUT (first non-annotated param that matches a known model)
                if http_method in ['POST', 'PUT'] and body_model is None:
                    no_annot = re.sub(r'@\w+\([^)]*\)', '', part)
                    for model in model_map:
                        if model in no_annot:
                            body_model = model
                            break

            # Merge @Path and annotation-extracted path params
            all_path_params = sorted(set(path_params + path_params_annotated))

            # Extract JavaDoc
            javadoc = ""
            method_start = match.start()
            javadoc_pattern = re.compile(r'/\*\*(.*?)\*/', re.DOTALL)
            for javadoc_match in javadoc_pattern.finditer(content[:method_start]):
                if not re.search(r'\S', content[javadoc_match.end():method_start].replace('@', '')):
                    javadoc = javadoc_match.group(1).strip()
                    javadoc = re.sub(r'\s*\*\s*', ' ', javadoc).strip()
                    desc_match = re.search(r'([^@.]+)', javadoc)
                    if desc_match:
                        javadoc = desc_match.group(1).strip()
                    break

            methods.append({
                'name': method_name,
                'http_method': http_method,
                'path': path,
                'description': javadoc,
                'return_type': return_type.strip(),
                'path_params': all_path_params,
                'query_params': query_params,
                'body_model': body_model
            })

        return {
            'interface_name': interface_name,
            'base_path': base_path,
            'methods': methods,
            'file_path': file_path
        }

    except Exception as e:
        print(f"Error parsing service file {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return {
            'interface_name': os.path.basename(file_path).replace('.java', ''),
            'base_path': "",
            'methods': [],
            'file_path': file_path
        }


def extract_project_name(project):
    """
    Extract the service name from the client folder name and ensure it ends with 's'.
    """
    # Remove -client suffix if present
    if project.endswith('-client'):
        name = project[:-7]  # Remove '-client'
    else:
        name = project
    
    # Ensure the name ends with 's'
    if not name.endswith('s'):
        name = name + 's'
    
    return name

def normalize_path(path_segments):
    """Normalize path segments to avoid double slashes."""
    # Remove empty segments
    result = [segment for segment in path_segments if segment]
    return result

def create_postman_collection(service_info, project_name, model_map):
    """Create a Postman collection from the service information."""
    interface_name = service_info['interface_name']
    collection_name = interface_name.replace('I', '', 1) if interface_name.startswith('I') else interface_name
    
    collection = {
        'info': {
            'name': collection_name,
            '_postman_id': str(uuid.uuid4()),
            'description': f'Collection for {interface_name}',
            'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
        },
        'item': [],
        'auth': {
            'type': 'bearer',
            'bearer': [
                {
                    'key': 'token',
                    'value': '{{intranetAccessToken}}',
                    'type': 'string'
                }
            ]
        },
        'variable': [
            {
                'key': 'baseUrl',
                'value': 'https://mdpa-11837.domad.local',
                'type': 'string'
            }
        ]
    }
    
    for method in service_info['methods']:
        request_name = ' '.join(re.findall('[A-Z][a-z]*', method['name']))
        if not request_name:
            request_name = method['name']
            
        # Build URL
        url_path = [project_name, 'api']
        
        # Add the base path if not empty and handle trailing slashes
        if service_info['base_path']:
            base_path_segments = service_info['base_path'].strip('/').split('/')
            url_path.extend([s for s in base_path_segments if s])
            
        # Add method path, handle trailing/leading slashes
        if method['path']:
            path_segments = method['path'].strip('/').split('/')
            path_segments = [s for s in path_segments if s]  # Remove empty segments
            
            # Replace path params with variables
            for i, segment in enumerate(path_segments):
                if '{' in segment:
                    path_segments[i] = segment.replace('{', '{{').replace('}', '}}')
                    
            url_path.extend(path_segments)
        
        # Normalize the path to avoid double slashes
        url_path = normalize_path(url_path)
        
        # Create request item
        request_item = {
            'name': request_name,
            'request': {
                'auth': {
                    'type': 'bearer',
                    'bearer': [
                        {
                            'key': 'token',
                            'value': '{{intranetAccessToken}}',
                            'type': 'string'
                        }
                    ]
                },
                'method': method['http_method'],
                'header': [
                    {
                        'key': 'Accept',
                        'value': 'application/json',
                        'type': 'text'
                    }
                ],
                'url': {
                    'raw': f"{{{{baseUrl}}}}/{'/'.join(url_path)}",
                    'host': ['{{baseUrl}}'],
                    'path': url_path
                },
                'description': method['description']
            },
            'response': []
        }
        
        if request_name == 'All Signatures Multiple Filters':
            print(method)

        # Add query parameters if any
        # Add query parameters if any
        if method['query_params']:
            query_params = []
            for param in method['query_params']:
                query_params.append({
                    'key': param,
                    'value': '',  # Leave empty or provide a placeholder like '{{' + param + '}}'
                    'description': ''
                })
            request_item['request']['url']['query'] = query_params
            
            # Properly rebuild the raw URL with both path and query parameters
            base_url = f"{{{{baseUrl}}}}/{'/'.join(url_path)}"
            query_str = '&'.join([f"{param}=" for param in method['query_params']])
            request_item['request']['url']['raw'] = f"{base_url}?{query_str}"
        
        # Add body if it's POST or PUT
        if method['http_method'] in ['POST', 'PUT']:
            request_item['request']['header'].append({
                'key': 'Content-Type',
                'value': 'application/json',
                'type': 'text'
            })
            
            # Get model template if available
            body_template = {}
            if method['body_model'] and method['body_model'] in model_map:
                body_template = create_model_template(model_map[method['body_model']])
            
            request_item['request']['body'] = {
                'mode': 'raw',
                'raw': json.dumps(body_template, indent=2),
                'options': {
                    'raw': {
                        'language': 'json'
                    }
                }
            }
        
        collection['item'].append(request_item)
    
    return collection

def main():
    parser = argparse.ArgumentParser(description='Generate Postman collections from Java service interfaces')
    parser.add_argument('root_dirs', nargs='+', help='Root directories to search for service files')
    parser.add_argument('--output', help='Output directory for Postman collections', default='postman_collections')
    args = parser.parse_args()
    
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # Initialize the model map
    model_map = {}
    service_files = []
    
    # Process each root directory
    for root_dir in args.root_dirs:
        # Find and parse all model files to build a mapping
        model_files = find_model_files(root_dir)
        print(f"Found {len(model_files)} model files in {root_dir}")
        
        for model_file in model_files:
            model_info = parse_model_file(model_file)
            if model_info:
                model_map[model_info['name']] = model_info
        
        # Find service files
        root_service_files = find_service_files(root_dir)
        print(f"Found {len(root_service_files)} service files in {root_dir}")
        service_files.extend(root_service_files)
    
    print(f"Parsed {len(model_map)} models successfully across all directories")
    print(f"Found {len(service_files)} service files across all directories")
    
    # Group by project (client) name
    projects = {}
    for file_path in service_files:
        path_parts = Path(file_path).parts
        client_part = next((part for part in path_parts if part.endswith('-client')), None)
        
        if client_part:
            if client_part not in projects:
                projects[client_part] = []
            projects[client_part].append(file_path)
    
    # Create a main collection that will contain all projects
    main_collection = {
        'info': {
            'name': 'MDPA API Services',
            '_postman_id': str(uuid.uuid4()),
            'description': 'Complete collection of all MDPA API services',
            'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
        },
        'item': [],
        'auth': {
            'type': 'bearer',
            'bearer': [
                {
                    'key': 'token',
                    'value': '{{intranetAccessToken}}',
                    'type': 'string'
                }
            ]
        },
        'variable': [
            {
                'key': 'baseUrl',
                'value': 'https://mdpa-11837.domad.local',
                'type': 'string'
            },
            {
                'key': 'intranetAccessToken',
                'value': '',
                'type': 'string'
            }
        ]
    }
    
    for project, files in projects.items():
        project_name = extract_project_name(project)
        project_collections = []
        
        project_folder = {
            'name': project_name,
            'item': [],
            'description': f'Services from {project}'
        }
        
        for file_path in files:
            try:
                service_info = parse_service_file(file_path, model_map)
                collection = create_postman_collection(service_info, project_name, model_map)
                project_collections.append(collection)
                
                # Add to project folder
                service_name = collection['info']['name']
                project_folder['item'].append({
                    'name': service_name,
                    'item': collection['item']
                })
                
                # Save individual collection
                filename = f"{service_info['interface_name'].replace('I', '', 1) if service_info['interface_name'].startswith('I') else service_info['interface_name']}.json"
                output_path = os.path.join(args.output, filename)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(collection, f, indent=2)
                
                print(f"Created collection: {output_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        # Add project folder to main collection
        main_collection['item'].append(project_folder)
        
        # Create a project-level collection
        if project_collections:
            project_collection = {
                'info': {
                    'name': project_name,
                    '_postman_id': str(uuid.uuid4()),
                    'description': f'Collection for {project}',
                    'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
                },
                'item': project_folder['item'],
                'auth': {
                    'type': 'bearer',
                    'bearer': [
                        {
                            'key': 'token',
                            'value': '{{intranetAccessToken}}',
                            'type': 'string'
                        }
                    ]
                },
                'variable': [
                    {
                        'key': 'baseUrl',
                        'value': 'https://mdpa-11837.domad.local',
                        'type': 'string'
                    },
                    {
                        'key': 'intranetAccessToken',
                        'value': '',
                        'type': 'string'
                    }
                ]
            }
            
            with open(os.path.join(args.output, f"{project_name}.json"), 'w', encoding='utf-8') as f:
                json.dump(project_collection, f, indent=2)
            
            print(f"Created project collection: {os.path.join(args.output, f'{project_name}.json')}")
    
    # Save the main collection
    with open(os.path.join(args.output, "All_Services.json"), 'w', encoding='utf-8') as f:
        json.dump(main_collection, f, indent=2)
    
    print(f"Created main collection: {os.path.join(args.output, 'All_Services.json')}")

if __name__ == "__main__":
    main()