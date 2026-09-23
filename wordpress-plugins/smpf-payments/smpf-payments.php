<?php
/**
 * Plugin Name: SMPF Payments
 * Plugin URI: https://finwatchpro.net
 * Description: Payment integration, package tiers, floating donation bar, Ko-fi and Buy Me a Coffee widgets for SMPF. Requires SMPF Core.
 * Version: 1.6.0
 * Author: Jo Bluemann
 * License: GPL-2.0+
 * Text Domain: smpf-payments
 *
 * @package SMPF_Payments
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

add_action( 'admin_init', function() {
    if ( ! class_exists( 'SMPF_Core' ) ) {
        deactivate_plugins( plugin_basename( __FILE__ ) );
        add_action( 'admin_notices', function() {
            echo '<div class="error"><p><strong>SMPF Payments:</strong> ' . esc_html__( 'SMPF Core must be active.', 'smpf-payments' ) . '</p></div>';
        });
    }
});

class SMPF_Payments {
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
        add_action( 'wp_enqueue_scripts', array( $this, 'enqueue_frontend_assets' ) );
        add_action( 'wp_footer', array( $this, 'render_bmc_widget' ) );
        add_action( 'wp_footer', array( $this, 'render_kofi_widget' ) );
        add_action( 'wp_footer', array( $this, 'render_donation_bar' ) );
        add_shortcode( 'smpf_kofi_embed', array( $this, 'shortcode_kofi_embed' ) );
    }

    public function register_menu() {
        add_submenu_page(
            'smpf-dashboard',
            __( 'Packages & Payments', 'smpf-payments' ),
            __( 'Packages', 'smpf-payments' ),
            'manage_options',
            'smpf-payments',
            array( $this, 'render_page' )
        );
    }

    public function register_settings() {
        // Payment gateway settings
        register_setting( 'smpf_payments_settings', 'smpf_payfast_merchant_id' );
        register_setting( 'smpf_payments_settings', 'smpf_payfast_merchant_key' );
        register_setting( 'smpf_payments_settings', 'smpf_paypal_email' );
        register_setting( 'smpf_payments_settings', 'smpf_paypal_link' );
        register_setting( 'smpf_payments_settings', 'smpf_kofi_link' );
        register_setting( 'smpf_payments_settings', 'smpf_buymeacoffee_link' );
        register_setting( 'smpf_payments_settings', 'smpf_crypto_btc_address' );
        register_setting( 'smpf_payments_settings', 'smpf_crypto_eth_address' );

        // Buy Me a Coffee widget settings
        register_setting( 'smpf_payments_settings', 'smpf_bmc_widget_enabled', array(
            'type'    => 'boolean',
            'default' => false,
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_bmc_slug', array(
            'type'    => 'string',
            'default' => '',
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_bmc_color', array(
            'type'    => 'string',
            'default' => '#FFDD00',
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_bmc_emoji', array(
            'type'    => 'string',
            'default' => '☕',
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_bmc_font', array(
            'type'    => 'string',
            'default' => 'Cookie',
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_bmc_text', array(
            'type'    => 'string',
            'default' => __( 'Buy me a coffee', 'smpf-payments' ),
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_bmc_outline_color', array(
            'type'    => 'string',
            'default' => '#000000',
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_bmc_font_color', array(
            'type'    => 'string',
            'default' => '#000000',
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_bmc_coffee_color', array(
            'type'    => 'string',
            'default' => '#ffffff',
        ) );

        // Ko-fi official widget settings
        register_setting( 'smpf_payments_settings', 'smpf_kofi_widget_enabled', array(
            'type'    => 'boolean',
            'default' => false,
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_kofi_username' );
        register_setting( 'smpf_payments_settings', 'smpf_kofi_widget_type', array(
            'type'    => 'string',
            'default' => 'button',
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_kofi_widget_text', array(
            'type'    => 'string',
            'default' => __( 'Support me on Ko-fi', 'smpf-payments' ),
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_kofi_widget_color', array(
            'type'    => 'string',
            'default' => '#72a4f2',
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_kofi_chat_button_text', array(
            'type'    => 'string',
            'default' => __( 'Support me', 'smpf-payments' ),
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_kofi_chat_bg_color', array(
            'type'    => 'string',
            'default' => '#00b9fe',
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_kofi_chat_text_color', array(
            'type'    => 'string',
            'default' => '#ffffff',
        ) );

        // Ko-fi inline iframe embed settings
        register_setting( 'smpf_payments_settings', 'smpf_kofi_iframe_height', array(
            'type'    => 'integer',
            'default' => 712,
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_kofi_iframe_bg', array(
            'type'    => 'string',
            'default' => '#f9f9f9',
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_kofi_iframe_hidefeed', array(
            'type'    => 'boolean',
            'default' => true,
        ) );

        // Donation bar settings
        register_setting( 'smpf_payments_settings', 'smpf_donation_bar_enabled', array(
            'type'    => 'boolean',
            'default' => true,
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_donation_bar_interval', array(
            'type'              => 'integer',
            'default'           => 5,
            'sanitize_callback' => array( $this, 'sanitize_interval' ),
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_donation_bar_position', array(
            'type'    => 'string',
            'default' => 'bottom-right',
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_donation_banner_text', array(
            'type'    => 'string',
            'default' => __( 'Help support our work', 'smpf-payments' ),
        ) );
        register_setting( 'smpf_payments_settings', 'smpf_donation_qr_code_url' );
    }

    public function sanitize_interval( $value ) {
        $int = absint( $value );
        if ( $int < 1 ) return 1;
        if ( $int > 10 ) return 10;
        return $int;
    }

    public function render_page() {
        include plugin_dir_path( __FILE__ ) . 'templates/packages.php';
    }

    /**
     * Enqueue donation bar CSS and JS on the frontend.
     */
    public function enqueue_frontend_assets() {
        if ( ! $this->should_show_donation_bar() && ! get_option( 'smpf_donation_qr_code_url' ) ) {
            return;
        }
        wp_enqueue_style(
            'smpf-donation-bar-css',
            plugin_dir_url( __FILE__ ) . 'assets/css/donation-bar.css',
            array(),
            '1.6.0'
        );
        wp_enqueue_script(
            'smpf-donation-bar-js',
            plugin_dir_url( __FILE__ ) . 'assets/js/donation-bar.js',
            array(),
            '1.6.0',
            true
        );
        wp_localize_script( 'smpf-donation-bar-js', 'smpfDonationConfig', array(
            'interval' => absint( get_option( 'smpf_donation_bar_interval', 5 ) ),
        ) );
    }

    /**
     * Determine if any donation UI should render.
     */
    private function has_any_donation_method() {
        $methods = array(
            'smpf_paypal_link',
            'smpf_kofi_link',
            'smpf_buymeacoffee_link',
            'smpf_crypto_btc_address',
            'smpf_crypto_eth_address',
        );
        foreach ( $methods as $key ) {
            if ( get_option( $key ) ) {
                return true;
            }
        }
        return false;
    }

    /**
     * Determine if the donation bar should render.
     */
    private function should_show_donation_bar() {
        if ( is_admin() ) {
            return false;
        }
        if ( ! get_option( 'smpf_donation_bar_enabled', true ) ) {
            return false;
        }
        return $this->has_any_donation_method();
    }

    /**
     * Shortcode: Inline Ko-fi iframe embed.
     *
     * Usage: [smpf_kofi_embed]
     */
    public function shortcode_kofi_embed( $atts ) {
        $username = sanitize_text_field( get_option( 'smpf_kofi_username', '' ) );
        if ( empty( $username ) ) {
            return '<p>' . esc_html__( 'Ko-fi username not configured.', 'smpf-payments' ) . '</p>';
        }

        $height    = absint( get_option( 'smpf_kofi_iframe_height', 712 ) );
        $bg        = sanitize_hex_color( get_option( 'smpf_kofi_iframe_bg', '#f9f9f9' ) );
        $hidefeed  = get_option( 'smpf_kofi_iframe_hidefeed', true ) ? 'true' : 'false';

        $url = sprintf(
            'https://ko-fi.com/%s/?hidefeed=%s&widget=true&embed=true&preview=true',
            esc_attr( $username ),
            $hidefeed
        );

        ob_start();
        ?>
        <iframe id="kofiframe" src="<?php echo esc_url( $url ); ?>" style="border:none;width:100%;padding:4px;background:<?php echo esc_attr( $bg ); ?>;" height="<?php echo esc_attr( $height ); ?>" title="<?php echo esc_attr( $username ); ?>"></iframe>
        <?php
        return ob_get_clean();
    }

    /**
     * Render the Buy Me a Coffee widget in the footer.
     */
    public function render_bmc_widget() {
        if ( is_admin() ) {
            return;
        }
        if ( ! get_option( 'smpf_bmc_widget_enabled', false ) ) {
            return;
        }
        $slug = sanitize_text_field( get_option( 'smpf_bmc_slug', '' ) );
        if ( empty( $slug ) ) {
            return;
        }
        $color        = sanitize_hex_color( get_option( 'smpf_bmc_color', '#FFDD00' ) );
        $emoji        = sanitize_text_field( get_option( 'smpf_bmc_emoji', '☕' ) );
        $font         = sanitize_text_field( get_option( 'smpf_bmc_font', 'Cookie' ) );
        $text         = esc_js( get_option( 'smpf_bmc_text', __( 'Buy me a coffee', 'smpf-payments' ) ) );
        $outline      = sanitize_hex_color( get_option( 'smpf_bmc_outline_color', '#000000' ) );
        $font_color   = sanitize_hex_color( get_option( 'smpf_bmc_font_color', '#000000' ) );
        $coffee_color = sanitize_hex_color( get_option( 'smpf_bmc_coffee_color', '#ffffff' ) );
        ?>
        <script type="text/javascript" src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js" data-name="bmc-button" data-slug="<?php echo esc_js( $slug ); ?>" data-color="<?php echo esc_js( $color ); ?>" data-emoji="<?php echo esc_js( $emoji ); ?>" data-font="<?php echo esc_js( $font ); ?>" data-text="<?php echo $text; ?>" data-outline-color="<?php echo esc_js( $outline ); ?>" data-font-color="<?php echo esc_js( $font_color ); ?>" data-coffee-color="<?php echo esc_js( $coffee_color ); ?>"></script>
        <?php
    }

    /**
     * Render the official Ko-fi widget in the footer.
     */
    public function render_kofi_widget() {
        if ( is_admin() ) {
            return;
        }
        if ( ! get_option( 'smpf_kofi_widget_enabled', false ) ) {
            return;
        }
        $username = sanitize_text_field( get_option( 'smpf_kofi_username', '' ) );
        if ( empty( $username ) ) {
            return;
        }

        $type = sanitize_text_field( get_option( 'smpf_kofi_widget_type', 'button' ) );

        // Inline embed is handled via shortcode only, not footer.
        if ( 'inline-embed' === $type ) {
            return;
        }

        if ( 'floating-chat' === $type ) {
            $btn_text   = esc_js( get_option( 'smpf_kofi_chat_button_text', __( 'Support me', 'smpf-payments' ) ) );
            $btn_bg     = sanitize_hex_color( get_option( 'smpf_kofi_chat_bg_color', '#00b9fe' ) );
            $btn_color  = sanitize_hex_color( get_option( 'smpf_kofi_chat_text_color', '#ffffff' ) );
            ?>
            <script src='https://storage.ko-fi.com/cdn/scripts/overlay-widget.js'></script>
            <script>
                kofiWidgetOverlay.draw('<?php echo esc_js( $username ); ?>', {
                    'type': 'floating-chat',
                    'floating-chat.donateButton.text': '<?php echo $btn_text; ?>',
                    'floating-chat.donateButton.background-color': '<?php echo esc_js( $btn_bg ); ?>',
                    'floating-chat.donateButton.text-color': '<?php echo esc_js( $btn_color ); ?>'
                });
            </script>
            <?php
        } else {
            $text  = esc_js( get_option( 'smpf_kofi_widget_text', __( 'Support me on Ko-fi', 'smpf-payments' ) ) );
            $color = sanitize_hex_color( get_option( 'smpf_kofi_widget_color', '#72a4f2' ) );
            ?>
            <script type='text/javascript' src='https://storage.ko-fi.com/cdn/widget/Widget_2.js'></script>
            <script type='text/javascript'>
                kofiwidget2.init('<?php echo $text; ?>', '<?php echo esc_js( $color ); ?>', '<?php echo esc_js( $username ); ?>');
                kofiwidget2.draw();
            </script>
            <?php
        }
    }

    /**
     * Render the floating donation bar in the footer.
     */
    public function render_donation_bar() {
        $has_methods = $this->has_any_donation_method();
        $qr_url      = esc_url( get_option( 'smpf_donation_qr_code_url', '' ) );

        if ( ! $this->should_show_donation_bar() && empty( $qr_url ) ) {
            return;
        }

        $position    = sanitize_text_field( get_option( 'smpf_donation_bar_position', 'bottom-right' ) );
        $banner_text = esc_html( get_option( 'smpf_donation_banner_text', __( 'Help support our work', 'smpf-payments' ) ) );

        $links = array(
            'paypal'       => esc_url( get_option( 'smpf_paypal_link', '' ) ),
            'kofi'         => esc_url( get_option( 'smpf_kofi_link', '' ) ),
            'buymeacoffee' => esc_url( get_option( 'smpf_buymeacoffee_link', '' ) ),
            'btc'          => sanitize_text_field( get_option( 'smpf_crypto_btc_address', '' ) ),
            'eth'          => sanitize_text_field( get_option( 'smpf_crypto_eth_address', '' ) ),
        );

        $icons = array(
            'paypal' => '<svg viewBox="0 0 24 24"><path d="M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944 3.72a.77.77 0 0 1 .757-.629h6.724c2.838 0 5.098.835 5.946 2.455.468.895.633 1.81.527 2.94-.169 1.856-1.023 3.295-2.47 4.146-1.35.795-3.135 1.135-5.118 1.135H9.784a.77.77 0 0 0-.756.629l-.76 4.933a.641.641 0 0 1-.633.74H7.076zm7.337-14.34c-.079.503.034.93.351 1.296.342.395.89.6 1.611.6h.032c1.397 0 2.52-.297 3.312-.876.802-.587 1.348-1.468 1.588-2.556.123-.548.055-1.005-.197-1.36-.268-.377-.742-.577-1.396-.577-.025 0-.051 0-.076.001h-.032c-1.301 0-2.337.29-3.047.849-.724.57-1.188 1.418-1.347 2.423z"/></svg>',
            'kofi' => '<svg viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/><path d="M12 6c-1.1 0-2 .9-2 2 0 .55.45 1 1 1s1-.45 1-1c0-.55.45-1 1-1s1 .45 1 1c0 1.1-.9 2-2 2-.55 0-1 .45-1 1v2c0 .55.45 1 1 1s1-.45 1-1v-1.1c1.28-.55 2.17-1.82 2.17-3.3 0-2.21-1.79-4-4-4z" fill="currentColor" opacity="0.3"/></svg>',
            'buymeacoffee' => '<svg viewBox="0 0 24 24"><path d="M6.449 0h11.102c.68 0 1.232.552 1.232 1.232v21.536c0 .68-.552 1.232-1.232 1.232H6.449a1.232 1.232 0 0 1-1.232-1.232V1.232C5.217.552 5.769 0 6.449 0zm1.974 4.635v13.73h7.154V4.635H8.423zm2.038 12.308h3.077v1.538h-3.077v-1.538zM7.654 3.097h8.692v.769H7.654v-.769z"/></svg>',
            'btc' => '<svg viewBox="0 0 24 24"><path d="M23.638 14.904c-1.602 6.43-8.113 10.34-14.542 8.736C2.67 22.05-1.244 15.525.362 9.105 1.962 2.67 8.475-1.244 14.9.358c6.43 1.605 10.342 8.115 8.738 14.546zm-6.35-4.613c.24-1.59-.974-2.45-2.64-3.03l.54-2.153-1.315-.33-.52 2.1c-.347-.087-.7-.167-1.053-.25l.53-2.12-1.32-.33-.54 2.15c-.285-.065-.565-.13-.837-.2l-1.815-.45-.35 1.407s.975.224.955.238c.535.136.63.486.615.766l-.616 2.473c.037.01.085.025.138.048l-.14-.035-.865 3.47c-.066.164-.234.41-.612.316.014.02-.956-.238-.956-.238L8.12 16.54l1.71.426c.318.08.63.164.937.243l-.545 2.19 1.32.33.54-2.16c.36.1.708.19 1.05.27l-.537 2.14 1.32.33.545-2.18c2.24.42 3.93.25 4.64-1.77.57-1.63-.03-2.57-1.22-3.18.87-.2 1.53-.78 1.7-1.97zm-3.04 4.3c-.41 1.64-3.17.75-4.07.53l.73-2.92c.9.22 3.78.66 3.34 2.39zm.41-4.3c-.37 1.49-2.68.73-3.43.55l.66-2.64c.75.19 3.17.54 2.77 2.09z"/></svg>',
            'eth' => '<svg viewBox="0 0 24 24"><path d="M11.944 17.97L4.58 13.62 11.943 24l7.37-10.38-7.372 4.35h.003zM12.056 0L4.69 12.223l7.365 4.354 7.365-4.35L12.056 0z"/></svg>',
        );

        ?>
        <div id="smpf-donation-bar" class="smpf-donation-bar position-<?php echo esc_attr( $position ); ?>">
            <button id="smpf-donation-close" class="smpf-donation-close" aria-label="<?php esc_attr_e( 'Close', 'smpf-payments' ); ?>">&times;</button>
            <div class="smpf-donation-banner"><?php echo $banner_text; ?></div>
            <?php if ( $has_methods ) : ?>
            <div class="smpf-donation-icons">
                <?php if ( $links['paypal'] ) : ?>
                    <a href="<?php echo $links['paypal']; ?>" target="_blank" rel="noopener noreferrer" class="smpf-donation-icon paypal" data-label="PayPal" aria-label="PayPal">
                        <?php echo $icons['paypal']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
                    </a>
                <?php endif; ?>
                <?php if ( $links['kofi'] ) : ?>
                    <a href="<?php echo $links['kofi']; ?>" target="_blank" rel="noopener noreferrer" class="smpf-donation-icon kofi" data-label="Ko-fi" aria-label="Ko-fi">
                        <?php echo $icons['kofi']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
                    </a>
                <?php endif; ?>
                <?php if ( $links['buymeacoffee'] ) : ?>
                    <a href="<?php echo $links['buymeacoffee']; ?>" target="_blank" rel="noopener noreferrer" class="smpf-donation-icon buymeacoffee" data-label="Buy Me a Coffee" aria-label="Buy Me a Coffee">
                        <?php echo $icons['buymeacoffee']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
                    </a>
                <?php endif; ?>
                <?php if ( $links['btc'] ) : ?>
                    <a href="bitcoin:<?php echo esc_attr( $links['btc'] ); ?>" class="smpf-donation-icon btc" data-label="Bitcoin" aria-label="Bitcoin">
                        <?php echo $icons['btc']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
                    </a>
                <?php endif; ?>
                <?php if ( $links['eth'] ) : ?>
                    <a href="ethereum:<?php echo esc_attr( $links['eth'] ); ?>" class="smpf-donation-icon eth" data-label="Ethereum" aria-label="Ethereum">
                        <?php echo $icons['eth']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
                    </a>
                <?php endif; ?>
            </div>
            <?php endif; ?>
            <?php if ( $qr_url ) : ?>
            <div class="smpf-donation-qr">
                <img src="<?php echo $qr_url; ?>" alt="<?php esc_attr_e( 'Scan to donate', 'smpf-payments' ); ?>" loading="lazy">
            </div>
            <?php endif; ?>
        </div>
        <?php
    }
}
add_action( 'plugins_loaded', array( 'SMPF_Payments', 'get_instance' ) );
