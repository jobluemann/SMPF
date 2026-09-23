<?php
/**
 * Plugin Name: SMPF Analytics
 * Plugin URI: https://finwatchpro.net
 * Description: Analytics and reporting viewer for SMPF. Requires SMPF Core.
 * Version: 1.0.0
 * Author: Jo Bluemann
 * License: GPL-2.0+
 * Text Domain: smpf-analytics
 *
 * @package SMPF_Analytics
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

add_action( 'admin_init', function() {
    if ( ! class_exists( 'SMPF_Core' ) ) {
        deactivate_plugins( plugin_basename( __FILE__ ) );
        add_action( 'admin_notices', function() {
            echo '<div class="error"><p><strong>SMPF Analytics:</strong> ' . esc_html__( 'SMPF Core must be active.', 'smpf-analytics' ) . '</p></div>';
        });
    }
});

class SMPF_Analytics {
    private static $instance = null;
    public static function get_instance() {
        if ( null === self::$instance ) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    private function __construct() {
        add_action( 'admin_menu', array( $this, 'register_menu' ) );
    }
    public function register_menu() {
        add_submenu_page(
            'smpf-dashboard',
            __( 'Analytics', 'smpf-analytics' ),
            __( 'Analytics', 'smpf-analytics' ),
            'manage_options',
            'smpf-analytics',
            array( $this, 'render_page' )
        );
    }
    public function render_page() {
        $core = SMPF_Core::get_instance();
        $overview = $core->api->get( '/api/analytics/overview' );
        $content  = $core->api->get( '/api/analytics/content-history' );
        $log      = $core->api->get( '/api/post-log', array( 'limit' => 20 ) );
        include plugin_dir_path( __FILE__ ) . 'templates/analytics.php';
    }
}
add_action( 'plugins_loaded', array( 'SMPF_Analytics', 'get_instance' ) );
