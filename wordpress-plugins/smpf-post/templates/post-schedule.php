<?php
/**
 * SMPF Post Schedule Template (placeholder for future scheduling UI)
 *
 * @package SMPF_Post
 */
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}
?>
<div class="wrap smpf-wrap">
    <h1><?php esc_html_e( 'Post Schedule', 'smpf-post' ); ?></h1>
    <div class="smpf-card">
        <h2><?php esc_html_e( 'Scheduled Posts', 'smpf-post' ); ?></h2>
        <div class="smpf-alert smpf-alert-warning">
            <?php esc_html_e( 'Scheduling is coming in a future update. For now, all posts are sent immediately.', 'smpf-post' ); ?>
        </div>
        <p><?php esc_html_e( 'Planned features:', 'smpf-post' ); ?></p>
        <ul>
            <li><?php esc_html_e( 'Calendar view of upcoming posts', 'smpf-post' ); ?></li>
            <li><?php esc_html_e( 'Recurring post series', 'smpf-post' ); ?></li>
            <li><?php esc_html_e( 'Best-time scheduling per platform', 'smpf-post' ); ?></li>
            <li><?php esc_html_e( 'Queue management and drag-and-drop reordering', 'smpf-post' ); ?></li>
        </ul>
    </div>
</div>
