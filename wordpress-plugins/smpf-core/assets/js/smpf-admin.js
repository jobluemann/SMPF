/**
 * SMPF Admin JavaScript
 */
(function($) {
    'use strict';

    $(document).ready(function() {
        // Test backend connection button.
        $('#smpf-test-connection').on('click', function(e) {
            e.preventDefault();
            var $btn = $(this);
            var $result = $('#smpf-connection-result');
            $btn.prop('disabled', true).text('Testing…');
            $result.hide();

            $.post(smpf_ajax.ajax_url, {
                action: 'smpf_test_connection',
                nonce: smpf_ajax.nonce
            }, function(response) {
                if (response.success) {
                    $result.removeClass('smpf-alert-error').addClass('smpf-alert-success')
                        .text(response.data.message).show();
                } else {
                    $result.removeClass('smpf-alert-success').addClass('smpf-alert-error')
                        .text('Error: ' + response.data).show();
                }
            }).fail(function() {
                $result.removeClass('smpf-alert-success').addClass('smpf-alert-error')
                    .text('Request failed. Is the backend running?').show();
            }).always(function() {
                $btn.prop('disabled', false).text('Test Connection');
            });
        });

        // Refresh platform status on dashboard.
        $('#smpf-refresh-status').on('click', function(e) {
            e.preventDefault();
            var $btn = $(this);
            $btn.prop('disabled', true).text('Refreshing…');

            $.post(smpf_ajax.ajax_url, {
                action: 'smpf_fetch_status',
                nonce: smpf_ajax.nonce
            }, function(response) {
                if (response.success && response.data.platforms) {
                    renderPlatformStatus(response.data.platforms);
                }
            }).always(function() {
                $btn.prop('disabled', false).text('Refresh Status');
            });
        });

        function renderPlatformStatus(platforms) {
            var $grid = $('.smpf-status-grid');
            $grid.empty();
            $.each(platforms, function(i, p) {
                var isConnected = p.status === 'connected';
                var $item = $('<div class="smpf-status-item"></div>')
                    .toggleClass('connected', isConnected);
                $item.append('<span class="platform-name">' + escapeHtml(p.name) + '</span>');
                $item.append('<span class="platform-status">' + (isConnected ? 'Connected' : 'Not connected') + '</span>');
                $grid.append($item);
            });
        }

        function escapeHtml(text) {
            var div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    });
})(jQuery);
