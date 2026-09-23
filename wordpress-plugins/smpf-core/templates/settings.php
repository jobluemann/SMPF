<?php
/**
 * SMPF Settings Template
 *
 * @package SMPF_Core
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}
?>
<div class="wrap smpf-wrap">
    <h1><?php esc_html_e( 'SMPF Settings', 'smpf-core' ); ?></h1>

    <div class="smpf-card">
        <h2><?php esc_html_e( 'Backend Connection', 'smpf-core' ); ?></h2>
        <form method="post" action="options.php">
            <?php settings_fields( 'smpf_core_settings' ); ?>
            <?php do_settings_sections( 'smpf_core_settings' ); ?>

            <div class="smpf-form-group">
                <label for="smpf_backend_url"><?php esc_html_e( 'Backend URL', 'smpf-core' ); ?></label>
                <input type="url" id="smpf_backend_url" name="smpf_backend_url"
                       value="<?php echo esc_attr( get_option( 'smpf_backend_url', 'http://127.0.0.1:8000' ) ); ?>"
                       class="regular-text">
                <p class="description">
                    <?php esc_html_e( 'The URL of your SMPF FastAPI backend. Default: http://127.0.0.1:8000', 'smpf-core' ); ?>
                </p>
            </div>

            <div class="smpf-form-group">
                <label for="smpf_api_key"><?php esc_html_e( 'API Key (optional)', 'smpf-core' ); ?></label>
                <input type="password" id="smpf_api_key" name="smpf_api_key"
                       value="<?php echo esc_attr( get_option( 'smpf_api_key', '' ) ); ?>"
                       class="regular-text">
                <p class="description">
                    <?php esc_html_e( 'If your backend requires an API key, enter it here.', 'smpf-core' ); ?>
                </p>
            </div>

            <div class="smpf-form-group">
                <label>
                    <input type="checkbox" name="smpf_debug_mode" value="1" <?php checked( get_option( 'smpf_debug_mode', false ) ); ?>>
                    <?php esc_html_e( 'Enable debug mode', 'smpf-core' ); ?>
                </label>
                <p class="description">
                    <?php esc_html_e( 'Logs API requests to the WordPress debug log.', 'smpf-core' ); ?>
                </p>
            </div>

            <?php submit_button(); ?>
        </form>

        <hr>

        <h3><?php esc_html_e( 'Test Connection', 'smpf-core' ); ?></h3>
        <p>
            <button id="smpf-test-connection" class="smpf-btn"><?php esc_html_e( 'Test Connection', 'smpf-core' ); ?></button>
        </p>
        <div id="smpf-connection-result" class="smpf-alert" style="display:none;"></div>
    </div>
</div>
