#include <gtk/gtk.h>
#include <webkit/webkit.h>

static void activate(GtkApplication *application, gpointer user_data) {
    GtkWidget *window = gtk_application_window_new(application);
    gtk_window_set_title(GTK_WINDOW(window), "Kimi Console");
    gtk_window_set_default_size(GTK_WINDOW(window), 1280, 800);

    WebKitSettings *settings = webkit_settings_new();
    webkit_settings_set_allow_universal_access_from_file_urls(settings, TRUE);
    webkit_settings_set_allow_file_access_from_file_urls(settings, TRUE);

    GtkWidget *web_view = webkit_web_view_new();
    webkit_web_view_set_settings(WEBKIT_WEB_VIEW(web_view), settings);
    g_object_unref(settings);
    char *uri = g_filename_to_uri("/app/share/kimi-console/index.html", NULL, NULL);
    webkit_web_view_load_uri(WEBKIT_WEB_VIEW(web_view), uri);
    g_free(uri);

    gtk_window_set_child(GTK_WINDOW(window), web_view);
    gtk_window_present(GTK_WINDOW(window));
}

int main(int argc, char **argv) {
    GtkApplication *application = gtk_application_new(
        "com.kimi.Console", G_APPLICATION_DEFAULT_FLAGS);
    g_signal_connect(application, "activate", G_CALLBACK(activate), NULL);
    int status = g_application_run(G_APPLICATION(application), argc, argv);
    g_object_unref(application);
    return status;
}