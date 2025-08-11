import os
import zipfile

def decompress(zip_file_path: str, name: str, base_dir: str = "/tmp/webots_worlds") -> str:
        """
        Decompresses a .zip file to a specific directory, creating a subfolder with the given name.
        
        :param zip_file_path: The path to the .zip file to decompress.
        :param name: The name to use for the extracted subfolder.
        :param base_dir: The base directory where the subfolder will be created (default: /tmp/webots_worlds).
        :return: The full path to the extracted directory.
        """
        # Combine base_dir and name to form the full extraction path
        extract_path = os.path.join(base_dir, name)
        
        # Create the extraction directory if it doesn't exist
        os.makedirs(extract_path, exist_ok=True)
        
        # Open the zip file and extract all contents to the extract_path
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        return extract_path