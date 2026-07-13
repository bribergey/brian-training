import fs from 'node:fs';

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
];

if (appFile === 'brian_STAGING.html') {
  expected.push(
    ['staging environment', "const ENV = 'staging'"],
    ['food photo upload support', 'const DAILY_PHOTO_LIMIT = 5'],
  );
}

const missing = expected.filter(([, marker]) => !html.includes(marker));
if (missing.length) {
  missing.forEach(([name, marker]) => console.error(`Missing ${name}: ${marker}`));
  process.exit(1);
}

console.log(`App contract passed for ${appFile} (${expected.length} checks).`);
