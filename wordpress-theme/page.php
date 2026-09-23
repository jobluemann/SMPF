<?php
/**
 * Template for displaying pages
 *
 * @package SMPF_Portal
 */

get_header();
?>

<?php while ( have_posts() ) : the_post(); ?>
    <div class="smpf-page-header">
        <h1><?php the_title(); ?></h1>
        <?php if ( has_excerpt() ) : ?>
            <p><?php echo esc_html( get_the_excerpt() ); ?></p>
        <?php endif; ?>
    </div>

    <article class="smpf-card">
        <?php the_content(); ?>
    </article>
<?php endwhile; ?>

<?php
get_footer();
