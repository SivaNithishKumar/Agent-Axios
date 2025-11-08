"""Quick test to verify a GitHub repository is valid and has code files."""
import sys
import tempfile
import shutil
from app.services.repo_service import RepoService
from app.services.chunking_service import ChunkingService

def test_repository(repo_url: str):
    """Test if a repository can be cloned and has code files."""
    print(f"\n🔍 Testing repository: {repo_url}")
    print("=" * 60)
    
    repo_service = RepoService()
    chunking_service = ChunkingService()
    repo_path = None
    
    try:
        # Step 1: Try to clone
        print("\n1️⃣  Cloning repository...")
        repo_path = repo_service.clone(repo_url)
        print(f"✅ Successfully cloned to: {repo_path}")
        
        # Step 2: Check for code files
        print("\n2️⃣  Scanning for code files...")
        chunks = chunking_service.process_directory(
            repo_path,
            analysis_id=None,  # Test mode
            max_files=10,  # Just check first 10 files
            max_chunks_per_file=5
        )
        
        files_found = chunking_service.files_processed
        chunks_found = len(chunks)
        
        print(f"\n📊 Results:")
        print(f"   • Files scanned: {files_found}")
        print(f"   • Code chunks created: {chunks_found}")
        
        if chunks_found == 0:
            print("\n⚠️  WARNING: No code chunks generated!")
            print("   This repository may:")
            print("   - Be empty")
            print("   - Contain no supported code files (.py, .js, .java, etc.)")
            print("   - Be private/inaccessible")
            return False
        else:
            print(f"\n✅ Repository is VALID for analysis!")
            print(f"   Found {chunks_found} code segments to analyze")
            return True
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False
    finally:
        # Cleanup
        if repo_path:
            try:
                shutil.rmtree(repo_path)
                print(f"\n🧹 Cleaned up temp directory")
            except:
                pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_repo.py <github_url>")
        print("\nExample:")
        print("  python test_repo.py https://github.com/pallets/flask")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    is_valid = test_repository(repo_url)
    sys.exit(0 if is_valid else 1)
