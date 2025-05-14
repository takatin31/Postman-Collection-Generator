# Postman Collection Generator

A Python utility that automatically generates Postman collections from Java service interfaces in client projects.

## Overview

This tool scans Java projects for service interface files and model classes, then generates complete Postman collections that can be imported into Postman for API testing.

Key features:
- Automatically detects Java service interfaces and model classes
- Extracts API endpoints, parameters, and request/response models
- Generates structured Postman collections with proper authentication, headers, and request formats
- Supports organization by project/client
- Creates template request bodies based on model fields
- Includes a user-friendly GUI for selecting input and output directories

## Requirements

- Python 3.6 or higher
- For the GUI: tkinter (usually included with Python)

## Installation

1. Clone this repository:
```
git clone https://github.com/takatin31/postman-collection-generator.git
cd postman-collection-generator
```

2. No additional packages are required for basic functionality.

## Usage

### Command Line Interface

```
python postman_generator.py path/to/directory1 path/to/directory2 ... --output output_directory
```

Arguments:
- `path/to/directory`: One or more root directories to scan for client projects, or direct paths to client folders (ending with `-client`)
- `--output`: Directory where the generated Postman collections will be saved (default: `postman_collections`)

### Graphical User Interface

For a more user-friendly experience, run the GUI application:

```
python postman_gui.py
```

## GUI Features

![Postman Collection Generator GUI](https://github.com/takatin31/Postman-Collection-Generator/blob/master/images%20gui/gui.png)

The GUI includes:

1. **Tab Interface**:
   - **Root Directories**: Select directories to scan for client projects
   - **Client Folders**: Directly select specific client folders ending with `-client`

2. **Directory Management**:
   - Add multiple directories for processing
   - Remove selected directories
   - Clear all directories with one click

3. **Output Options**:
   - Select output directory for generated collections
   - Open output directory after generation completes

4. **Status Updates**:
   - Error notifications
   - Completion confirmation

## How It Works

1. The tool scans the specified directories for Java files:
   - Service interfaces (files ending with `Service.java`) in projects ending with `-client`
   - Model classes (other `.java` files) that define data structures

2. It parses these files to extract:
   - API endpoints (paths and HTTP methods)
   - Path and query parameters
   - Request and response models
   - JavaDoc descriptions

3. It generates Postman collections with:
   - Individual requests for each API endpoint
   - Appropriate authentication settings
   - Template request bodies based on model fields
   - Proper organization by project/client

4. The output includes:
   - Individual collection files for each service
   - Project-level collections that group services
   - A main collection containing all services

## Output Structure

Generated collections follow this structure:
- `All_Services.json`: Main collection with all services
- `{ProjectName}.json`: Collections for each project/client
- Individual service collections

## Notes

- The tool is designed to work with RESTful Java services, particularly those using JAX-RS annotations.
- Services must be in folders ending with `-client` to be detected by default.
- The tool assumes bearer token authentication is used for the APIs.

## License

[Your license information here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
