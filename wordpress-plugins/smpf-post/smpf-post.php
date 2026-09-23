<?php
/**
 * Plugin Name: SMPF Post
 * Plugin URI: https://finwatchpro.net
 * Description: Post composer and scheduler for the Social Media Platform Framework. Requires SMPF Core.
 * Version: 1.0.0
 * Author: Jo Bluemann
 * License: GPL-2.0+
 * Text Domain: smpf-post
 *
 * @package SMPF_Post
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

// Dependency check.
add_action( 'admin_init', function() {
    if ( ! class_exists( 'SMPF_Core' ) ) {
        deactivate_plugins( plugin_basename( __FILE__ ) );
        add_action( 'admin_notices', function() {
            echo '<div class="error"><p><strong>SMPF Post:</strong> ' . esc_html__( 'SMPF Core must be installed and activated first.', 'smpf-post' ) . '</p></div>';
        });
    }
});

/**
 * Class SMPF_Post
 */
class SMPF_Post {

    private static $instance = null;

    public static function get_instance() {
        if ( null === self::$instance ) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        add_action( 'admin_menu', array( $this, 'register_menu' ) );
        add_action( 'wp_ajax_smpf_create_post', array( $this, 'ajax_create_post' ) );
        add_action( 'wp_ajax_smpf_get_platforms', array( $this, 'ajax_get_platforms' ) );
    }

    public function register_menu() {
        add_submenu_page(
            'smpf-dashboard',
            __( 'Create Post', 'smpf-post' ),
            __( 'Create Post', 'smpf-post' ),
            'manage_options',
            'smpf-post-composer',
            array( $this, 'render_composer' )
        );
        add_submenu_page(
            'smpf-dashboard',
            __( 'Post Schedule', 'smpf-post' ),
            __( 'Schedule', 'smpf-post' ),
            'manage_options',
            'smpf-post-schedule',
            array( $this, 'render_schedule' )
        );
    }

    public function render_composer() {
        include plugin_dir_path( __FILE__ ) . 'templates/post-composer.php';
    }

    public function render_schedule() {
        include plugin_dir_path( __FILE__ ) . 'templates/post-schedule.php';
    }

    public function ajax_create_post() {
        check_ajax_referer( 'smpf_ajax_nonce', 'nonce' );
        if ( ! current_user_can( 'manage_options' ) ) {
            wp_send_json_error( __( 'Permission denied.', 'smpf-post' ) );
        }

        $text     = isset( $_POST['text'] ) ? sanitize_textarea_field( wp_unslash( $_POST['text'] ) ) : '';
        $platforms = isset( $_POST['platforms'] ) ? array_map( 'sanitize_text_field', wp_unslash( $_POST['platforms'] ) ) : array();
        $image_url = isset( $_POST['image_url'] ) ? esc_url_raw( wp_unslash( $_POST['image_url'] ) ) : '';

        if ( empty( $text ) || empty( $platforms ) ) {
            wp_send_json_error( __( 'Text and at least one platform are required.', 'smpf-post' ) );
        }

        $core = SMPF_Core::get_instance();
        $body = array(
            'platforms' => $platforms,
            'content'   => array( 'text' => $text ),
        );
        if ( ! empty( $image_url ) ) {
            $body['content']['image_url'] = $image_url;
        }

        $result = $core->api->post( '/api/post', $body );
        if ( is_wp_error( $result ) ) {
            wp_send_json_error( $result->get_error_message() );
        }
        wp_send_json_success( $result );
    }

    public function ajax_get_platforms() {
        check_ajax_referer( 'smpf_ajax_nonce', 'nonce' );
        $core = SMPF_Core::get_instance();
        $result = $core->api->get( '/api/analytics/connections' );
        if ( is_wp_error( $result ) ) {
            wp_send_json_error( $result->get_error_message() );
        }
        wp_send_json_success( isset( $result['platforms'] ) ? $result['platforms'] : array() );
    }
}

add_action( 'plugins_loaded', array( 'SMPF_Post', 'get_instance' ) );
