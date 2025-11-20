/**
 * Validation Service
 * Uses GPT-4 to validate CVE matches against code
 */

import { AzureChatOpenAI } from '@langchain/openai';
import { ChatAnthropic } from '@langchain/anthropic';
import settings from '../config/settings';
import logger from '../utils/logger';

export interface ValidationParams {
  cveId: string;
  cveDescription: string;
  codeSnippet: string;
  filePath: string;
}

export interface ValidationResult {
  is_vulnerable: boolean;
  confidence: number;
  reasoning: string;
}

export class ValidationService {
  private llm: any;

  constructor() {
    // Use Azure OpenAI for validation if available, otherwise Anthropic
    if (settings.azureOpenAI.apiKey) {
      this.llm = new AzureChatOpenAI({
        azureOpenAIEndpoint: settings.azureOpenAI.endpoint,
        azureOpenAIApiKey: settings.azureOpenAI.apiKey,
        azureOpenAIApiVersion: settings.azureOpenAI.apiVersion,
        azureOpenAIApiDeploymentName: settings.azureOpenAI.model,
        temperature: 0.1,
        maxTokens: 2000,
      });
      logger.info('Validation Service initialized with Azure OpenAI');
    } else {
      this.llm = new ChatAnthropic({
        modelName: 'claude-3-7-sonnet-20250219',
        anthropicApiKey: settings.anthropic.apiKey,
        temperature: 0.1,
        maxTokens: 2000,
      });
      logger.info('Validation Service initialized with Anthropic Claude');
    }
  }

  /**
   * Validate if code is vulnerable to a specific CVE
   */
  async validateCVEMatch(params: ValidationParams): Promise<ValidationResult> {
    try {
      const { cveId, cveDescription, codeSnippet, filePath } = params;

      logger.info(`Validating ${cveId} against ${filePath}`);

      const prompt = `You are a security expert analyzing code for vulnerabilities.

CVE ID: ${cveId}
CVE Description: ${cveDescription}

File Path: ${filePath}
Code Snippet:
\`\`\`
${codeSnippet}
\`\`\`

TASK:
Analyze whether this code snippet is vulnerable to the CVE described above.

Consider:
1. Does the code pattern match the vulnerability?
2. Are proper security measures in place?
3. Is user input properly sanitized/validated?
4. Are there any mitigating factors?

Respond in JSON format:
{
  "is_vulnerable": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Detailed explanation"
}`;

      const response = await this.llm.invoke(prompt);
      const content = response.content;

      // Parse JSON response
      let result: ValidationResult;
      try {
        // Extract JSON from response (might be wrapped in markdown code blocks)
        const jsonMatch = content.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          result = JSON.parse(jsonMatch[0]);
        } else {
          throw new Error('No JSON found in response');
        }
      } catch (parseError) {
        // Fallback: parse from text
        const isVulnerable = content.toLowerCase().includes('vulnerable');
        result = {
          is_vulnerable: isVulnerable,
          confidence: 0.5,
          reasoning: content,
        };
      }

      logger.info(
        `✓ Validation complete: ${result.is_vulnerable ? 'VULNERABLE' : 'NOT VULNERABLE'} (${(
          result.confidence * 100
        ).toFixed(0)}%)`
      );

      return result;
    } catch (error: any) {
      logger.error(`Validation error: ${error.message}`);
      return {
        is_vulnerable: false,
        confidence: 0.0,
        reasoning: `Error during validation: ${error.message}`,
      };
    }
  }
}
