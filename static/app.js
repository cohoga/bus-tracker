// Auto-refresh every 30 seconds
setTimeout(function() {
    location.reload();
}, 30000);

// Optional: Add fade-in animation when page loads
document.addEventListener('DOMContentLoaded', function() {
    document.body.style.opacity = '0';
    setTimeout(function() {
        document.body.style.transition = 'opacity 0.3s';
        document.body.style.opacity = '1';
    }, 100);
});

// Optional: Show loading state when refreshing
window.addEventListener('beforeunload', function() {
    document.body.style.opacity = '0.5';
});