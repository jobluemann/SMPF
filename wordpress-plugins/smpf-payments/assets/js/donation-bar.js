/**
 * SMPF Donation Bar Frontend Script
 *
 * Handles timed appear/disappear of the floating donation banner.
 */
(function () {
    'use strict';

    var config = window.smpfDonationConfig || {};
    var bar = document.getElementById('smpf-donation-bar');
    if (!bar) return;

    var intervalMinutes = parseFloat(config.interval) || 5;
    var intervalMs = intervalMinutes * 60 * 1000;
    var showDurationMs = 15000; // Banner stays visible for 15 seconds
    var isActive = false;
    var timerId = null;

    // Check if user dismissed this session
    if (sessionStorage.getItem('smpf_donation_dismissed') === '1') {
        return;
    }

    function showBar() {
        if (!bar || sessionStorage.getItem('smpf_donation_dismissed') === '1') return;
        bar.classList.add('active');
        isActive = true;

        // Auto-hide after showDuration
        clearTimeout(timerId);
        timerId = setTimeout(function () {
            hideBar();
        }, showDurationMs);
    }

    function hideBar() {
        if (!bar) return;
        bar.classList.remove('active');
        isActive = false;

        // Schedule next appearance
        clearTimeout(timerId);
        timerId = setTimeout(function () {
            showBar();
        }, intervalMs);
    }

    // Close button handler
    var closeBtn = document.getElementById('smpf-donation-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function (e) {
            e.preventDefault();
            bar.classList.remove('active');
            sessionStorage.setItem('smpf_donation_dismissed', '1');
            clearTimeout(timerId);
        });
    }

    // Initial delay before first show (random 3-8 seconds so it feels natural)
    var initialDelay = Math.floor(Math.random() * 5000) + 3000;
    setTimeout(function () {
        showBar();
    }, initialDelay);
})();
