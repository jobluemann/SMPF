<?php
/**
 * SMPF Post Composer Template
 *
 * @package SMPF_Post
 */
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}
$core = SMPF_Core::get_instance();
$platforms_data = $core->api->get( '/api/analytics/connections' );
$platforms = ( ! is_wp_error( $platforms_data ) && isset( $platforms_data['platforms'] ) ) ? $platforms_data['platforms'] : array();
?>
<div class="wrap smpf-wrap">
    <h1><?php esc_html_e( 'Create Post', 'smpf-post' ); ?></h1>

    <div class="smpf-card">
        <h2><?php esc_html_e( 'Post Content', 'smpf-post' ); ?></h2>

        <div class="smpf-form-group">
            <label for="smpf-post-text"><?php esc_html_e( 'Post Text', 'smpf-post' ); ?></label>
            <textarea id="smpf-post-text" rows="5" class="large-text" placeholder="<?php esc_attr_e( 'What do you want to say?', 'smpf-post' ); ?>"></textarea>
        </div>

        <div class="smpf-form-group">
            <label for="smpf-post-image"><?php esc_html_e( 'Image URL (optional, required for Instagram)', 'smpf-post' ); ?></label>
            <input type="url" id="smpf-post-image" class="regular-text" placeholder="https://example.com/image.jpg">
        </div>

        <h3><?php esc_html_e( 'Select Platforms', 'smpf-post' ); ?></h3>
        <div id="smpf-platforms-list" style="margin-bottom:16px;">
            <?php foreach ( $platforms as $p ) : ?>
                <label style="display:inline-flex;align-items:center;margin-right:16px;cursor:pointer;">
                    <input type="checkbox" class="smpf-platform-cb" value="<?php echo esc_attr( strtolower( $p['name'] ) ); ?>"
                        <?php disabled( 'connected' !== $p['status'] ); ?>
                        <?php checked( 'connected' === $p['status'] ); ?>>
                    <?php echo esc_html( $p['name'] ); ?>
                    <?php if ( 'connected' !== $p['status'] ) : ?>
                        <span style="color:#d63638;font-size:0.8em;margin-left:4px;">(<?php esc_html_e( 'not connected', 'smpf-post' ); ?>)</span>
                    <?php endif; ?>
                </label>
            <?php endforeach; ?>
        </div>

        <p>
            <button id="smpf-submit-post" class="smpf-btn smpf-btn-success"><?php esc_html_e( 'Post Now', 'smpf-post' ); ?></button>
        </p>

        <div id="smpf-post-result" class="smpf-alert" style="display:none;"></div>
    </div>
</div>

<script>
(function($) {
    $('#smpf-submit-post').on('click', function(e) {
        e.preventDefault();
        var $btn = $(this), $result = $('#smpf-post-result');
        var text = $('#smpf-post-text').val().trim();
        var imageUrl = $('#smpf-post-image').val().trim();
        var platforms = [];
        $('.smpf-platform-cb:checked').each(function() {
            platforms.push($(this).val());
        });

        if (!text) { alert('<?php echo esc_js( __( 'Enter post text.', 'smpf-post' ) ); ?>'); return; }
        if (!platforms.length) { alert('<?php echo esc_js( __( 'Select at least one platform.', 'smpf-post' ) ); ?>'); return; }

        $btn.prop('disabled', true).text('<?php echo esc_js( __( 'Posting…', 'smpf-post' ) ); ?>');
        $result.hide();

        $.post(smpf_ajax.ajax_url, {
            action: 'smpf_create_post',
            nonce: smpf_ajax.nonce,
            text: text,
            platforms: platforms,
            image_url: imageUrl
        }, function(response) {
            if (response.success) {
                $result.removeClass('smpf-alert-error').addClass('smpf-alert-success').html(
                    '<strong><?php echo esc_js( __( 'Posted!', 'smpf-post' ) ); ?></strong><br>' +
                    JSON.stringify(response.data.results, null, 2)
                ).show();
            } else {
                $result.removeClass('smpf-alert-success').addClass('smpf-alert-error')
                    .text('<?php echo esc_js( __( 'Error:', 'smpf-post' ) ); ?> ' + response.data).show();
            }
        }).fail(function() {
            $result.removeClass('smpf-alert-success').addClass('smpf-alert-error')
                .text('<?php echo esc_js( __( 'Request failed.', 'smpf-post' ) ); ?>').show();
        }).always(function() {
            $btn.prop('disabled', false).text('<?php echo esc_js( __( 'Post Now', 'smpf-post' ) ); ?>');
        });
    });
})(jQuery);
</script>
