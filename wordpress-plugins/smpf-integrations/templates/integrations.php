<?php
/**
 * SMPF Integrations Template
 *
 * @package SMPF_Integrations
 */
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}
?>
<div class="wrap smpf-wrap">
    <h1><?php esc_html_e( 'Integrations', 'smpf-integrations' ); ?></h1>

    <div class="smpf-card">
        <h2><?php esc_html_e( 'Email Marketing Provider', 'smpf-integrations' ); ?></h2>
        <form method="post" action="options.php">
            <?php settings_fields( 'smpf_integrations_settings' ); ?>
            <?php do_settings_sections( 'smpf_integrations_settings' ); ?>

            <div class="smpf-form-group">
                <label for="smpf_email_provider"><?php esc_html_e( 'Provider', 'smpf-integrations' ); ?></label>
                <select id="smpf_email_provider" name="smpf_email_provider">
                    <option value="mailerlite" <?php selected( get_option( 'smpf_email_provider', 'mailerlite' ), 'mailerlite' ); ?>>MailerLite</option>
                    <option value="brevo" <?php selected( get_option( 'smpf_email_provider' ), 'brevo' ); ?>>Brevo (Sendinblue)</option>
                    <option value="mailchimp" <?php selected( get_option( 'smpf_email_provider' ), 'mailchimp' ); ?>>Mailchimp</option>
                    <option value="convertkit" <?php selected( get_option( 'smpf_email_provider' ), 'convertkit' ); ?>>ConvertKit</option>
                </select>
            </div>

            <div class="smpf-form-group">
                <label for="smpf_email_api_key"><?php esc_html_e( 'API Key', 'smpf-integrations' ); ?></label>
                <input type="password" id="smpf_email_api_key" name="smpf_email_api_key" value="<?php echo esc_attr( get_option( 'smpf_email_api_key', '' ) ); ?>" class="regular-text">
            </div>

            <div class="smpf-form-group">
                <label for="smpf_email_list_id"><?php esc_html_e( 'List / Group ID', 'smpf-integrations' ); ?></label>
                <input type="text" id="smpf_email_list_id" name="smpf_email_list_id" value="<?php echo esc_attr( get_option( 'smpf_email_list_id', '' ) ); ?>" class="regular-text">
                <p class="description"><?php esc_html_e( 'The list or group new subscribers will be added to.', 'smpf-integrations' ); ?></p>
            </div>

            <?php submit_button(); ?>
        </form>
    </div>

    <div class="smpf-card">
        <h2><?php esc_html_e( 'Telegram Notifications', 'smpf-integrations' ); ?></h2>
        <form method="post" action="options.php">
            <?php settings_fields( 'smpf_integrations_settings' ); ?>
            <div class="smpf-form-group">
                <label for="smpf_telegram_notify_chat"><?php esc_html_e( 'Notification Chat ID', 'smpf-integrations' ); ?></label>
                <input type="text" id="smpf_telegram_notify_chat" name="smpf_telegram_notify_chat" value="<?php echo esc_attr( get_option( 'smpf_telegram_notify_chat', '' ) ); ?>" class="regular-text">
                <p class="description"><?php esc_html_e( 'Send admin alerts (new signups, payment confirmations) to this Telegram chat.', 'smpf-integrations' ); ?></p>
            </div>
            <?php submit_button(); ?>
        </form>
    </div>

    <div class="smpf-card">
        <h2><?php esc_html_e( 'Shortcode', 'smpf-integrations' ); ?></h2>
        <p><?php esc_html_e( 'Add an email signup form anywhere on your site:', 'smpf-integrations' ); ?></p>
        <code style="background:#f0f0f0;padding:8px 12px;display:inline-block;border-radius:4px;">[smpf_email_signup]</code>
        <p class="description"><?php esc_html_e( 'Optional attributes: button_text, placeholder', 'smpf-integrations' ); ?></p>
        <p><strong><?php esc_html_e( 'Preview:', 'smpf-integrations' ); ?></strong></p>
        <?php echo do_shortcode( '[smpf_email_signup]' ); ?>
    </div>
</div>
