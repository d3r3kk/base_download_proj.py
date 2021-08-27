# download_proj.py

The base for a Python project that requires a list of downloaded files.

## Usage

Start with this project, make note of the configuration file - particularly the 'downloads' section. Each member of
that section is dictionary with the member fields: {'file_group': {'local_file_name': 'uri'}}. Multiple file groups
can be created, and within each multiple files can be created as well.

The 'output_path' will define where the downloads are saved to, with the file_group(s) being used as top-level
directories within that folder. Each file_group's set of files are downloaded to their appropriate directories.

See `python base_download_proj.py --help` for basic command line usage.

## Contributing

I welcome contributions! This is intended to just be a base project, perhaps it will be a `cookiecutter` someday
but I'm not worried about it. Under construction 👷‍♀️👷‍♂️ always.

## Notes

- If you use VS Code, there are sample/recommended settings you can make use of in the `.vscode/` folder.
