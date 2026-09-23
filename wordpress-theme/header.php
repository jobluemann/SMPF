<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo( 'charset' ); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<div class="smpf-site">

    <header class="smpf-header">
        <div class="smpf-container smpf-header-inner">
            <div class="smpf-logo">
                <a href="<?php echo esc_url( home_url( '/' ) ); ?>">
                    <?php bloginfo( 'name' ); ?>
                </a>
            </div>

            <?php if ( has_nav_menu( 'primary' ) ) : ?>
                <nav class="smpf-nav" aria-label="<?php esc_attr_e( 'Primary Menu', 'smpf-portal' ); ?>">
                    <?php
                    wp_nav_menu( array(
                        'theme_location' => 'primary',
                        'container'      => false,
                        'menu_class'     => '',
                        'depth'          => 1,
                        'fallback_cb'    => false,
                    ) );
                    ?>
                </nav>
            <?php endif; ?>

            <button class="smpf-nav-toggle" aria-label="<?php esc_attr_e( 'Toggle Menu', 'smpf-portal' ); ?>">&#9776;</button>
        </div>
    </header>

    <main class="smpf-main">
        <div class="smpf-container">
