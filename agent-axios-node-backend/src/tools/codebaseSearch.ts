/**
 * Codebase Search Tool
 * Semantic search using FAISS indexing
 */

import { tool } from '@langchain/core/tools';
import { z } from 'zod';
import { LangGraphRunnableConfig } from '@langchain/langgraph';
import { ConversationSession } from '../agent/ConversationSession';
import logger from '../utils/logger';

// This will be implemented with the CodebaseIndexingService
let indexingService: any = null;

export function setIndexingService(service: any): void {
  indexingService = service;
}

export const createSearchCodebaseSemanticallTool = (conversationSession: ConversationSession) => {
  return tool(
    async (
      { query, limit = 10, minScore = 0.5 }: { query: string; limit?: number; minScore?: number },
      config?: LangGraphRunnableConfig
    ) => {
      try {
        logger.info(`Semantic search: ${query.substring(0, 100)}`);
        config?.writer?.('🔍 Searching codebase semantically...');

        if (!indexingService) {
          logger.warn('Indexing service not initialized');
          return JSON.stringify({
            error: 'Codebase indexing service not initialized. Build index first.',
            success: false,
            results: [],
          });
        }

        config?.writer?.(`🔎 Searching for: "${query.substring(0, 50)}..."`);

        // Perform semantic search
        const results = await indexingService.search(query, limit, minScore);

        logger.info(`✓ Found ${results.length} relevant code chunks`);
        config?.writer?.(`✅ Found ${results.length} relevant code chunks`);

        return JSON.stringify({
          success: true,
          results,
          query,
          total_found: results.length,
        });
      } catch (error: any) {
        logger.error(`✗ Error in semantic search: ${error.message}`);
        config?.writer?.(`❌ Error: ${error.message}`);
        return JSON.stringify({
          error: error.message,
          success: false,
          results: [],
        });
      }
    },
    {
      name: 'search_codebase_semantically',
      description: `Search the codebase using semantic similarity to find relevant code chunks.

WHEN TO USE:
- To find code patterns that may be vulnerable
- To locate specific functionality in the codebase
- To identify areas of interest for vulnerability analysis

INPUT:
{
  "query": "SQL injection vulnerability in user input",
  "limit": 10,        // optional, max results
  "minScore": 0.5     // optional, minimum similarity score
}

RETURNS:
JSON object with:
- results: Array of relevant code chunks with similarity scores
- total_found: Number of results found

This tool uses FAISS-based semantic search to find code similar to your query.
Build the codebase index first using the indexing service.`,
      schema: z.object({
        query: z.string().min(1).describe('Search query describing what to find'),
        limit: z.number().nullable().optional().describe('Maximum number of results (default: 10)'),
        minScore: z.number().nullable().optional().describe('Minimum similarity score 0-1 (default: 0.5)'),
      }),
    }
  );
};
