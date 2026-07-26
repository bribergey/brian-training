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
  ['food photo upload support', 'const DAILY_PHOTO_LIMIT = 5'],
  ['three-stage Daily Log calendar', 'function dailyLogStage'],
  ['Daily Log sleep stepper', "stepperHtml('daily-sleep-duration'"],
  ['Daily Log work-hours stepper', "stepperHtml('daily-work-hours'"],
  ['Daily Log empty-food filter', 'filter(entry => entry.description || entry.photos.length)'],
  ['brick favicon', '<link rel="icon" type="image/svg+xml"'],
  ['food-complete calendar marker', 'function nutritionFoodLogIsAnalyzedComplete'],
  ['logged extra-activity target', 'function nutritionExtraActivityEstimate'],
  ['stool nutrition analytics', 'function nutritionStoolMetricInsight'],
  ['Daily notes analytics', 'function nutritionNoteThemeInsights'],
  ['button success feedback', 'function dailyFlashButton'],
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

const forbidden = [
  ['Daily Log mood scale', "dailyScaleMarkup('mood'"],
  ['Daily Log mood payload', "mood: scaleValue('mood')"],
  ['obsolete Daily Log calendar footer', 'daily-calendar-footer'],
];
const present = forbidden.filter(([, marker]) => html.includes(marker));
if (present.length) {
  present.forEach(([name, marker]) => console.error(`Obsolete ${name}: ${marker}`));
  process.exit(1);
}

console.log(`App contract passed for ${appFile} (${expected.length} required, ${forbidden.length} forbidden checks).`);
