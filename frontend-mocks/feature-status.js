// Feature Status Indicators for LLMplate Mocks
// Based on PROJECT_STATUS.md - 95% Complete

const FEATURE_STATUS = {
  // Authentication - 100% Complete
  auth: {
    emailLogin: { ready: true, status: 'production', api: '/auth/login' },
    emailRegister: { ready: true, status: 'production', api: '/auth/register' },
    googleOAuth: { ready: true, status: 'production', api: '/auth/oauth/google' },
    githubOAuth: { ready: true, status: 'production', api: '/auth/oauth/github' },
    jwtTokens: { ready: true, status: 'production', api: '/auth/refresh' },
    userProfile: { ready: true, status: 'production', api: '/auth/me' }
  },
  
  // Template System - 100% Complete
  templates: {
    createTemplate: { ready: true, status: 'production', api: '/templates' },
    listTemplates: { ready: true, status: 'production', api: '/templates' },
    updateTemplate: { ready: true, status: 'production', api: '/templates/{id}' },
    deleteTemplate: { ready: true, status: 'production', api: '/templates/{id}' },
    validateTemplate: { ready: true, status: 'production', api: '/templates/{id}/validate' },
    previewTemplate: { ready: true, status: 'production', api: '/templates/{id}/preview' },
    publicTemplates: { ready: true, status: 'production', api: '/templates/public' },
    importExport: { ready: true, status: 'production', api: '/templates/import' }
  },
  
  // Generation System - 90% Complete
  generation: {
    startGeneration: { ready: true, status: 'production', api: '/generate/start' },
    checkStatus: { ready: true, status: 'production', api: '/generate/{id}/status' },
    getResult: { ready: true, status: 'production', api: '/generate/{id}/result' },
    cancelGeneration: { ready: true, status: 'production', api: '/generate/{id}/cancel' },
    generationHistory: { ready: true, status: 'production', api: '/generate/history' },
    batchGeneration: { ready: true, status: 'testing', api: '/generate/batch' },
    progressTracking: { ready: true, status: 'production', api: 'included in status' },
    costCalculation: { ready: true, status: 'production', api: 'included in result' }
  },
  
  // Export System - 100% Complete
  export: {
    exportJSON: { ready: true, status: 'production', api: '/generate/{id}/export?format=json' },
    exportCSV: { ready: true, status: 'production', api: '/generate/{id}/export?format=csv' },
    exportPDF: { ready: true, status: 'production', api: '/generate/{id}/export?format=pdf' },
    exportExcel: { ready: true, status: 'production', api: '/generate/{id}/export?format=xlsx' },
    exportMarkdown: { ready: true, status: 'production', api: '/generate/{id}/export?format=md' },
    exportHTML: { ready: true, status: 'production', api: '/generate/{id}/export?format=html' },
    exportXML: { ready: true, status: 'production', api: '/generate/{id}/export?format=xml' },
    exportTXT: { ready: true, status: 'production', api: '/generate/{id}/export?format=txt' }
  },
  
  // Provider System - 100% Complete
  providers: {
    listProviders: { ready: true, status: 'production', api: '/providers' },
    listModels: { ready: true, status: 'production', api: '/providers/models' },
    modelFiltering: { ready: true, status: 'production', api: '/providers/models?free=true' },
    providerHealth: { ready: true, status: 'production', api: '/providers/{provider}/health' },
    openRouter: { ready: true, status: 'production', api: 'OpenRouter integration' },
    ollama: { ready: true, status: 'production', api: 'Ollama integration' },
    pricingInfo: { ready: true, status: 'production', api: 'included in model list' }
  },
  
  // Planned/In Development Features
  planned: {
    visualBuilder: { ready: false, status: 'planned', note: 'Visual template builder UI' },
    realtimeUpdates: { ready: false, status: 'development', note: 'WebSocket support' },
    resultCaching: { ready: false, status: 'planned', note: 'Generation result caching' },
    fullCelery: { ready: false, status: 'development', note: 'Full Celery/Redis integration' },
    fileUploads: { ready: false, status: 'planned', note: 'File upload for variables' },
    templateVersioning: { ready: false, status: 'planned', note: 'Version control for templates' },
    advancedSearch: { ready: false, status: 'planned', note: 'Advanced template search' },
    rateLimiting: { ready: false, status: 'planned', note: 'API rate limiting' }
  }
};

// Helper function to create status badge HTML
function createStatusBadge(feature) {
  const statusColors = {
    production: '#4CAF50',
    testing: '#FF9800',
    development: '#2196F3',
    planned: '#9E9E9E'
  };
  
  const color = statusColors[feature.status] || '#9E9E9E';
  const icon = feature.ready ? '✓' : '⏳';
  const text = feature.ready ? 'Ready' : feature.status.charAt(0).toUpperCase() + feature.status.slice(1);
  
  return `
    <span class="feature-status-badge" style="
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 4px 8px;
      background: ${color}20;
      color: ${color};
      border: 1px solid ${color}40;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 500;
      cursor: help;
    " title="${feature.api || feature.note || 'Feature status'}">
      <span>${icon}</span>
      <span>${text}</span>
    </span>
  `;
}

// Helper function to create feature status indicator
function createFeatureIndicator(featureKey, compact = false) {
  const parts = featureKey.split('.');
  let feature = FEATURE_STATUS;
  
  for (const part of parts) {
    feature = feature[part];
    if (!feature) return '';
  }
  
  if (compact) {
    return feature.ready ? 
      '<span style="color: #4CAF50; font-size: 16px;" title="Feature ready">✓</span>' : 
      '<span style="color: #FF9800; font-size: 16px;" title="In development">⏳</span>';
  }
  
  return createStatusBadge(feature);
}

// CSS styles for feature status components
const FEATURE_STATUS_STYLES = `
  <style>
    .feature-status-container {
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: white;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 16px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      max-width: 320px;
      z-index: 1000;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }
    
    .feature-status-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      font-weight: 600;
      font-size: 14px;
    }
    
    .feature-status-close {
      cursor: pointer;
      font-size: 20px;
      line-height: 1;
      color: #999;
      background: none;
      border: none;
      padding: 0;
    }
    
    .feature-status-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      font-size: 13px;
    }
    
    .feature-status-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }
    
    .feature-status-note {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid #e0e0e0;
      font-size: 12px;
      color: #666;
      line-height: 1.4;
    }
    
    .feature-inline-indicator {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      margin-left: 8px;
      font-size: 12px;
      color: #666;
    }
    
    @media (max-width: 640px) {
      .feature-status-container {
        bottom: 10px;
        right: 10px;
        left: 10px;
        max-width: none;
      }
    }
  </style>
`;

// Component to show feature status for current page
function createFeatureStatusPanel(features) {
  const items = features.map(f => {
    const [name, key] = Array.isArray(f) ? f : [f, f];
    const parts = key.split('.');
    let feature = FEATURE_STATUS;
    
    for (const part of parts) {
      feature = feature[part];
      if (!feature) break;
    }
    
    if (!feature) return '';
    
    return `
      <div class="feature-status-item">
        <span>${name}</span>
        ${createStatusBadge(feature)}
      </div>
    `;
  }).join('');
  
  return `
    ${FEATURE_STATUS_STYLES}
    <div class="feature-status-container" id="featureStatusPanel">
      <div class="feature-status-header">
        <span>🚀 Feature Status</span>
        <button class="feature-status-close" onclick="document.getElementById('featureStatusPanel').style.display='none'">×</button>
      </div>
      <div class="feature-status-list">
        ${items}
      </div>
      <div class="feature-status-note">
        <strong>Backend Progress: 95%</strong><br>
        Most features are production-ready. UI components marked as "Planned" represent frontend-only features.
      </div>
    </div>
  `;
}

// Auto-inject feature status panel if script is loaded
if (typeof document !== 'undefined' && document.body) {
  document.addEventListener('DOMContentLoaded', function() {
    // Only inject if not already present
    if (!document.getElementById('featureStatusPanel')) {
      const statusHTML = createFeatureStatusPanel([]);
      document.body.insertAdjacentHTML('beforeend', statusHTML);
    }
  });
}