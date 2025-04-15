import os
import tomli  # You may need to install this with: pip install tomli

def load_toml_env(file_path='.env.toml'):
    """
    Load environment variables from a TOML file.
    
    Args:
        file_path (str): Path to the TOML file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(file_path):
            print(f"TOML file not found: {file_path}")
            return False
            
        # Read the TOML file
        with open(file_path, 'rb') as f:
            config = tomli.load(f)
            
        # Set environment variables from the TOML config
        # Flattening the nested structure
        if 'supabase' in config:
            os.environ['SUPABASE_URL'] = config['supabase'].get('url', '')
            os.environ['SUPABASE_KEY'] = config['supabase'].get('key', '')
            os.environ['SUPABASE_SERVICE_ROLE_KEY'] = config['supabase'].get('service_role_key', '')
            
        if 'app' in config:
            os.environ['DEBUG'] = str(config['app'].get('debug', False)).lower()
            os.environ['ENVIRONMENT'] = config['app'].get('environment', 'development')
            
        if 'deployment' in config:
            os.environ['PUBLIC_URL'] = config['deployment'].get('public_url', '')
            
        return True
        
    except Exception as e:
        print(f"Error loading TOML environment: {str(e)}")
        return False

# Example usage:
# from utils.toml_loader import load_toml_env
# load_toml_env()  # Call this before other environment loading 