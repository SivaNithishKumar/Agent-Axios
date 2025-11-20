/**
 * Global context management for tools
 * Allows tools to share repository and analysis context
 */

interface RepoContext {
  repoPath: string;
  repoUrl: string;
}

interface AnalysisContext {
  analysisId: number;
}

let currentRepoContext: RepoContext | null = null;
let currentAnalysisContext: AnalysisContext | null = null;

/**
 * Set repository context for all tools
 */
export function setRepoContext(repoPath: string, repoUrl: string): void {
  currentRepoContext = { repoPath, repoUrl };
}

/**
 * Get current repository context
 */
export function getRepoContext(): RepoContext | null {
  return currentRepoContext;
}

/**
 * Clear repository context
 */
export function clearRepoContext(): void {
  currentRepoContext = null;
}

/**
 * Set analysis context (analysis ID from database)
 */
export function setAnalysisContext(analysisId: number): void {
  currentAnalysisContext = { analysisId };
}

/**
 * Get current analysis context
 */
export function getAnalysisContext(): number | null {
  return currentAnalysisContext?.analysisId || null;
}

/**
 * Clear analysis context
 */
export function clearAnalysisContext(): void {
  currentAnalysisContext = null;
}

/**
 * Clear all contexts
 */
export function clearAllContexts(): void {
  currentRepoContext = null;
  currentAnalysisContext = null;
}

/**
 * Resolve file path relative to current repo context
 */
export function resolveRepoPath(filePath: string): string {
  if (!currentRepoContext) {
    return filePath;
  }

  // If path is absolute, return as is
  if (filePath.startsWith('/')) {
    return filePath;
  }

  // Otherwise, resolve relative to repo path
  return `${currentRepoContext.repoPath}/${filePath}`;
}
