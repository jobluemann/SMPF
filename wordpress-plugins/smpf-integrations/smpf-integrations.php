<?php
/**
 * Plugin Name: SMPF Integrations
 * Plugin URI: https://finwatchpro.net
 * Description: Email signup forms and CRM webhooks for SMPF. Requires SMPF Core.
 * Version: 1.0.0
 * Author: Jo Bluemann
 * License: GPL-2.0+
 * Text Domain: smpf-integrations
 *
 * @package SMPF_Integrations
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

add_action( 'admin_init', function() {
    if ( ! class_exists( 'SMPF_Core' ) ) {
        deactivate_plugins( plugin_basename( __FILE__ ) );
        add_action( 'admin_notices', function() {
            echo '<div class="error"><p><strong>SMPF Integrations:</strong> ' . esc_html__( 'SMPF Core must be active.', 'smpf-integrations' ) . '</p></div>';
        });
    }
});

class SMPF_Integrations {
    private static $instance = null;
    public static function get_instance() {
        if ( null === self::$instance ) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    private function __construct() {
        add_action( 'admin_menu', array( $this, 'register_menu' ) );
        add_action( 'admin_init', array( $this, 'register_settings' ) );
        add_shortcode( 'smpf_email_signup', array( $this, 'render_email_shortcode' ) );
    }
    public function register_menu() {
        add_submenu_page(
            'smpf-dashboard',
            __( 'Integrations', 'smpf-integrations' ),
            __( 'Integrations', 'smpf-integrations' ),
            'manage_options',
            'smpf-integrations',
            array( $this, 'render_page' )
        );
    }
    public function register_settings() {
        register_setting( 'smpf_integrations_settings', 'smpf_email_provider', array( 'default' => 'mailerlite' ) );
        register_setting( 'smpf_integrations_settings', 'smpf_email_api_key' );
        register_setting( 'smpf_integrations_settings', 'smpf_email_list_id' );
        register_setting( 'smpf_integrations_settings', 'smpf_telegram_notify_chat' );
    }
    public function render_page() {
        include plugin_dir_path( __FILE__ ) . 'templates/integrations.php';
    }
    public function render_email_shortcode( $atts ) {
        $atts = shortcode_atts( array(
            'button_text' => __( 'Subscribe', 'smpf-integrations' ),
            'placeholder' => __( 'Enter your email', 'smpf-integrations' ),
        ), $atts, 'smpf_email_signup' );
        ob_start();
        ?>
        <form class="smpf-email-signup" style="display:flex;gap:8px;max-width:400px;">
            <input type="email" name="smpf_email" placeholder="<?php echo esc_attr( $atts['placeholder'] ); ?>" required style="flex:1;padding:10px;border:1px solid #ccc;border-radius:4px;">
            <button type="submit" style="padding:10px 20px;background:#2271b1;color:#fff;border:none;border-radius:4px;cursor:pointer;"><?php echo esc_html( $atts['button_text'] ); ?></button>
        </form>
        <div class="smpf-email-result" style="margin-top:8px;font-size:0.9em;"></div>
        <?php
        return ob_get_clean();
    }
}
add_action( 'plugins_loaded', array( 'SMPF_Integrations', 'get_instance' ) );
