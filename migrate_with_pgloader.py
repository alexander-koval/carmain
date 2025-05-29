#!/usr/bin/env python3
"""
Migration script using pgloader to migrate from SQLite to PostgreSQL.
Usage: python migrate_with_pgloader.py
"""

import os
import subprocess
import tempfile
import logging
from pathlib import Path

# Try to load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, try to read .env manually
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"\'')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_pgloader_config(sqlite_path: str, postgres_url: str) -> str:
    """Create pgloader configuration file."""
    config = f"""
LOAD DATABASE
    FROM sqlite://{sqlite_path}
    INTO {postgres_url}

WITH include drop, create tables, create indexes, reset sequences

SET work_mem to '256MB', maintenance_work_mem to '512 MB'

CAST type int when (= precision 1) to boolean drop typemod using tinyint-to-boolean,
     type char when (> precision 1) to varchar drop typemod,
     type datetime to timestamptz drop default drop not null using zero-dates-to-null

ALTER TABLE NAMES MATCHING ~/user/ IN SCHEMA 'public' RENAME TO '"user"'

BEFORE LOAD DO
$$
-- Ensure UTF-8 encoding
SET client_encoding TO 'UTF8';
$$;
"""
    return config


def run_pgloader(config_content: str) -> bool:
    """Run pgloader with the provided configuration."""
    try:
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.load', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        logger.info(f"Created pgloader config: {config_file}")
        logger.info("Running pgloader migration...")
        
        # Run pgloader
        result = subprocess.run(
            ['pgloader', config_file],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Log output
        if result.stdout:
            logger.info("pgloader output:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"  {line}")
        
        if result.stderr:
            logger.error("pgloader errors:")
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.error(f"  {line}")
        
        # Clean up config file
        os.unlink(config_file)
        
        if result.returncode == 0:
            logger.info("pgloader migration completed successfully!")
            return True
        else:
            logger.error(f"pgloader failed with return code: {result.returncode}")
            return False
            
    except FileNotFoundError:
        logger.error("pgloader not found. Install it first (see instructions above)")
        return False
    except Exception as e:
        logger.error(f"Error running pgloader: {e}")
        return False


def check_pgloader_installed() -> bool:
    """Check if pgloader is installed."""
    try:
        result = subprocess.run(['pgloader', '--version'], capture_output=True, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def install_pgloader_instructions():
    """Print instructions for installing pgloader."""
    logger.info("pgloader is not installed. To install it:")
    logger.info("")
    logger.info("Ubuntu/Debian:")
    logger.info("  sudo apt-get update")
    logger.info("  sudo apt-get install pgloader")
    logger.info("")
    logger.info("Arch Linux/Manjaro:")
    logger.info("  sudo pacman -S pgloader")
    logger.info("  # or from AUR:")
    logger.info("  yay -S pgloader")
    logger.info("")
    logger.info("macOS (with Homebrew):")
    logger.info("  brew install pgloader")
    logger.info("")
    logger.info("Docker (alternative):")
    logger.info("  docker run --rm -v $(pwd):/data dimitri/pgloader:latest pgloader /data/config.load")


def main():
    """Main function to run the migration."""
    # Configuration
    SQLITE_PATH = os.path.abspath("carmain.db")
    
    # PostgreSQL connection from environment variables
    postgres_user = os.getenv('POSTGRES_USER', 'carmain')
    postgres_password = os.getenv('POSTGRES_PASSWORD', 'carmain_password')
    postgres_host = os.getenv('POSTGRES_HOST', 'localhost')
    postgres_port = os.getenv('POSTGRES_PORT', '5432')
    postgres_db = os.getenv('POSTGRES_DB', 'carmain')
    
    postgres_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    
    logger.info("Starting Carmain database migration with pgloader...")
    logger.info(f"Source: SQLite ({SQLITE_PATH})")
    logger.info(f"Target: PostgreSQL ({postgres_host}:{postgres_port}/{postgres_db})")
    
    # Check if SQLite file exists
    if not os.path.exists(SQLITE_PATH):
        logger.error(f"SQLite database file not found: {SQLITE_PATH}")
        return
    
    # Check if pgloader is installed
    if not check_pgloader_installed():
        install_pgloader_instructions()
        return
    
    # Create pgloader configuration
    config = create_pgloader_config(SQLITE_PATH, postgres_url)
    
    # Run migration
    success = run_pgloader(config)
    
    if success:
        logger.info("✅ Migration completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Verify your data in PostgreSQL")
        logger.info("2. Update your application's DATABASE_URL")
        logger.info("3. Run any necessary post-migration scripts")
    else:
        logger.error("❌ Migration failed. Check the logs above for details.")


if __name__ == "__main__":
    main()