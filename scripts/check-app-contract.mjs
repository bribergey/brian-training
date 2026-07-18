import fs from 'node:fs';

const requiredContextFiles = [
  'AGENTS.md',
  'APP_SOURCES.md',
  'docs/project-context.md',
  'docs/infrastructure.md',
  'docs/operating-policy.md',
  'docs/qa-and-release.md',
  'docs/notion-workflow.md',
];
const forbiddenAppCopies = ['brian_master.html', 'brian_PRODUCTION.html'];

const missingContext = requiredContextFiles.filter(file => !fs.existsSync(file));
const obsoleteCopies = forbiddenAppCopies.filter(file => fs.existsSync(file));

if (missingContext.length || obsoleteCopies.length) {
  missingContext.forEach(file => console.error(`Required agent context is missing: ${file}`));
  obsoleteCopies.forEach(file => console.error(`Obsolete parallel app source exists: ${file}`));
  process.exit(1);
}

const workflowContracts = [
  ['.github/workflows/deploy-production.yml', [
    'cp index.html gh-pages/index.html',
    'cp app/index.html gh-pages/app/index.html',
  ]],
  ['.github/workflows/deploy-staging.yml', [
    'cp marketing_STAGING.html gh-pages/staging/index.html',
    'cp marketing_STAGING.html gh-pages/staging/home/index.html',
    'cp brian_STAGING.html gh-pages/staging/app/index.html',
  ]],
];

for (const [file, markers] of workflowContracts) {
  if (!fs.existsSync(file)) {
    console.error(`Deployment workflow is missing: ${file}`);
    process.exit(1);
  }
  const workflow = fs.readFileSync(file, 'utf8');
  for (const marker of markers) {
    if (!workflow.includes(marker)) {
      console.error(`Deployment workflow mapping is missing in ${file}: ${marker}`);
      process.exit(1);
    }
  }
}

const requestedFile = process.argv[2];
const appFile = requestedFile || (fs.existsSync('app/index.html') ? 'app/index.html' : 'brian_STAGING.html');

if (!fs.existsSync(appFile)) {
  console.error(`Canonical app source is missing: ${appFile}`);
  process.exit(1);
}

const html = fs.readFileSync(appFile, 'utf8');
const expected = [
  ['non-skipped workout count', 'function getCompletedWorkoutCount'],
  ['stable scheduled-workout selection', 'function getQueueSelectionKey'],
  ['saved workout selection', 'function rememberSelectedSession'],
  ['analytics lift filters', 'function setLiftFilter'],
  ['real analytics date labels', 'function formatShortDateLabel'],
  ['silent token refresh handling', "event === 'TOKEN_REFRESHED'"],
  ['scoped lift-card sharing', "querySelectorAll('#lift-tracker .lift-card')"],
  ['food photo upload support', 'const DAILY_PHOTO_LIMIT = 5'],
];

if (appFile === 'brian_STAGING.html') {
  expected.push(
    ['staging environment', "const ENV = 'staging'"],
  );
} else {
  expected.push(
    ['production environment', "const ENV = 'production'"],
    ['production photo storage prefix', "ENV === 'production' ? 'production' : 'staging'"],
  );
}

const missing = expected.filter(([, marker]) => !html.includes(marker));
if (missing.length) {
  missing.forEach(([name, marker]) => console.error(`Missing ${name}: ${marker}`));
  process.exit(1);
}

console.log(`App contract passed for ${appFile} (${expected.length} app checks plus repository source checks).`);
