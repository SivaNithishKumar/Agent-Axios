"""Repository cloning service with LangSmith tracking."""
import os
import tempfile
import shutil
from git import Repo, GitCommandError
from langsmith import traceable
import logging

logger = logging.getLogger(__name__)

class RepoService:
    """Handles repository cloning and cleanup."""
    
    @traceable(name="clone_repository", run_type="tool")
    def clone(self, repo_url: str, branch: str = None) -> str:
        """
        Clone a git repository to a temporary directory.
        
        Args:
            repo_url: Git repository URL (https or ssh)
            branch: Optional branch name (defaults to repo's default branch)
        
        Returns:
            str: Absolute path to cloned repository
        
        Raises:
            GitCommandError: If cloning fails
        """
        temp_dir = None

        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix='agent_axios_')
            logger.info(f"Cloning {repo_url} to {temp_dir}")
            
            # Clone repository
            clone_kwargs = {
                'depth': 1,  # Shallow clone for speed
                'single_branch': True
            }
            
            if branch:
                clone_kwargs['branch'] = branch
            
            repo = Repo.clone_from(repo_url, temp_dir, **clone_kwargs)
            
            logger.info(f"Successfully cloned {repo_url}")
            logger.info(f"Active branch: {repo.active_branch.name}")
            logger.info(f"Last commit: {repo.head.commit.hexsha[:8]}")
            
            return temp_dir
            
        except GitCommandError as e:
            logger.error(f"Failed to clone {repo_url}: {str(e)}")
            # Cleanup on failure
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise Exception(f"Failed to clone repository: {str(e)}")
    
    @staticmethod
    def cleanup(repo_path: str):
        """
        Remove cloned repository directory.
        
        Args:
            repo_path: Path to repository directory
        """
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
                logger.info(f"Cleaned up repository at {repo_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {repo_path}: {str(e)}")
    
    @traceable(name="get_repo_metadata", run_type="tool")
    def get_metadata(self, repo_path: str) -> dict:
        """
        Extract repository metadata.
        
        Args:
            repo_path: Path to cloned repository
        
        Returns:
            dict: Repository metadata (branch, commit, etc.)
        """
        try:
            repo = Repo(repo_path)
            
            return {
                'branch': repo.active_branch.name,
                'commit': repo.head.commit.hexsha,
                'commit_message': repo.head.commit.message.strip(),
                'author': str(repo.head.commit.author),
                'commit_date': repo.head.commit.committed_datetime.isoformat(),
                'remotes': [remote.url for remote in repo.remotes]
            }
        except Exception as e:
            logger.warning(f"Failed to get metadata: {str(e)}")
            return {}
