<?php
/**
 * SMPF Analytics Template
 *
 * @package SMPF_Analytics
 */
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}
$is_online = ! is_wp_error( $overview );
?>
<div class="wrap smpf-wrap">
    <h1><?php esc_html_e( 'Analytics', 'smpf-analytics' ); ?></h1>

    <?php if ( ! $is_online ) : ?>
        <div class="smpf-alert smpf-alert-warning">
            <?php esc_html_e( 'Backend is offline. Analytics unavailable.', 'smpf-analytics' ); ?>
        </div>
    <?php else : ?>

    <div class="smpf-card">
        <h2><?php esc_html_e( 'Platform Overview', 'smpf-analytics' ); ?></h2>
        <p>
            <strong><?php esc_html_e( 'Connected:', 'smpf-analytics' ); ?></strong>
            <?php echo absint( $overview['platforms']['connected'] ); ?> / <?php echo absint( $overview['platforms']['total'] ); ?><br>
            <strong><?php esc_html_e( 'Content Generated:', 'smpf-analytics' ); ?></strong>
            <?php echo absint( $overview['content_generated']['total'] ); ?>
            (<?php echo absint( $overview['content_generated']['images'] ); ?> images,
            <?php echo absint( $overview['content_generated']['audio'] ); ?> audio)
        </p>
    </div>

    <div class="smpf-card">
        <h2><?php esc_html_e( 'Recent Posts', 'smpf-analytics' ); ?></h2>
        <?php if ( ! empty( $log['entries'] ) ) : ?>
            <table class="wp-list-table widefat fixed striped">
                <thead>
                    <tr>
                        <th><?php esc_html_e( 'Time', 'smpf-analytics' ); ?></th>
                        <th><?php esc_html_e( 'Preview', 'smpf-analytics' ); ?></th>
                        <th><?php esc_html_e( 'Results', 'smpf-analytics' ); ?></th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ( array_reverse( $log['entries'] ) as $entry ) : ?>
                        <tr>
                            <td><?php echo esc_html( date_i18n( 'Y-m-d H:i', strtotime( $entry['time'] ) ) ); ?></td>
                            <td><?php echo esc_html( $entry['text_preview'] ); ?></td>
                            <td>
                                <?php foreach ( $entry['results'] as $r ) : ?>
                                    <span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:0.8em;margin:2px;
                                        <?php echo ( 'sent' === $r['status'] || 'posted' === $r['status'] ) ? 'background:#d4edda;color:#155724;' : 'background:#f8d7da;color:#721c24;'; ?>">
                                        <?php echo esc_html( $r['platform'] . ': ' . $r['status'] ); ?>
                                    </span>
                                <?php endforeach; ?>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        <?php else : ?>
            <p><?php esc_html_e( 'No posts yet.', 'smpf-analytics' ); ?></p>
        <?php endif; ?>
    </div>

    <div class="smpf-card">
        <h2><?php esc_html_e( 'Generated Content', 'smpf-analytics' ); ?></h2>
        <?php if ( ! empty( $content['images'] ) ) : ?>
            <h4><?php esc_html_e( 'Images', 'smpf-analytics' ); ?></h4>
            <div style="display:flex;flex-wrap:wrap;gap:12px;">
                <?php foreach ( $content['images'] as $img ) : ?>
                    <div style="text-align:center;">
                        <img src="<?php echo esc_url( $core->api->get_base_url() . '/generated/' . $img['name'] ); ?>"
                             style="width:100px;height:100px;object-fit:cover;border-radius:6px;"
                             alt="">
                        <div style="font-size:0.75em;color:#666;"><?php echo esc_html( size_format( $img['size'] ) ); ?></div>
                    </div>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>
    </div>

    <?php endif; ?>
</div>
