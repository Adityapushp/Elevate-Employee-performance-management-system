export function calculateProgress({ baseline, target, current, direction = 'increase' }) {
  const denominator = direction === 'decrease' ? baseline - target : target - baseline;
  if (denominator === 0) throw new Error('Baseline and target must be different.');
  const raw = direction === 'decrease' ? ((baseline - current) / denominator) * 100 : ((current - baseline) / denominator) * 100;
  return Math.max(0, raw);
}
export function weightedProgress(keyResults) {
  if (!keyResults.length) return 0;
  const totalWeight = keyResults.reduce((sum, kr) => sum + Number(kr.weight), 0);
  if (totalWeight <= 0) throw new Error('Key-result weights must sum to a positive value.');
  return keyResults.reduce((sum, kr) => sum + Number(kr.weight) * Number(kr.scoring_progress_pct), 0) / totalWeight;
}
export function confidenceForProgress(progress, expected) {
  const ratio = expected > 0 ? progress / expected : 1;
  return ratio >= 0.9 ? 'on_track' : ratio >= 0.6 ? 'at_risk' : 'off_track';
}
