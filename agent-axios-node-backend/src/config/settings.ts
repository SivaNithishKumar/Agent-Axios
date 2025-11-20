/**
 * Configuration settings loaded from environment variables
 */

import dotenv from 'dotenv';
import path from 'path';

// Load environment variables
dotenv.config();

export interface Settings {
  // Server
  nodeEnv: string;
  port: number;
  frontendUrl: string;

  // Database
  databaseUrl: string;

  // Azure OpenAI
  azureOpenAI: {
    endpoint: string;
    apiKey: string;
    apiVersion: string;
    model: string;
  };

  // CVE Service
  cveService: {
    baseUrl: string;
  };

  // JWT
  jwt: {
    secret: string;
    expiresIn: string;
  };

  // Paths
  paths: {
    dataDir: string;
    cacheDir: string;
    faissDir: string;
    reportsDir: string;
  };

  // LangSmith (Optional)
  langsmith: {
    tracingEnabled: boolean;
    apiKey: string;
    project: string;
  };
}

const settings: Settings = {
  // Server
  nodeEnv: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.PORT || '3000', 10),
  frontendUrl: process.env.FRONTEND_URL || 'http://localhost:5173',

  // Database
  databaseUrl: process.env.DATABASE_URL || 'file:./prisma/dev.db',

  // Azure OpenAI
  azureOpenAI: {
    endpoint: process.env.AZURE_OPENAI_ENDPOINT || '',
    apiKey: process.env.AZURE_OPENAI_API_KEY || '',
    apiVersion: process.env.AZURE_OPENAI_API_VERSION || '2024-02-15-preview',
    model: process.env.AZURE_OPENAI_MODEL || 'gpt-4',
  },

  // CVE Service
  cveService: {
    baseUrl: process.env.CVE_SERVICE_BASE_URL || 'http://140.238.227.29:5000',
  },

  // JWT
  jwt: {
    secret: process.env.JWT_SECRET || 'change-this-secret',
    expiresIn: process.env.JWT_EXPIRES_IN || '7d',
  },

  // Paths
  paths: {
    dataDir: path.resolve(process.env.DATA_DIR || './data'),
    cacheDir: path.resolve(process.env.CACHE_DIR || './data/cache'),
    faissDir: path.resolve(process.env.FAISS_DIR || './data/faiss_indexes'),
    reportsDir: path.resolve(process.env.REPORTS_DIR || './data/reports'),
  },

  // LangSmith
  langsmith: {
    tracingEnabled: process.env.LANGCHAIN_TRACING_V2 === 'true',
    apiKey: process.env.LANGCHAIN_API_KEY || '',
    project: process.env.LANGCHAIN_PROJECT || 'agent-axios-node',
  },
};

// Validation
export function validateSettings(): void {
  const errors: string[] = [];

  // Check critical settings
  if (!settings.databaseUrl) {
    errors.push('DATABASE_URL is required');
  }

  if (!settings.azureOpenAI.apiKey) {
    errors.push('AZURE_OPENAI_API_KEY is required');
  }

  if (!settings.azureOpenAI.endpoint) {
    errors.push('AZURE_OPENAI_ENDPOINT is required');
  }

  if (!settings.jwt.secret || settings.jwt.secret === 'change-this-secret') {
    console.warn('⚠️  WARNING: Using default JWT_SECRET. Change this in production!');
  }

  if (errors.length > 0) {
    throw new Error(`Configuration errors:\n${errors.join('\n')}`);
  }

  console.log('✅ Configuration validated successfully');
}

export default settings;
