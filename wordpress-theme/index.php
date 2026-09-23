<?php
/**
 * The main template file
 *
 * @package SMPF_Portal
 */

get_header();
?>

<div class="smpf-page-header">
    <h1><?php single_post_title(); ?></h1>
    <?php
    $description = get_bloginfo( 'description', 'display' );
    if ( $description || is_customize_preview() ) :
        ?>
        <p><?php echo esc_html( $description ); ?></p>
    <?php endif; ?>
</div>

<?php if ( have_posts() ) : ?>
    <?php while ( have_posts() ) : the_post(); ?>
        <article class="smpf-card">
            <?php if ( has_post_thumbnail() ) : ?>
                <a href="<?php the_permalink(); ?>">
                    <?php the_post_thumbnail( 'medium', array( 'style' => 'border-radius:4px;margin-bottom:12px;' ) ); ?>
                </a>
            <?php endif; ?>
            <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
            <?php the_excerpt(); ?>
            <a href="<?php the_permalink(); ?>" class="smpf-btn smpf-btn-ghost"><?php esc_html_e( 'Read More', 'smpf-portal' ); ?></a>
        </article>
    <?php endwhile; ?>

    <?php the_posts_pagination(); ?>

<?php else : ?>
    <div class="smpf-card">
        <p><?php esc_html_e( 'No content found.', 'smpf-portal' ); ?></p>
    </div>
<?php endif; ?>

<?php
get_footer();
