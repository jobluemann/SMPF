<?php
/**
 * SMPF Admin Renderer
 *
 * Renders all admin pages for the SMPF Core plugin.
 *
 * @package SMPF_Core
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

/**
 * Class SMPF_Admin
 */
class SMPF_Admin {

    /**
     * Render the main dashboard page.
     */
    public static function render_dashboard() {
        $core = SMPF_Core::get_instance();
        $status = $core->api->get( '/api/analytics/connections' );
        $overview = $core->api->get( '/api/analytics/overview' );
        include SMPF_CORE_PLUGIN_DIR . 'templates/dashboard.php';
    }

    /**
     * Render the settings page.
     */
    public static function render_settings() {
        include SMPF_CORE_PLUGIN_DIR . 'templates/settings.php';
    }
}
