<?php
/**
 * SMPF Dashboard Template
 *
 * @package SMPF_Core
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

$is_online = false;
if ( ! is_wp_error( $overview ) && isset( $overview['platforms'] ) ) {
    $is_online = true;
}
?>
<div class="wrap smpf-wrap">
    <h1><?php esc_html_e( 'SMPF Dashboard', 'smpf-core' ); ?></h1>

    <?php if ( ! $is_online ) : ?>
    <div class="smpf-alert smpf-alert-warning">
        <strong><?php esc_html_e( 'Backend Offline', 'smpf-core' ); ?></strong><br>
        <?php esc_html_e( 'The SMPF FastAPI backend is not reachable. Check that it is running and the URL in Settings is correct.', 'smpf-core' ); ?>
    </div>
    <?php endif; ?>

    <div class="smpf-card">
        <h2><?php esc_html_e( 'Platform Connections', 'smpf-core' ); ?></h2>
        <p>
            <button id="smpf-refresh-status" class="smpf-btn"><?php esc_html_e( 'Refresh Status', 'smpf-core' ); ?></button>
        </p>
        <div class="smpf-status-grid">
            <?php if ( $is_online && ! empty( $status['platforms'] ) ) : ?>
                <?php foreach ( $status['platforms'] as $platform ) : ?>
                    <?php $connected = ( 'connected' === $platform['status'] ); ?>
                    <div class="smpf-status-item <?php echo $connected ? 'connected' : ''; ?>">
                        <span class="platform-name"><?php echo esc_html( $platform['name'] ); ?></span>
                        <span class="platform-status"><?php echo $connected ? esc_html__( 'Connected', 'smpf-core' ) : esc_html__( 'Not connected', 'smpf-core' ); ?></span>
                    </div>
                <?php endforeach; ?>
            <?php else : ?>
                <div class="smpf-status-item">
                    <span class="platform-name"><?php esc_html_e( 'No data available', 'smpf-core' ); ?></span>
                    <span class="platform-status"><?php esc_html_e( 'Offline', 'smpf-core' ); ?></span>
                </div>
            <?php endif; ?>
        </div>
    </div>

    <?php if ( $is_online && isset( $overview['content_generated'] ) ) : ?>
    <div class="smpf-card">
        <h2><?php esc_html_e( 'Content Overview', 'smpf-core' ); ?></h2>
        <p>
            <strong><?php esc_html_e( 'Images generated:', 'smpf-core' ); ?></strong> <?php echo absint( $overview['content_generated']['images'] ); ?><br>
            <strong><?php esc_html_e( 'Audio generated:', 'smpf-core' ); ?></strong> <?php echo absint( $overview['content_generated']['audio'] ); ?><br>
            <strong><?php esc_html_e( 'Total:', 'smpf-core' ); ?></strong> <?php echo absint( $overview['content_generated']['total'] ); ?><br>
            <strong><?php esc_html_e( 'Platforms connected:', 'smpf-core' ); ?></strong> <?php echo absint( $overview['platforms']['connected'] ); ?> / <?php echo absint( $overview['platforms']['total'] ); ?>
        </p>
    </div>
    <?php endif; ?>

    <div class="smpf-card">
        <h2><?php esc_html_e( 'Quick Actions', 'smpf-core' ); ?></h2>
        <p>
            <?php if ( class_exists( 'SMPF_Post' ) ) : ?>
                <a href="<?php echo esc_url( admin_url( 'admin.php?page=smpf-post-composer' ) ); ?>" class="smpf-btn smpf-btn-success"><?php esc_html_e( '➕ Create Post', 'smpf-core' ); ?></a>
            <?php endif; ?>
            <?php if ( class_exists( 'SMPF_Analytics' ) ) : ?>
                <a href="<?php echo esc_url( admin_url( 'admin.php?page=smpf-analytics' ) ); ?>" class="smpf-btn"><?php esc_html_e( '📊 Analytics', 'smpf-core' ); ?></a>
            <?php endif; ?>
            <a href="<?php echo esc_url( admin_url( 'admin.php?page=smpf-settings' ) ); ?>" class="smpf-btn"><?php esc_html_e( '⚙️ Settings', 'smpf-core' ); ?></a>
        </p>
    </div>
</div>
