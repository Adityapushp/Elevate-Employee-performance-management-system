import test from 'node:test';
import assert from 'node:assert/strict';
import { calculateProgress, weightedProgress, confidenceForProgress } from '../src/services/performance.js';

test('increase metric progress is derived from baseline and target', () => {
  assert.equal(calculateProgress({baseline: 10, target: 30, current: 20, direction: 'increase'}), 50);
});
test('decrease metric progress treats lower values as better', () => {
  assert.equal(calculateProgress({baseline: 100, target: 20, current: 60, direction: 'decrease'}), 50);
});
test('weighted goal progress reconciles key result weights', () => {
  assert.equal(weightedProgress([{weight: 0.25, scoring_progress_pct: 40}, {weight: 0.75, scoring_progress_pct: 80}]), 70);
});
test('zero denominator is rejected', () => {
  assert.throws(() => calculateProgress({baseline: 10, target: 10, current: 10}), /different/);
});
test('confidence uses documented progress-to-expected thresholds', () => {
  assert.equal(confidenceForProgress(95, 100), 'on_track');
  assert.equal(confidenceForProgress(70, 100), 'at_risk');
  assert.equal(confidenceForProgress(40, 100), 'off_track');
});
