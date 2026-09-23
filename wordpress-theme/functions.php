<?php
/**
 * SMPF Portal Theme Functions
 *
 * @package SMPF_Portal
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

/* ===== THEME SETUP ===== */
add_action( 'after_setup_theme', function() {
    // Theme supports
    add_theme_support( 'title-tag' );
    add_theme_support( 'post-thumbnails' );
    add_theme_support( 'html5', array( 'search-form', 'comment-form', 'comment-list', 'gallery', 'caption' ) );
    add_theme_support( 'responsive-embeds' );

    // Register navigation menus
    register_nav_menus( array(
        'primary' => __( 'Primary Menu', 'smpf-portal' ),
        'footer'  => __( 'Footer Menu', 'smpf-portal' ),
    ) );
});

/* ===== ENQUEUE ASSETS ===== */
add_action( 'wp_enqueue_scripts', function() {
    wp_enqueue_style(
        'smpf-portal-style',
        get_stylesheet_uri(),
        array(),
        wp_get_theme()->get( 'Version' )
    );
});

/* ===== CUSTOM LOGIN LOGO ===== */
add_action( 'login_enqueue_scripts', function() {
    ?>
    <style type="text/css">
        #login h1 a {
            background-image: none;
            text-indent: 0;
            width: auto;
            height: auto;
            font-size: 1.5rem;
            font-weight: 700;
            color: #1a1a2e;
            text-decoration: none;
        }
        body.login {
            background: #f6f7f7;
        }
        #login {
            padding: 5% 0 0;
        }
        #loginform {
            border: 1px solid #c3c4c7;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
    </style>
    <?php
});
add_filter( 'login_headerurl', function() { return home_url(); } );
add_filter( 'login_headertext', function() { return get_bloginfo( 'name' ); } );
