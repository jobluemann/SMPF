<?php
/**
 * Plugin Name: SMPF Core
 * Plugin URI: https://finwatchpro.net
 * Description: Core API client and admin framework for the Social Media Platform Framework. Required by all other SMPF plugins.
 * Version: 1.0.0
 * Author: Jo Bluemann
 * Author URI: https://www.youtube.com/@jobluemann
 * License: GPL-2.0+
 * License URI: http://www.gnu.org/licenses/gpl-2.0.txt
 * Text Domain: smpf-core
 * Domain Path: /languages
 *
 * @package SMPF_Core
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

// Plugin constants.
define( 'SMPF_CORE_VERSION', '1.0.0' );
define( 'SMPF_CORE_PLUGIN_DIR', plugin_dir_path( __FILE__ ) );
define( 'SMPF_CORE_PLUGIN_URL', plugin_dir_url( __FILE__ ) );

// Require core classes.
require_once SMPF_CORE_PLUGIN_DIR . 'includes/class-smpf-api-client.php';
require_once SMPF_CORE_PLUGIN_DIR . 'includes/class-smpf-admin.php';

/**
 * Main SMPF Core class.
 *
 * Handles activation, settings, and bootstraps the admin interface.
 */
class SMPF_Core {

    /**
     * Singleton instance.
     *
     * @var SMPF_Core|null
     */
    private static $instance = null;

    /**
     * API client instance.
     *
     * @var SMPF_API_Client|null
     */
    public $api = null;

    /**
     * Get singleton instance.
     *
     * @return SMPF_Core
     */
    public static function get_instance() {
        if ( null === self::$instance ) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    /**
     * Constructor.
     */
    private function __construct() {
        $this->api = new SMPF_API_Client();
        add_action( 'admin_menu', array( $this, 'register_admin_menu' ) );
        add_action( 'admin_init', array( $this, 'register_settings' ) );
        add_action( 'admin_enqueue_scripts', array( $this, 'enqueue_assets' ) );
        add_action( 'wp_ajax_smpf_test_connection', array( $this, 'ajax_test_connection' ) );
        add_action( 'wp_ajax_smpf_fetch_status', array( $this, 'ajax_fetch_status' ) );
    }

    /**
     * Register the top-level admin menu.
     */
    public function register_admin_menu() {
        add_menu_page(
            __( 'SMPF Dashboard', 'smpf-core' ),
            __( 'SMPF', 'smpf-core' ),
            'manage_options',
            'smpf-dashboard',
            array( 'SMPF_Admin', 'render_dashboard' ),
            'dashicons-share-alt2',
            30
        );

        add_submenu_page(
            'smpf-dashboard',
            __( 'SMPF Dashboard', 'smpf-core' ),
            __( 'Dashboard', 'smpf-core' ),
            'manage_options',
            'smpf-dashboard',
            array( 'SMPF_Admin', 'render_dashboard' )
        );

        add_submenu_page(
            'smpf-dashboard',
            __( 'SMPF Settings', 'smpf-core' ),
            __( 'Settings', 'smpf-core' ),
            'manage_options',
            'smpf-settings',
            array( 'SMPF_Admin', 'render_settings' )
        );
    }

    /**
     * Register plugin settings.
     */
    public function register_settings() {
        register_setting( 'smpf_core_settings', 'smpf_backend_url', array(
            'type'              => 'string',
            'default'           => 'http://127.0.0.1:8000',
            'sanitize_callback' => 'esc_url_raw',
        ) );
        register_setting( 'smpf_core_settings', 'smpf_api_key', array(
            'type'    => 'string',
            'default' => '',
        ) );
        register_setting( 'smpf_core_settings', 'smpf_debug_mode', array(
            'type'    => 'boolean',
            'default' => false,
        ) );
    }

    /**
     * Enqueue admin CSS and JS.
     *
     * @param string $hook Current admin page hook.
     */
    public function enqueue_assets( $hook ) {
        if ( strpos( $hook, 'smpf-' ) === false ) {
            return;
        }
        wp_enqueue_style(
            'smpf-admin-css',
            SMPF_CORE_PLUGIN_URL . 'assets/css/smpf-admin.css',
            array(),
            SMPF_CORE_VERSION
        );
        wp_enqueue_script(
            'smpf-admin-js',
            SMPF_CORE_PLUGIN_URL . 'assets/js/smpf-admin.js',
            array( 'jquery' ),
            SMPF_CORE_VERSION,
            true
        );
        wp_localize_script( 'smpf-admin-js', 'smpf_ajax', array(
            'ajax_url' => admin_url( 'admin-ajax.php' ),
            'nonce'    => wp_create_nonce( 'smpf_ajax_nonce' ),
        ) );
    }

    /**
     * AJAX handler: Test backend connection.
     */
    public function ajax_test_connection() {
        check_ajax_referer( 'smpf_ajax_nonce', 'nonce' );
        if ( ! current_user_can( 'manage_options' ) ) {
            wp_send_json_error( __( 'Permission denied.', 'smpf-core' ) );
        }
        $result = $this->api->get( '/' );
        if ( is_wp_error( $result ) ) {
            wp_send_json_error( $result->get_error_message() );
        }
        wp_send_json_success( array(
            'message' => __( 'Backend connected successfully.', 'smpf-core' ),
            'data'    => $result,
        ) );
    }

    /**
     * AJAX handler: Fetch platform status from backend.
     */
    public function ajax_fetch_status() {
        check_ajax_referer( 'smpf_ajax_nonce', 'nonce' );
        if ( ! current_user_can( 'manage_options' ) ) {
            wp_send_json_error( __( 'Permission denied.', 'smpf-core' ) );
        }
        $result = $this->api->get( '/api/analytics/connections' );
        if ( is_wp_error( $result ) ) {
            wp_send_json_error( $result->get_error_message() );
        }
        wp_send_json_success( $result );
    }
}

// Initialize.
add_action( 'plugins_loaded', array( 'SMPF_Core', 'get_instance' ) );
