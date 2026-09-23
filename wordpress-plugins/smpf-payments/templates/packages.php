<?php
/**
 * SMPF Packages & Donations Template
 *
 * @package SMPF_Payments
 */
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}
?>
<div class="wrap smpf-wrap">
    <h1><?php esc_html_e( 'Packages & Payments', 'smpf-payments' ); ?></h1>

    <div class="smpf-card">
        <h2><?php esc_html_e( 'Tip / Donation Links', 'smpf-payments' ); ?></h2>
        <p><?php esc_html_e( 'Enter your public donation links below. The floating donation bar will appear on every page of your site.', 'smpf-payments' ); ?></p>
        <form method="post" action="options.php">
            <?php settings_fields( 'smpf_payments_settings' ); ?>
            <?php do_settings_sections( 'smpf_payments_settings' ); ?>

            <h3><?php esc_html_e( 'PayPal', 'smpf-payments' ); ?></h3>
            <div class="smpf-form-group">
                <label><?php esc_html_e( 'PayPal Email (legacy)', 'smpf-payments' ); ?></label>
                <input type="email" name="smpf_paypal_email" value="<?php echo esc_attr( get_option( 'smpf_paypal_email', '' ) ); ?>" class="regular-text">
            </div>
            <div class="smpf-form-group">
                <label><?php esc_html_e( 'PayPal.Me or Donation Link', 'smpf-payments' ); ?></label>
                <input type="url" name="smpf_paypal_link" value="<?php echo esc_attr( get_option( 'smpf_paypal_link', '' ) ); ?>" class="regular-text" placeholder="https://paypal.me/yourname">
            </div>

            <h3><?php esc_html_e( 'Ko-fi', 'smpf-payments' ); ?></h3>
            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Ko-fi Page Link', 'smpf-payments' ); ?></label>
                <input type="url" name="smpf_kofi_link" value="<?php echo esc_attr( get_option( 'smpf_kofi_link', '' ) ); ?>" class="regular-text" placeholder="https://ko-fi.com/yourname">
            </div>

            <h3><?php esc_html_e( 'Buy Me a Coffee', 'smpf-payments' ); ?></h3>
            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Buy Me a Coffee Link', 'smpf-payments' ); ?></label>
                <input type="url" name="smpf_buymeacoffee_link" value="<?php echo esc_attr( get_option( 'smpf_buymeacoffee_link', '' ) ); ?>" class="regular-text" placeholder="https://buymeacoffee.com/yourname">
            </div>

            <h3><?php esc_html_e( 'Crypto Wallets', 'smpf-payments' ); ?></h3>
            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Bitcoin (BTC) Address', 'smpf-payments' ); ?></label>
                <input type="text" name="smpf_crypto_btc_address" value="<?php echo esc_attr( get_option( 'smpf_crypto_btc_address', '' ) ); ?>" class="regular-text">
            </div>
            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Ethereum (ETH) Address', 'smpf-payments' ); ?></label>
                <input type="text" name="smpf_crypto_eth_address" value="<?php echo esc_attr( get_option( 'smpf_crypto_eth_address', '' ) ); ?>" class="regular-text">
            </div>

            <hr style="margin: 24px 0; border: 0; border-top: 1px solid #c3c4c7;">

            <h2><?php esc_html_e( 'Floating Donation Bar Settings', 'smpf-payments' ); ?></h2>

            <div class="smpf-form-group">
                <label>
                    <input type="checkbox" name="smpf_donation_bar_enabled" value="1" <?php checked( 1, get_option( 'smpf_donation_bar_enabled', 1 ) ); ?>>
                    <?php esc_html_e( 'Enable floating donation bar on all pages', 'smpf-payments' ); ?>
                </label>
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Banner Text', 'smpf-payments' ); ?></label>
                <input type="text" name="smpf_donation_banner_text" value="<?php echo esc_attr( get_option( 'smpf_donation_banner_text', __( 'Help support our work', 'smpf-payments' ) ) ); ?>" class="regular-text">
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Appear Every (minutes)', 'smpf-payments' ); ?></label>
                <input type="number" name="smpf_donation_bar_interval" value="<?php echo esc_attr( get_option( 'smpf_donation_bar_interval', 5 ) ); ?>" min="1" max="10" step="1" class="small-text">
                <p class="description"><?php esc_html_e( 'The bar will appear every X minutes (1–10). It stays visible for 15 seconds each time.', 'smpf-payments' ); ?></p>
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Position on Screen', 'smpf-payments' ); ?></label>
                <select name="smpf_donation_bar_position">
                    <?php
                    $position = get_option( 'smpf_donation_bar_position', 'bottom-right' );
                    $positions = array(
                        'bottom-right'  => __( 'Bottom Right', 'smpf-payments' ),
                        'bottom-left'   => __( 'Bottom Left', 'smpf-payments' ),
                        'bottom-center' => __( 'Bottom Center', 'smpf-payments' ),
                        'top-right'     => __( 'Top Right', 'smpf-payments' ),
                        'top-left'      => __( 'Top Left', 'smpf-payments' ),
                    );
                    foreach ( $positions as $key => $label ) {
                        printf( '<option value="%s" %s>%s</option>', esc_attr( $key ), selected( $position, $key, false ), esc_html( $label ) );
                    }
                    ?>
                </select>
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'QR Code Image URL', 'smpf-payments' ); ?></label>
                <input type="url" name="smpf_donation_qr_code_url" value="<?php echo esc_attr( get_option( 'smpf_donation_qr_code_url', '' ) ); ?>" class="regular-text" placeholder="https://yoursite.com/qr-code.png">
                <p class="description"><?php esc_html_e( 'Upload your QR code via Media Library and paste the URL here. It will appear in the donation bar for mobile scanning.', 'smpf-payments' ); ?></p>
            </div>

            <?php submit_button( __( 'Save Donation Settings', 'smpf-payments' ) ); ?>
        </form>
    </div>

    <div class="smpf-card">
        <h2><?php esc_html_e( 'Ko-fi Official Widget', 'smpf-payments' ); ?></h2>
        <p><?php esc_html_e( 'Enable the official Ko-fi widget. Floating types appear on every page; Inline Embed is placed via shortcode.', 'smpf-payments' ); ?></p>
        <form method="post" action="options.php">
            <?php settings_fields( 'smpf_payments_settings' ); ?>
            <?php do_settings_sections( 'smpf_payments_settings' ); ?>

            <div class="smpf-form-group">
                <label>
                    <input type="checkbox" name="smpf_kofi_widget_enabled" value="1" <?php checked( 1, get_option( 'smpf_kofi_widget_enabled', 0 ) ); ?>>
                    <?php esc_html_e( 'Enable official Ko-fi widget', 'smpf-payments' ); ?>
                </label>
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Ko-fi Username', 'smpf-payments' ); ?></label>
                <input type="text" name="smpf_kofi_username" value="<?php echo esc_attr( get_option( 'smpf_kofi_username', '' ) ); ?>" class="regular-text" placeholder="jobluemann">
                <p class="description"><?php esc_html_e( 'Your Ko-fi page username.', 'smpf-payments' ); ?></p>
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Widget Type', 'smpf-payments' ); ?></label>
                <select name="smpf_kofi_widget_type">
                    <?php
                    $type = get_option( 'smpf_kofi_widget_type', 'button' );
                    $types = array(
                        'button'        => __( 'Floating Button', 'smpf-payments' ),
                        'floating-chat' => __( 'Floating Chat Overlay', 'smpf-payments' ),
                        'inline-embed'  => __( 'Inline Embed (shortcode only)', 'smpf-payments' ),
                    );
                    foreach ( $types as $key => $label ) {
                        printf( '<option value="%s" %s>%s</option>', esc_attr( $key ), selected( $type, $key, false ), esc_html( $label ) );
                    }
                    ?>
                </select>
            </div>

            <hr style="margin: 20px 0; border: 0; border-top: 1px solid #f0f0f0;">
            <h4><?php esc_html_e( 'Floating Button Options', 'smpf-payments' ); ?></h4>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Button Text', 'smpf-payments' ); ?></label>
                <input type="text" name="smpf_kofi_widget_text" value="<?php echo esc_attr( get_option( 'smpf_kofi_widget_text', __( 'Support me on Ko-fi', 'smpf-payments' ) ) ); ?>" class="regular-text">
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Button Colour', 'smpf-payments' ); ?></label>
                <input type="color" name="smpf_kofi_widget_color" value="<?php echo esc_attr( get_option( 'smpf_kofi_widget_color', '#72a4f2' ) ); ?>" style="width:60px;height:36px;padding:2px;border:1px solid #8c8f94;border-radius:4px;">
            </div>

            <hr style="margin: 20px 0; border: 0; border-top: 1px solid #f0f0f0;">
            <h4><?php esc_html_e( 'Floating Chat Overlay Options', 'smpf-payments' ); ?></h4>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Donate Button Text', 'smpf-payments' ); ?></label>
                <input type="text" name="smpf_kofi_chat_button_text" value="<?php echo esc_attr( get_option( 'smpf_kofi_chat_button_text', __( 'Support me', 'smpf-payments' ) ) ); ?>" class="regular-text">
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Button Background Colour', 'smpf-payments' ); ?></label>
                <input type="color" name="smpf_kofi_chat_bg_color" value="<?php echo esc_attr( get_option( 'smpf_kofi_chat_bg_color', '#00b9fe' ) ); ?>" style="width:60px;height:36px;padding:2px;border:1px solid #8c8f94;border-radius:4px;">
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Button Text Colour', 'smpf-payments' ); ?></label>
                <input type="color" name="smpf_kofi_chat_text_color" value="<?php echo esc_attr( get_option( 'smpf_kofi_chat_text_color', '#ffffff' ) ); ?>" style="width:60px;height:36px;padding:2px;border:1px solid #8c8f94;border-radius:4px;">
            </div>

            <hr style="margin: 20px 0; border: 0; border-top: 1px solid #f0f0f0;">
            <h4><?php esc_html_e( 'Inline Embed (iframe) Options', 'smpf-payments' ); ?></h4>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Iframe Height (px)', 'smpf-payments' ); ?></label>
                <input type="number" name="smpf_kofi_iframe_height" value="<?php echo esc_attr( get_option( 'smpf_kofi_iframe_height', 712 ) ); ?>" min="200" max="2000" step="1" class="small-text">
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Background Colour', 'smpf-payments' ); ?></label>
                <input type="color" name="smpf_kofi_iframe_bg" value="<?php echo esc_attr( get_option( 'smpf_kofi_iframe_bg', '#f9f9f9' ) ); ?>" style="width:60px;height:36px;padding:2px;border:1px solid #8c8f94;border-radius:4px;">
            </div>

            <div class="smpf-form-group">
                <label>
                    <input type="checkbox" name="smpf_kofi_iframe_hidefeed" value="1" <?php checked( 1, get_option( 'smpf_kofi_iframe_hidefeed', 1 ) ); ?>>
                    <?php esc_html_e( 'Hide feed (show only donation widget)', 'smpf-payments' ); ?>
                </label>
            </div>

            <div class="smpf-form-group">
                <p class="description">
                    <?php esc_html_e( 'Shortcode to place embed anywhere:', 'smpf-payments' ); ?>
                    <code>[smpf_kofi_embed]</code>
                </p>
            </div>

            <?php submit_button( __( 'Save Ko-fi Widget Settings', 'smpf-payments' ) ); ?>
        </form>
    </div>

    <div class="smpf-card">
        <h2><?php esc_html_e( 'Buy Me a Coffee Widget', 'smpf-payments' ); ?></h2>
        <p><?php esc_html_e( 'Enable the official Buy Me a Coffee floating button. This appears on every page of your site.', 'smpf-payments' ); ?></p>
        <form method="post" action="options.php">
            <?php settings_fields( 'smpf_payments_settings' ); ?>
            <?php do_settings_sections( 'smpf_payments_settings' ); ?>

            <div class="smpf-form-group">
                <label>
                    <input type="checkbox" name="smpf_bmc_widget_enabled" value="1" <?php checked( 1, get_option( 'smpf_bmc_widget_enabled', 0 ) ); ?>>
                    <?php esc_html_e( 'Enable Buy Me a Coffee widget', 'smpf-payments' ); ?>
                </label>
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'BMC Page Slug', 'smpf-payments' ); ?></label>
                <input type="text" name="smpf_bmc_slug" value="<?php echo esc_attr( get_option( 'smpf_bmc_slug', '' ) ); ?>" class="regular-text" placeholder="jobluemann">
                <p class="description"><?php esc_html_e( 'Your Buy Me a Coffee page slug (the part after buymeacoffee.com/).', 'smpf-payments' ); ?></p>
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Button Text', 'smpf-payments' ); ?></label>
                <input type="text" name="smpf_bmc_text" value="<?php echo esc_attr( get_option( 'smpf_bmc_text', __( 'Buy me a coffee', 'smpf-payments' ) ) ); ?>" class="regular-text">
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Button Colour', 'smpf-payments' ); ?></label>
                <input type="color" name="smpf_bmc_color" value="<?php echo esc_attr( get_option( 'smpf_bmc_color', '#FFDD00' ) ); ?>" style="width:60px;height:36px;padding:2px;border:1px solid #8c8f94;border-radius:4px;">
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Emoji', 'smpf-payments' ); ?></label>
                <input type="text" name="smpf_bmc_emoji" value="<?php echo esc_attr( get_option( 'smpf_bmc_emoji', '☕' ) ); ?>" class="small-text" maxlength="4" style="width:60px;">
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Font', 'smpf-payments' ); ?></label>
                <select name="smpf_bmc_font">
                    <?php
                    $font = get_option( 'smpf_bmc_font', 'Cookie' );
                    $fonts = array(
                        'Cookie'      => 'Cookie',
                        'Arial'       => 'Arial',
                        'Comic'       => 'Comic',
                        'Courier'     => 'Courier',
                        'Georgia'     => 'Georgia',
                        'Impact'      => 'Impact',
                        'Lato'        => 'Lato',
                        'Poppins'     => 'Poppins',
                        'Tahoma'      => 'Tahoma',
                        'Verdana'     => 'Verdana',
                    );
                    foreach ( $fonts as $key => $label ) {
                        printf( '<option value="%s" %s>%s</option>', esc_attr( $key ), selected( $font, $key, false ), esc_html( $label ) );
                    }
                    ?>
                </select>
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Outline Colour', 'smpf-payments' ); ?></label>
                <input type="color" name="smpf_bmc_outline_color" value="<?php echo esc_attr( get_option( 'smpf_bmc_outline_color', '#000000' ) ); ?>" style="width:60px;height:36px;padding:2px;border:1px solid #8c8f94;border-radius:4px;">
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Text Colour', 'smpf-payments' ); ?></label>
                <input type="color" name="smpf_bmc_font_color" value="<?php echo esc_attr( get_option( 'smpf_bmc_font_color', '#000000' ) ); ?>" style="width:60px;height:36px;padding:2px;border:1px solid #8c8f94;border-radius:4px;">
            </div>

            <div class="smpf-form-group">
                <label><?php esc_html_e( 'Coffee Cup Colour', 'smpf-payments' ); ?></label>
                <input type="color" name="smpf_bmc_coffee_color" value="<?php echo esc_attr( get_option( 'smpf_bmc_coffee_color', '#ffffff' ) ); ?>" style="width:60px;height:36px;padding:2px;border:1px solid #8c8f94;border-radius:4px;">
            </div>

            <?php submit_button( __( 'Save BMC Widget Settings', 'smpf-payments' ) ); ?>
        </form>
    </div>

    <div class="smpf-card">
        <h2><?php esc_html_e( 'Planned Package Tiers', 'smpf-payments' ); ?></h2>
        <table class="wp-list-table widefat fixed striped">
            <thead>
                <tr><th><?php esc_html_e( 'Package', 'smpf-payments' ); ?></th><th><?php esc_html_e( 'Platforms', 'smpf-payments' ); ?></th><th><?php esc_html_e( 'Posts/Day', 'smpf-payments' ); ?></th><th><?php esc_html_e( 'Price', 'smpf-payments' ); ?></th></tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong><?php esc_html_e( 'Starter', 'smpf-payments' ); ?></strong></td>
                    <td>X + 1 Meta (FB/IG/Threads)</td>
                    <td>3</td>
                    <td>R299 / $17/mo</td>
                </tr>
                <tr>
                    <td><strong><?php esc_html_e( 'Growth', 'smpf-payments' ); ?></strong></td>
                    <td>X + All Meta + Telegram</td>
                    <td>5</td>
                    <td>R499 / $29/mo</td>
                </tr>
                <tr>
                    <td><strong><?php esc_html_e( 'Pro', 'smpf-payments' ); ?></strong></td>
                    <td>All platforms + WhatsApp groups</td>
                    <td>10</td>
                    <td>R799 / $47/mo</td>
                </tr>
                <tr>
                    <td><strong><?php esc_html_e( 'Enterprise', 'smpf-payments' ); ?></strong></td>
                    <td>Everything + custom AI voice + priority</td>
                    <td>Unlimited</td>
                    <td><?php esc_html_e( 'Custom', 'smpf-payments' ); ?></td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
