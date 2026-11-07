const REVIEW_MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ');
let trackedReviewSignature;
let lastReviewEditAt = null;

function trackReviewEdit(signature) {
  if (signature !== trackedReviewSignature) {
    trackedReviewSignature = signature;
    lastReviewEditAt = hasUnsavedChanges() ? new Date().toISOString() : null;
  }
  return lastReviewEditAt;
}

function reviewDateTime(value, dateOnly = false) {
  const date = dateOnly ? new Date(value + 'T00:00:00Z') : new Date(Date.parse(value) + 7 * 60 * 60 * 1000);
  const day = date.getUTCDate() + ' ' + REVIEW_MONTHS[date.getUTCMonth()] + ' ' + date.getUTCFullYear();
  if (dateOnly) return day + ' (time unavailable)';
  const pad = number => String(number).padStart(2, '0');
  return day + ', ' + pad(date.getUTCHours()) + ':' + pad(date.getUTCMinutes()) + ' ICT';
}

function updateReviewTimeline(review, dirty) {
  const edited = document.getElementById('review-edited');
  const approved = document.getElementById('review-approved');
  const instant = dirty ? lastReviewEditAt : review.editedAt;
  const day = dirty ? null : review.editedOn;
  edited.textContent = instant || day ? 'Last edited: ' + reviewDateTime(instant || day, !instant) : '';
  approved.textContent = !dirty && review.approvedAt ? 'Approved on: ' + reviewDateTime(review.approvedAt) : '';
}
