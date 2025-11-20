/**
 * Build FAISS index tool for semantic code search
 */

import { tool } from '@langchain/core/tools';
import { z } from 'zod';
import { LangGraphRunnableConfig } from '@langchain/langgraph';
import logger from '../utils/logger';
import { getRepoContext, getAnalysisContext } from './context';
import { CodebaseIndexingService } from '../services/CodebaseIndexingService';

export const createBuildIndexTool = () => {
  return tool(
    async (
      { repoPath }: { repoPath?: string },
      config?: LangGraphRunnableConfig
    ) => {
      try {
        const context = getRepoContext();
        const analysisId = getAnalysisContext();
        
        const actualRepoPath = repoPath || context?.repoPath;

        if (!actualRepoPath) {
          logger.error('No repository path available');
          return JSON.stringify({
            success: false,
            error: 'No repository cloned yet. Clone a repository first using clone_repository tool.',
          });
        }

        logger.info(`Building FAISS index for: ${actualRepoPath}`);
        config?.writer?.(`🔨 Building semantic search index...`);

        const indexingService = new CodebaseIndexingService();
        
        config?.writer?.(`📊 Analyzing code files...`);
        await indexingService.buildIndex(actualRepoPath, analysisId || 0);

        logger.info(`✓ FAISS index built successfully`);
        config?.writer?.(`✅ Index built! Ready for semantic search.`);

        return JSON.stringify({
          success: true,
          repoPath: actualRepoPath,
          message: 'FAISS index built successfully. You can now use search_codebase_semantically tool.',
        });
      } catch (error: any) {
        logger.error(`✗ Error building index: ${error.message}`);
        config?.writer?.(`❌ Error: ${error.message}`);
        return JSON.stringify({
          success: false,
          error: error.message,
        });
      }
    },
    {
      name: 'build_codebase_index',
      description: `Build a FAISS semantic search index for the cloned repository.

WHEN TO USE:
- AFTER cloning a repository with clone_repository
- BEFORE using search_codebase_semantically tool
- Required for semantic code analysis and vulnerability pattern matching

WORKFLOW POSITION:
1. clone_repository (FIRST)
2. build_codebase_index (SECOND) ← You are here
3. analyze_repository_structure (optional)
4. search_codebase_semantically (requires this index)

WHAT IT DOES:
- Scans all code files in the repository
- Generates embeddings for code chunks
- Creates a FAISS index for fast semantic search
- Enables finding vulnerable code patterns

INPUT:
{
  "repoPath": "/path/to/cloned/repo"  // optional, uses context if not provided
}

RETURNS:
JSON object with:
- success: Boolean
- repoPath: Path to indexed repository
- message: Status message

NOTE: This may take 30-60 seconds for large repositories.`,
      schema: z.object({
        repoPath: z.string().nullable().optional().describe('Path to repository (uses context if omitted)'),
      }),
    }
  );
};
